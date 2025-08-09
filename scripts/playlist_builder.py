"""
Playlist Builder - Generates the final M3U playlist
"""

import logging
from typing import Dict, List, Tuple

class PlaylistBuilder:
    """Generate M3U playlist files."""
    
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    def generate_m3u(self, channels: List[Dict]) -> Tuple[int, Dict]:
        """Generate the M3U playlist file and return stats."""
        m3u_lines = ["#EXTM3U"]
        valid_channels = 0
        country_stats = {}
        
        for channel in channels:
            stream_name = channel.get('Stream name', '')
            group_name = channel.get('Group', 'Uncategorized')
            logo_url = channel.get('Logo', '')
            epg_id = channel.get('EPG id', '')
            stream_url = channel.get('Stream URL', '')
            
            if not stream_name or not stream_url:
                continue
            
            # Build EXTINF line with all attributes
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
            
            # Update country statistics
            country_stats[group_name] = country_stats.get(group_name, 0) + 1
        
        try:
            with open(self.config.playlist_file, 'w', encoding='utf-8') as f:
                for line in m3u_lines:
                    f.write(line + '\n')
            
            self.logger.info(f"Generated {self.config.playlist_file} with {valid_channels} channels")
            
            # Log top countries
            sorted_stats = dict(sorted(country_stats.items(), key=lambda x: x[1], reverse=True))
            top_countries = dict(list(sorted_stats.items())[:5])
            self.logger.info(f"Top countries: {top_countries}")
            
            return valid_channels, country_stats
            
        except Exception as e:
            self.logger.error(f"Error writing playlist: {e}")
            return 0, {}
    
    def validate_m3u_structure(self) -> bool:
        """Validate the generated M3U file structure."""
        try:
            with open(self.config.playlist_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            lines = content.strip().split('\n')
            
            if not lines or lines[0] != '#EXTM3U':
                self.logger.error("M3U file missing #EXTM3U header")
                return False
            
            extinf_count = sum(1 for line in lines if line.startswith('#EXTINF:'))
            url_count = sum(1 for line in lines if line.startswith(('http://', 'https://', 'rtmp://')))
            
            if extinf_count != url_count:
                self.logger.warning(f"M3U structure mismatch: {extinf_count} EXTINF lines vs {url_count} URLs")
            
            self.logger.info(f"M3U validation complete: {extinf_count} channels validated")
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating M3U: {e}")
            return False