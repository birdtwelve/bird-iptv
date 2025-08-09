"""
File Manager - Handles file operations, backups, and channel loading
"""

import os
import re
import shutil
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

class FileManager:
    """Manage file operations with backup and rotation."""
    
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.backup_dir = Path("backups")
        self.backup_dir.mkdir(exist_ok=True)
    
    def create_backup(self, file_path: str) -> Optional[Path]:
        """Create timestamped backup with rotation."""
        if not self.config.settings.get('create_backup', True):
            return None
        
        file_path = Path(file_path)
        if not file_path.exists():
            return None
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = self.backup_dir / f"{file_path.stem}_{timestamp}{file_path.suffix}"
        
        try:
            shutil.copy2(file_path, backup_path)
            self.logger.info(f"Created backup: {backup_path}")
            self._cleanup_old_backups(file_path.stem)
            return backup_path
        except Exception as e:
            self.logger.error(f"Failed to create backup: {e}")
            return None
    
    def _cleanup_old_backups(self, base_name: str):
        """Remove old backups, keeping only the most recent ones."""
        max_backups = self.config.settings.get('max_backups', 5)
        
        backup_files = sorted(
            [f for f in self.backup_dir.glob(f"{base_name}_*") if f.is_file()],
            key=lambda x: x.stat().st_mtime,
            reverse=True
        )
        
        for old_backup in backup_files[max_backups:]:
            try:
                old_backup.unlink()
                self.logger.debug(f"Removed old backup: {old_backup}")
            except Exception as e:
                self.logger.warning(f"Could not remove old backup {old_backup}: {e}")
    
    def load_all_channels(self) -> List[Dict]:
        """Load all channels from the channels file."""
        if not os.path.exists(self.config.channels_file):
            self.logger.info("No channels.txt file found")
            return []
        
        try:
            with open(self.config.channels_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            channel_blocks = re.split(r'\n\s*\n+', content.strip())
            channels = []
            
            for block in channel_blocks:
                if block.strip():
                    channel = self._parse_channel_block(block)
                    if channel:
                        channels.append(channel)
            
            self.logger.info(f"Loaded {len(channels)} channels from file")
            return channels
            
        except Exception as e:
            self.logger.error(f"Error loading channels: {e}")
            return []
    
    def _parse_channel_block(self, block: str) -> Optional[Dict]:
        """Parse a channel block from channels.txt."""
        channel_data = {}
        lines = block.strip().split('\n')
        
        for line in lines:
            if '=' in line:
                key, value = line.split('=', 1)
                channel_data[key.strip()] = value.strip()
        
        return channel_data if channel_data else None
    
    def save_channels(self, channels: List[Dict]) -> bool:
        """Save channels to the channels.txt file."""
        try:
            # Create backup first
            self.create_backup(self.config.channels_file)
            
            with open(self.config.channels_file, 'w', encoding='utf-8') as f:
                for i, channel in enumerate(channels):
                    if i > 0:
                        f.write("\n\n")
                    f.write(self._convert_to_channels_txt_block(channel))
            
            self.logger.info(f"Saved {len(channels)} channels to file")
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving channels: {e}")
            return False
    
    def append_channels(self, new_channels: List[Dict]) -> bool:
        """Append new channels to existing channels file."""
        try:
            # Load existing channels
            existing_channels = self.load_all_channels()
            
            # Combine with new channels
            all_channels = existing_channels + new_channels
            
            # Save combined channels
            return self.save_channels(all_channels)
            
        except Exception as e:
            self.logger.error(f"Error appending channels: {e}")
            return False
    
    def _convert_to_channels_txt_block(self, channel_data: Dict) -> str:
        """Convert to channels.txt format."""
        block = []
        block.append(f"Group = {channel_data.get('Group', 'Uncategorized')}")
        block.append(f"Stream name = {channel_data.get('Stream name', 'Unknown Channel')}")
        block.append(f"Logo = {channel_data.get('Logo', '')}")
        block.append(f"EPG id = {channel_data.get('EPG id', '')}")
        block.append(f"Stream URL = {channel_data.get('Stream URL', '')}")
        return "\n".join(block)
