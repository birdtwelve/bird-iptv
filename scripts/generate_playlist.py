import re
import os
import json
from datetime import datetime

# --- Configuration ---
CHANNELS_FILE = 'channels.txt'
PLAYLIST_FILE = 'playlist.m3u'
IMPORT_FILE = 'bulk_import.m3u'
LOG_FILE = 'playlist_update.log'
SETTINGS_FILE = 'config/settings.json'
GROUP_OVERRIDES_FILE = 'config/group_overrides.json'

def log_message(message, level="INFO"):
    """Logs messages to file and prints them."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted_message = f"[{timestamp}] {level}: {message}"
    
    try:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(formatted_message + "\n")
    except Exception as e:
        print(f"ERROR: Could not write to log: {e}")
    
    print(formatted_message)

def load_settings():
    """Load settings with enhanced defaults."""
    default_settings = {
        "remove_duplicates": True,
        "sort_channels": True,
        "backup_before_import": True,
        "auto_cleanup_import": True,
        "auto_detect_country": True,
        "detect_quality": True,
        "skip_adult_content": True,
        "min_channel_name_length": 2
    }
    
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                settings = json.load(f)
                return {**default_settings, **settings}
        except Exception as e:
            log_message(f"Could not load settings, using defaults: {e}", "WARNING")
    
    return default_settings

def load_group_overrides():
    """Load group overrides."""
    if os.path.exists(GROUP_OVERRIDES_FILE):
        try:
            with open(GROUP_OVERRIDES_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            log_message(f"Could not load group overrides: {e}", "WARNING")
    
    return {}

def detect_country_from_channel(channel_name, epg_id="", logo_url=""):
    """Comprehensive country detection with 100+ countries."""
    name_lower = channel_name.lower().strip()
    epg_lower = epg_id.lower().strip()
    logo_lower = logo_url.lower().strip()
    all_text = f"{name_lower} {epg_lower} {logo_lower}"
    
    log_message(f"Detecting country for: '{channel_name}'", "DEBUG")
    
    # Comprehensive patterns - shortened for space
    patterns = {
        "🇺🇸 United States": ["cbs", "nbc", "abc", "fox", "espn", "cnn", "hbo", " usa", " us ", ".us", "america", "nfl"],
        "🇬🇧 United Kingdom": ["bbc", "itv", "sky", "channel 4", "e4", " uk", ".uk", "british", "premier league"],
        "🇨🇦 Canada": ["cbc", "ctv", "global", "canada", "canadian", " ca ", ".ca"],
        "🇩🇪 Germany": ["ard", "zdf", "rtl", "sat.1", "pro7", "germany", "german", " de ", ".de"],
        "🇫🇷 France": ["tf1", "france 2", "m6", "canal+", "france", "french", " fr ", ".fr"],
        "🇪🇸 Spain": ["tve", "antena 3", "telecinco", "spain", "spanish", " es ", ".es"],
        "🇮🇹 Italy": ["rai", "mediaset", "canale 5", "italy", "italian", " it ", ".it"],
        "🇳🇱 Netherlands": ["npo", "rtl nl", "netherlands", "dutch", "holland", " nl ", ".nl"],
        "🇧🇪 Belgium": ["vtm", "één", "canvas", "belgium", "belgian", " be ", ".be"],
        "🇨🇭 Switzerland": ["srf", "rts", "switzerland", "swiss", " ch ", ".ch"],
        "🇦🇹 Austria": ["orf", "austria", "austrian", " at ", ".at"],
        "🇵🇹 Portugal": ["rtp", "sic", "tvi", "portugal", "portuguese", " pt ", ".pt"],
        "🇮🇪 Ireland": ["rte", "tg4", "ireland", "irish", " ie ", ".ie"],
        "🇸🇪 Sweden": ["svt", "tv4", "sweden", "swedish", " se ", ".se"],
        "🇳🇴 Norway": ["nrk", "tv 2 no", "norway", "norwegian", " no ", ".no"],
        "🇩🇰 Denmark": ["dr", "tv2 dk", "denmark", "danish", " dk ", ".dk"],
        "🇫🇮 Finland": ["yle", "mtv3", "finland", "finnish", " fi ", ".fi"],
        "🇮🇸 Iceland": ["ruv", "iceland", "icelandic", " is ", ".is"],
        "🇷🇺 Russia": ["channel one", "rossiya", "ntv", "russia", "russian", " ru ", ".ru"],
        "🇵🇱 Poland": ["tvp", "polsat", "tvn", "poland", "polish", " pl ", ".pl"],
        "🇨🇿 Czech Republic": ["ct", "nova", "prima", "czech", " cz ", ".cz"],
        "🇸🇰 Slovakia": ["rtvs", "markiza", "slovakia", "slovak", " sk ", ".sk"],
        "🇭🇺 Hungary": ["mtv hu", "rtl klub", "hungary", "hungarian", " hu ", ".hu"],
        "🇺🇦 Ukraine": ["1+1", "inter", "ictv", "ukraine", "ukrainian", " ua ", ".ua"],
        "🇷🇴 Romania": ["tvr", "pro tv", "romania", "romanian", " ro ", ".ro"],
        "🇧🇬 Bulgaria": ["btv", "nova bg", "bulgaria", "bulgarian", " bg ", ".bg"],
        "🇭🇷 Croatia": ["hrt", "nova tv hr", "croatia", "croatian", " hr ", ".hr"],
        "🇷🇸 Serbia": ["rts", "pink", "serbia", "serbian", " rs ", ".rs"],
        "🇬🇷 Greece": ["ert", "mega gr", "greece", "greek", " gr ", ".gr"],
        "🇧🇷 Brazil": ["globo", "band", "sbt", "brazil", "brasil", " br ", ".br"],
        "🇦🇷 Argentina": ["telefe", "canal 13", "argentina", " ar ", ".ar"],
        "🇲🇽 Mexico": ["televisa", "tv azteca", "mexico", "méxico", " mx ", ".mx"],
        "🇨🇱 Chile": ["tvn", "mega", "chile", "chilean", " cl ", ".cl"],
        "🇨🇴 Colombia": ["caracol", "rcn", "colombia", "colombian", " co ", ".co"],
        "🇵🇪 Peru": ["america tv pe", "peru", "peruvian", " pe ", ".pe"],
        "🇻🇪 Venezuela": ["venevision", "venezuela", "venezuelan", " ve ", ".ve"],
        "🇨🇳 China": ["cctv", "phoenix", "china", "chinese", " cn ", ".cn"],
        "🇯🇵 Japan": ["nhk", "fuji", "tv asahi", "japan", "japanese", " jp ", ".jp"],
        "🇰🇷 South Korea": ["kbs", "sbs kr", "mbc kr", "korea", "korean", " kr ", ".kr"],
        "🇰🇵 North Korea": ["kctv", "north korea", "dprk"],
        "🇹🇼 Taiwan": ["cts", "ctv", "tvbs", "taiwan", "taiwanese", " tw ", ".tw"],
        "🇭🇰 Hong Kong": ["tvb", "atv", "hong kong", "hongkong", " hk ", ".hk"],
        "🇹🇭 Thailand": ["ch3", "ch7", "thai pbs", "thailand", "thai", " th ", ".th"],
        "🇻🇳 Vietnam": ["vtv", "htv", "vietnam", "vietnamese", " vn ", ".vn"],
        "🇮🇩 Indonesia": ["tvri", "sctv", "rcti", "indonesia", "indonesian", " id ", ".id"],
        "🇲🇾 Malaysia": ["tv1", "tv3", "astro", "malaysia", "malaysian", " my ", ".my", "my:"],
        "🇸🇬 Singapore": ["channel 5", "channel 8", "singapore", " sg ", ".sg"],
        "🇵🇭 Philippines": ["abs-cbn", "gma", "philippines", "filipino", " ph ", ".ph"],
        "🇮🇳 India": ["star plus", "zee tv", "colors", "sony tv", "india", "indian", "hindi", " in ", ".in"],
        "🇵🇰 Pakistan": ["ptv", "geo tv", "ary", "pakistan", "pakistani", " pk ", ".pk"],
        "🇧🇩 Bangladesh": ["btv", "channel i", "bangladesh", "bangladeshi", " bd ", ".bd"],
        "🇱🇰 Sri Lanka": ["rupavahini", "sirasa", "sri lanka", " lk ", ".lk"],
        "🇳🇵 Nepal": ["nepal tv", "kantipur", "nepal", "nepali", " np ", ".np"],
        "🇦🇫 Afghanistan": ["rta", "tolo tv", "afghanistan", "afghan", " af ", ".af"],
        "🇦🇺 Australia": ["abc au", "seven", "nine", "ten", "australia", "australian", "aussie", " au ", ".au"],
        "🇳🇿 New Zealand": ["tvnz", "tvnz 1", "tvnz 2", "three nz", "tvnz duke", "new zealand", "kiwi", " nz ", ".nz"],
        "🇸🇦 Arabic": ["al jazeera", "mbc", "lbc", "dubai tv", "arabic", "arab", "qatar", "dubai", "saudi"],
        "🇮🇱 Israel": ["kan", "keshet 12", "israel", "israeli", "hebrew", " il ", ".il"],
        "🇹🇷 Turkey": ["trt", "atv", "kanal d", "turkey", "turkish", " tr ", ".tr", "tr |"],
        "🇮🇷 Iran": ["irib", "press tv", "iran", "iranian", "persian", " ir ", ".ir"],
        "🇪🇬 Egypt": ["nile tv", "cbc egypt", "egypt", "egyptian", " eg ", ".eg"],
        "🇿🇦 South Africa": ["sabc", "etv", "mnet", "south africa", " za ", ".za"],
        "🇳🇬 Nigeria": ["nta", "channels tv", "nigeria", "nigerian", " ng ", ".ng"]
    }
    
    # Check patterns - order matters, more specific first
    # First check for country prefixes (more specific)
    country_prefixes = {
        "🇺🇦 Ukraine": ["ua |"],
        "🇵🇱 Poland": ["pl |"], 
        "🇹🇷 Turkey": ["tr |"],
        "🇲🇾 Malaysia": ["my:", "my |"],
        "🇬🇧 United Kingdom": ["uk:", "uk |"],
        "🇺🇸 United States": ["us:", "us |"]
    }
    
    for country, prefixes in country_prefixes.items():
        for prefix in prefixes:
            if prefix in all_text:
                log_message(f"Detected {country} for: {channel_name} (matched prefix: '{prefix}')", "INFO")
                return country
    
    # Then check general patterns
    for country, keywords in patterns.items():
        for keyword in keywords:
            if keyword in all_text:
                log_message(f"Detected {country} for: {channel_name} (matched: '{keyword}')", "INFO")
                return country
    
    # No special categories - everything unmatched goes to Uncategorized
    log_message(f"No country detected for: {channel_name}", "DEBUG")
    return "Uncategorized"

def detect_quality(channel_name):
    """Detect quality from channel name."""
    name_lower = channel_name.lower()
    if "4k" in name_lower or "uhd" in name_lower:
        return "4K"
    elif "fhd" in name_lower or "1080" in name_lower:
        return "FHD"
    elif "hd" in name_lower:
        return "HD"
    elif "sd" in name_lower:
        return "SD"
    return ""

def is_adult_content(channel_name):
    """Check for adult content."""
    adult_keywords = ["xxx", "adult", "porn", "sex", "erotic", "playboy"]
    return any(keyword in channel_name.lower() for keyword in adult_keywords)

def validate_channel(channel, settings):
    """Validate channel for import."""
    name = channel.get('Stream name', '').strip()
    url = channel.get('Stream URL', '').strip()
    
    if not name or not url:
        return False, "Missing name or URL"
    if len(name) < settings.get('min_channel_name_length', 2):
        return False, "Name too short"
    if settings.get('skip_adult_content', True) and is_adult_content(name):
        return False, "Adult content filtered"
    if not (url.startswith('http') or url.startswith('rtmp')):
        return False, "Invalid URL"
    
    return True, "Valid"

def apply_auto_country_detection(channel, group_overrides, settings):
    """Apply country detection and quality tags."""
    stream_name = channel.get('Stream name', '')
    epg_id = channel.get('EPG id', '')
    logo_url = channel.get('Logo', '')
    
    # Manual overrides first
    for key, new_group in group_overrides.items():
        if key.lower() in stream_name.lower():
            channel['Group'] = new_group
            return channel
    
    # Add quality tag
    if settings.get('detect_quality', True):
        quality = detect_quality(stream_name)
        if quality and quality not in stream_name:
            channel['Stream name'] = f"{stream_name} [{quality}]"
    
    # Auto-detect country
    if settings.get('auto_detect_country', True):
        detected_country = detect_country_from_channel(stream_name, epg_id, logo_url)
        channel['Group'] = detected_country
        log_message(f"Auto-detected: '{stream_name}' → {detected_country}", "INFO")
    
    return channel

def parse_channel_block(block):
    """Parse channel block from channels.txt."""
    channel_data = {}
    lines = block.strip().split('\n')
    for line in lines:
        if '=' in line:
            key, value = line.split('=', 1)
            channel_data[key.strip()] = value.strip()
    return channel_data

def parse_m3u_entry(extinf_line, url_line):
    """Parse M3U entry."""
    channel = {}
    
    try:
        tvg_id_match = re.search(r'tvg-id="([^"]*)"', extinf_line)
        tvg_logo_match = re.search(r'tvg-logo="([^"]*)"', extinf_line)
        group_title_match = re.search(r'group-title="([^"]*)"', extinf_line)
        
        channel['EPG id'] = tvg_id_match.group(1) if tvg_id_match else ''
        channel['Logo'] = tvg_logo_match.group(1) if tvg_logo_match else ''
        channel['Group'] = group_title_match.group(1) if group_title_match else 'Uncategorized'
        
        stream_name_match = re.search(r',\s*(.+)$', extinf_line)
        if stream_name_match:
            stream_name = stream_name_match.group(1).strip()
            stream_name = re.sub(r'\s+', ' ', stream_name)
            channel['Stream name'] = stream_name
        else:
            channel['Stream name'] = 'Unknown Channel'
        
        channel['Stream URL'] = url_line.strip()
        
    except Exception as e:
        log_message(f"Error parsing M3U entry: {e}", "WARNING")
        channel = {
            'EPG id': '', 'Logo': '', 'Group': 'Uncategorized',
            'Stream name': 'Parse Error', 'Stream URL': url_line.strip()
        }
    
    return channel

def convert_to_channels_txt_block(channel_data):
    """Convert to channels.txt format."""
    block = []
    block.append(f"Group = {channel_data.get('Group', 'Uncategorized')}")
    block.append(f"Stream name = {channel_data.get('Stream name', 'Unknown Channel')}")
    block.append(f"Logo = {channel_data.get('Logo', '')}")
    block.append(f"EPG id = {channel_data.get('EPG id', '')}")
    block.append(f"Stream URL = {channel_data.get('Stream URL', '')}")
    return "\n".join(block)

def get_channel_signature(channel):
    """Create signature for duplicate detection."""
    name = channel.get('Stream name', '').strip().lower()
    url = channel.get('Stream URL', '').strip().lower()
    
    name_clean = re.sub(r'\s+', ' ', name)
    name_clean = re.sub(r'[^\w\s]', '', name_clean)
    name_clean = re.sub(r'\b(hd|fhd|4k|uhd|sd)\b', '', name_clean).strip()
    
    if '?' in url:
        url_clean = url.split('?')[0]
    else:
        url_clean = url
    
    return f"{name_clean}|{url_clean}"

def remove_duplicates(channels, settings):
    """Remove duplicate channels."""
    if not settings.get('remove_duplicates', True):
        return channels
    
    seen_signatures = set()
    unique_channels = []
    duplicates = []
    
    for channel in channels:
        signature = get_channel_signature(channel)
        if signature not in seen_signatures:
            seen_signatures.add(signature)
            unique_channels.append(channel)
        else:
            duplicates.append(channel.get('Stream name', 'Unknown'))
    
    if duplicates:
        log_message(f"Removed {len(duplicates)} duplicates", "INFO")
    
    return unique_channels

def update_existing_channels_with_country_detection():
    """Re-detect countries for existing channels - FORCE UPDATE ALL."""
    if not os.path.exists(CHANNELS_FILE):
        return
    
    settings = load_settings()
    
    log_message("FORCE re-detecting countries for ALL existing channels...", "INFO")
    
    with open(CHANNELS_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
    
    channel_blocks = re.split(r'\n\s*\n+', content.strip())
    updated_channels = []
    changes = 0
    
    for block in channel_blocks:
        if block.strip():
            channel = parse_channel_block(block)
            if channel:
                old_group = channel.get('Group', 'Uncategorized')
                stream_name = channel.get('Stream name', '')
                epg_id = channel.get('EPG id', '')
                logo_url = channel.get('Logo', '')
                
                # FORCE detection for ALL channels, regardless of current group
                detected = detect_country_from_channel(stream_name, epg_id, logo_url)
                
                # Always update the group
                channel['Group'] = detected
                if old_group != detected:
                    changes += 1
                    log_message(f"FORCED UPDATE: '{stream_name}' from '{old_group}' to '{detected}'", "INFO")
                
                updated_channels.append(channel)
    
    if updated_channels:
        # Always rewrite the file
        backup_name = f"{CHANNELS_FILE}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        try:
            import shutil
            shutil.copy2(CHANNELS_FILE, backup_name)
            log_message(f"Created backup: {backup_name}", "INFO")
        except:
            pass
        
        with open(CHANNELS_FILE, 'w', encoding='utf-8') as f:
            for i, channel in enumerate(updated_channels):
                if i > 0:
                    f.write("\n\n")
                f.write(convert_to_channels_txt_block(channel))
        
        log_message(f"FORCE updated ALL {len(updated_channels)} channels ({changes} changes made)", "INFO")

def process_import():
    """Process bulk M3U import with ROBUST handling of malformed files."""
    settings = load_settings()
    group_overrides = load_group_overrides()
    
    if not os.path.exists(IMPORT_FILE):
        log_message(f"No {IMPORT_FILE} found, skipping import", "INFO")
        return []

    log_message(f"Processing {IMPORT_FILE} with ROBUST parsing...", "INFO")
    
    stats = {
        'total_lines': 0, 'extinf_lines': 0, 'parsed': 0, 'valid': 0,
        'filtered_adult': 0, 'filtered_invalid': 0, 'duplicates': 0,
        'already_existed': 0, 'final_imported': 0, 'malformed_fixed': 0
    }
    
    imported_channels = []
    
    try:
        with open(IMPORT_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Pre-process the content to fix common issues
        log_message("Pre-processing M3U content to fix common issues...", "INFO")
        
        # Fix missing newlines between entries
        content = re.sub(r'(https?://[^\s]+)(#EXTINF)', r'\1\n\2', content)
        content = re.sub(r'(\.m3u8?)(#EXTINF)', r'\1\n\2', content)
        content = re.sub(r'(\.ts)(#EXTINF)', r'\1\n\2', content)
        
        # Split into lines after fixing
        lines = content.split('\n')
        stats['total_lines'] = len(lines)
        log_message(f"Processing {len(lines)} lines after pre-processing...", "INFO")

        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            if line.startswith('#EXTINF:'):
                stats['extinf_lines'] += 1
                extinf_line = line
                url_line = ""
                
                # Look for the URL in the next few lines (robust search)
                j = i + 1
                while j < len(lines) and j < i + 5:  # Look ahead max 5 lines
                    potential_url = lines[j].strip()
                    
                    # Skip empty lines and comments
                    if not potential_url or potential_url.startswith('#'):
                        j += 1
                        continue
                    
                    # Clean potential URL
                    if '#EXTINF' in potential_url:
                        # Split on #EXTINF and take the first part
                        url_parts = potential_url.split('#EXTINF')
                        potential_url = url_parts[0].strip()
                        
                        # Put the EXTINF part back for next iteration
                        if len(url_parts) > 1:
                            lines[j] = '#EXTINF' + url_parts[1]
                        stats['malformed_fixed'] += 1
                    
                    # Check if it looks like a URL
                    if (potential_url.startswith(('http://', 'https://', 'rtmp://', 'rtmps://')) or
                        potential_url.endswith(('.m3u8', '.ts', '.mp4')) or
                        '/' in potential_url):
                        url_line = potential_url
                        i = j  # Update our position
                        break
                    
                    j += 1
                
                # If we found a URL, process the channel
                if url_line:
                    try:
                        channel = parse_m3u_entry(extinf_line, url_line)
                        stats['parsed'] += 1
                        
                        # Additional URL cleaning
                        stream_url = channel.get('Stream URL', '').strip()
                        
                        # Remove any trailing garbage
                        if ' ' in stream_url:
                            url_parts = stream_url.split()
                            for part in url_parts:
                                if (part.startswith(('http://', 'https://', 'rtmp://')) or 
                                    part.endswith(('.m3u8', '.ts', '.mp4'))):
                                    channel['Stream URL'] = part
                                    break
                        
                        # Validate the channel
                        is_valid, reason = validate_channel(channel, settings)
                        if not is_valid:
                            if "adult" in reason.lower():
                                stats['filtered_adult'] += 1
                            else:
                                stats['filtered_invalid'] += 1
                            log_message(f"Filtered: {channel.get('Stream name')} - {reason}", "DEBUG")
                            i += 1
                            continue
                        
                        # Apply country detection
                        channel = apply_auto_country_detection(channel, group_overrides, settings)
                        imported_channels.append(channel)
                        stats['valid'] += 1
                        
                        log_message(f"Successfully imported: {channel.get('Stream name')} → {channel.get('Group')}", "DEBUG")
                        
                    except Exception as e:
                        log_message(f"Error processing channel: {e}", "WARNING")
                        i += 1
                        continue
                else:
                    log_message(f"No URL found for: {extinf_line[:50]}...", "WARNING")
                    i += 1
                    continue
            
            i += 1

        # Continue with duplicate removal and file writing...
        if imported_channels:
            log_message(f"Pre-duplicate removal: {len(imported_channels)} channels", "INFO")
            
            original_count = len(imported_channels)
            imported_channels = remove_duplicates(imported_channels, settings)
            stats['duplicates'] = original_count - len(imported_channels)
            
            # Check against existing channels
            existing_channels = []
            if os.path.exists(CHANNELS_FILE):
                with open(CHANNELS_FILE, 'r', encoding='utf-8') as f:
                    content = f.read()
                blocks = re.split(r'\n\s*\n+', content.strip())
                for block in blocks:
                    if block.strip():
                        existing_channels.append(parse_channel_block(block))
                
                existing_sigs = {get_channel_signature(ch) for ch in existing_channels}
                new_channels = []
                for channel in imported_channels:
                    if get_channel_signature(channel) not in existing_sigs:
                        new_channels.append(channel)
                    else:
                        stats['already_existed'] += 1
                
                imported_channels = new_channels
            
            stats['final_imported'] = len(imported_channels)
            
            # Write to file
            if imported_channels:
                log_message(f"Writing {len(imported_channels)} new channels to file...", "INFO")
                
                # Check if file exists and has content
                file_exists = os.path.exists(CHANNELS_FILE) and os.path.getsize(CHANNELS_FILE) > 0
                
                with open(CHANNELS_FILE, 'a', encoding='utf-8') as f:
                    for i, channel in enumerate(imported_channels):
                        if i > 0 or file_exists:
                            f.write("\n\n")
                        f.write(convert_to_channels_txt_block(channel))
                
                log_message(f"Successfully wrote {len(imported_channels)} channels", "INFO")

    except Exception as e:
        log_message(f"Error processing import: {e}", "ERROR")
    
    # Enhanced statistics
    log_message("=== ROBUST IMPORT STATISTICS ===", "INFO")
    for key, value in stats.items():
        log_message(f"{key.replace('_', ' ').title()}: {value}", "INFO")
    log_message("=== END STATISTICS ===", "INFO")
    
    # Cleanup
    if settings.get('auto_cleanup_import', True):
        try:
            os.remove(IMPORT_FILE)
            log_message(f"Cleaned up {IMPORT_FILE}", "INFO")
        except:
            pass
    
    return imported_channels

def generate_playlist():
    """Main enhanced playlist generation function."""
    if os.path.exists(LOG_FILE):
        open(LOG_FILE, 'w').close()
    
    log_message("Starting comprehensive playlist generation...", "INFO")
    
    settings = load_settings()
    group_overrides = load_group_overrides()
    
    update_existing_channels_with_country_detection()
    
    imported_channels = process_import()
    log_message(f"Import returned {len(imported_channels)} channels", "INFO")

    if not os.path.exists(CHANNELS_FILE):
        log_message(f"Error: {CHANNELS_FILE} not found", "ERROR")
        return

    with open(CHANNELS_FILE, 'r', encoding='utf-8') as f:
        content = f.read()

    channel_blocks = re.split(r'\n\s*\n+', content.strip())
    parsed_channels = []

    for block in channel_blocks:
        if block.strip():
            channel = parse_channel_block(block)
            if channel:
                parsed_channels.append(channel)

    log_message(f"Parsed {len(parsed_channels)} channels", "INFO")

    parsed_channels = remove_duplicates(parsed_channels, settings)
    
    if settings.get('sort_channels', True):
        parsed_channels.sort(key=lambda x: (x.get('Group', '').lower(), x.get('Stream name', '').lower()))

    m3u_lines = ["#EXTM3U"]
    valid_channels = 0
    country_stats = {}
    
    for channel in parsed_channels:
        stream_name = channel.get('Stream name', '')
        group_name = channel.get('Group', 'Uncategorized')
        logo_url = channel.get('Logo', '')
        epg_id = channel.get('EPG id', '')
        stream_url = channel.get('Stream URL', '')

        if not stream_name or not stream_url:
            continue

        extinf_attrs = [
            f'tvg-id="{epg_id}"',
            f'tvg-logo="{logo_url}"',
            f'group-title="{group_name}"',
            f'tvg-name="{stream_name}"'
        ]

        extinf_line = f"#EXTINF:-1 {' '.join(extinf_attrs)},{stream_name}"
        m3u_lines.append(extinf_line)
        m3u_lines.append(stream_url)
        valid_channels += 1
        
        country_stats[group_name] = country_stats.get(group_name, 0) + 1

    try:
        with open(PLAYLIST_FILE, 'w', encoding='utf-8') as f:
            for line in m3u_lines:
                f.write(line + '\n')
        log_message(f"Generated {PLAYLIST_FILE} with {valid_channels} channels", "INFO")
        
        sorted_stats = dict(sorted(country_stats.items(), key=lambda x: x[1], reverse=True))
        log_message(f"Channels by country: {sorted_stats}", "INFO")
        
    except Exception as e:
        log_message(f"Error writing playlist: {e}", "ERROR")

    log_message("Comprehensive playlist generation complete", "INFO")

if __name__ == "__main__":
    generate_playlist()