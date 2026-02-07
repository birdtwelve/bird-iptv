#!/usr/bin/env python3
import asyncio
import gzip
import re
from pathlib import Path
from xml.etree import ElementTree as ET

import httpx

epg_file = Path(__file__).parent / "TV.xml"

epg_urls = [
    "https://epgshare01.online/epgshare01/epg_ripper_ALL_SOURCES1.xml.gz" 
    "https://i.mjh.nz/Plex/all.xml.gz",
    "https://i.mjh.nz/PlutoTV/all.xml.gz",
    "https://i.mjh.nz/Roku/all.xml.gz",
    "https://raw.githubusercontent.com/BuddyChewChew/tubi-scraper/refs/heads/main/tubi_epg.xml",
    "https://raw.githubusercontent.com/BuddyChewChew/xumo-playlist-generator/main/playlists/xumo_epg.xml.gz",
]

client = httpx.AsyncClient(
    timeout=5,
    follow_redirects=True,
    http2=True,
    headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36 Edg/134.0.0.0"
    },
)

live_img = "https://i.gyazo.com/978f2eb4a199ca5b56b447aded0cb9e3.png"

dummies = {
    "Basketball.Dummy.us": live_img,
    "Golf.Dummy.us": live_img,
    "Live.Event.us": live_img,
    "MLB.Baseball.Dummy.us": None,
    "NBA.Basketball.Dummy.us": None,
    "NFL.Dummy.us": None,
    "NHL.Hockey.Dummy.us": None,
    "PPV.EVENTS.Dummy.us": live_img,
    "Racing.Dummy.us": live_img,
    "Soccer.Dummy.us": live_img,
    "Tennis.Dummy.us": live_img,
    "WNBA.dummy.us": None,
}

replace_ids = {
    "NCAA Sports": {"old": "Sports.Dummy.us", "new": "NCAA.Sports.Dummy.us"},
    "UFC": {"old": "UFC.247.Dummy.us", "new": "UFC.Dummy.us"},
}


def get_tvg_ids() -> dict[str, str]:
    base_m3u8 = (
        (Path(__file__).parent.parent / "M3U8" / "base.m3u8")
        .read_text(encoding="utf-8")
        .splitlines()
    )

    tvg = {}

    for line in base_m3u8:
        if line.startswith("#EXTINF"):
            tvg_id = re.search(r'tvg-id="([^"]*)"', line)[1]
            tvg_logo = re.search(r'tvg-logo="([^"]*)"', line)[1]

            tvg[tvg_id] = tvg_logo

    return tvg


async def fetch_xml(url: str) -> ET.Element | None:
    try:
        r = await client.get(url)
        r.raise_for_status()
    except Exception as e:
        print(f'Failed to fetch "{url}": {e}')
        return

    try:
        decompressed_data = gzip.decompress(r.content)

        return ET.fromstring(decompressed_data)

    except Exception as e:
        print(f'Failed to decompress and parse XML from "{url}": {e}')


def hijack_id(
    old: str,
    new: str,
    text: str,
    root: ET.Element,
) -> None:

    og_channel = root.find(f"./channel[@id='{old}']")

    if og_channel is not None:
        new_channel = ET.Element(og_channel.tag, {**og_channel.attrib, "id": new})

        display_name = og_channel.find("display-name")

        if display_name is not None:
            new_channel.append(ET.Element("display-name", display_name.attrib))
            new_channel[-1].text = text

        for child in og_channel:
            if child.tag == "display-name":
                continue

            new_child = ET.Element(child.tag, child.attrib)
            new_child.text = child.text

        root.remove(og_channel)

        root.append(new_channel)

    for program in root.findall(f"./programme[@channel='{old}']"):
        new_program = ET.Element(program.tag, {**program.attrib, "channel": new})

        for child in program:
            new_child = ET.Element(child.tag, child.attrib)
            new_child.text = child.text
            new_program.append(new_child)

        for tag_name in ["title", "desc", "sub-title"]:
            tag = new_program.find(tag_name)

            if tag is not None:
                tag.text = text

        root.remove(program)

        root.append(new_program)


async def main() -> None:
    tvg_ids = get_tvg_ids()

    tvg_ids |= dummies | {v["old"]: live_img for v in replace_ids.values()}

    root = ET.Element("tv")

    tasks = [fetch_xml(url) for url in epg_urls]

    results = await asyncio.gather(*tasks)

    for epg_data in results:
        if epg_data is None:
            continue

        for channel in epg_data.findall("channel"):
            if (channel_id := channel.get("id")) in tvg_ids:
                for icon_tag in channel.findall("icon"):
                    if logo := tvg_ids.get(channel_id):
                        icon_tag.set("src", logo)

                if (url_tag := channel.find("url")) is not None:
                    channel.remove(url_tag)

                root.append(channel)

        for program in epg_data.findall("programme"):
            if program.get("channel") in tvg_ids:
                title_text = program.find("title").text
                subtitle = program.find("sub-title")

                if (
                    title_text in ["NHL Hockey", "Live: NFL Football"]
                    and subtitle is not None
                ):
                    program.find("title").text = f"{title_text} {subtitle.text}"

                root.append(program)

        for k, v in replace_ids.items():
            hijack_id(**v, text=k, root=root)

    tree = ET.ElementTree(root)

    tree.write(epg_file, encoding="utf-8", xml_declaration=True)

    print(f"EPG saved to {epg_file.resolve()}")


if __name__ == "__main__":
    asyncio.run(main())

    try:
        asyncio.run(client.aclose())
    except Exception:
        pass
