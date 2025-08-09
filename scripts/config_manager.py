"""
Configuration Manager - Handles all configuration loading and management
Pure country-based detection with enhanced patterns
"""

import json
import os
import logging
from pathlib import Path

class ConfigManager:
    """Centralized configuration management for pure country-based organization."""
    
    def __init__(self, config_dir="config"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
        
        # File paths
        self.channels_file = "channels.txt"
        self.playlist_file = "playlist.m3u"
        self.import_file = "bulk_import.m3u"
        self.log_file = "playlist_update.log"
        
        # Config files (removed group_overrides)
        self.settings_file = self.config_dir / "settings.json"
        self.patterns_file = self.config_dir / "patterns.json"
        
        # Load configurations
        self.settings = self._load_settings()
        self.patterns = self._load_patterns()
        
        # No group overrides - pure country detection
        self.group_overrides = {}
        
        logging.info("Configuration manager initialized (Pure Country Mode)")
    
    def _load_settings(self):
        """Load settings with comprehensive defaults."""
        defaults = {
            "remove_duplicates": True,
            "sort_channels": True,
            "backup_before_import": True,
            "auto_cleanup_import": True,
            "auto_detect_country": True,
            "detect_quality": True,
            "skip_adult_content": True,
            "min_channel_name_length": 2,
            "max_workers": 4,
            "enable_health_check": False,
            "health_check_timeout": 5,
            "create_backup": True,
            "max_backups": 5,
            "log_level": "INFO",
            "clear_import_after_processing": True,
            "delete_import_file": False,
            # Enhanced country detection settings
            "pure_country_mode": True,
            "prefer_country_over_category": True,
            "enable_prefix_detection": True,
            "enable_quality_tags": True
        }
        
        if self.settings_file.exists():
            try:
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    user_settings = json.load(f)
                    merged = {**defaults, **user_settings}
                    logging.info(f"Loaded user settings from {self.settings_file}")
                    return merged
            except (json.JSONDecodeError, IOError) as e:
                logging.warning(f"Could not load settings, using defaults: {e}")
        else:
            # Create default settings file
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(defaults, f, indent=2)
            logging.info(f"Created default settings file: {self.settings_file}")
        
        return defaults
    
    def _load_patterns(self):
        """Load enhanced country detection patterns from external config."""
        # This will be the fallback if patterns.json doesn't exist
        minimal_patterns = {
            "country_patterns": {
                "🇺🇸 United States": ["cbs", "nbc", "abc", "fox", "espn", "cnn", "hbo", "usa", "america", "nfl"],
                "🇬🇧 United Kingdom": ["bbc", "itv", "sky", "channel 4", "e4", "uk", "british", "premier league"],
                "🇨🇦 Canada": ["cbc", "ctv", "global", "canada", "canadian"],
                "🇩🇪 Germany": ["ard", "zdf", "rtl", "sat.1", "pro7", "germany", "german"],
                "🇫🇷 France": ["tf1", "france 2", "m6", "canal+", "france", "french"],
                "🇪🇸 Spain": ["tve", "antena 3", "telecinco", "spain", "spanish"],
                "🇮🇹 Italy": ["rai", "mediaset", "canale 5", "italy", "italian"],
                "🇳🇱 Netherlands": ["npo", "rtl nl", "netherlands", "dutch", "holland"],
                "🇧🇷 Brazil": ["globo", "band", "sbt", "brazil", "brasil"],
                "🇦🇷 Argentina": ["telefe", "canal 13", "argentina"],
                "🇲🇽 Mexico": ["televisa", "tv azteca", "mexico", "méxico"],
                "🇦🇺 Australia": ["abc au", "seven", "nine", "ten", "australia", "australian"],
                "🇸🇦 Arabic": ["al jazeera", "mbc", "lbc", "dubai tv", "arabic", "arab"]
            },
            "country_prefixes": {
                "🇺🇸 United States": ["us:", "us |", "usa:"],
                "🇬🇧 United Kingdom": ["uk:", "uk |", "gb:"],
                "🇩🇪 Germany": ["de:", "de |", "ger:"],
                "🇫🇷 France": ["fr:", "fr |", "france:"],
                "🇪🇸 Spain": ["es:", "es |", "spain:"],
                "🇮🇹 Italy": ["it:", "it |", "italy:"],
                "🇺🇦 Ukraine": ["ua:", "ua |", "ukraine:"],
                "🇵🇱 Poland": ["pl:", "pl |", "poland:"],
                "🇹🇷 Turkey": ["tr:", "tr |", "turkey:"],
                "🇲🇾 Malaysia": ["my:", "my |", "malaysia:"],
                "🇦🇺 Australia": ["au:", "au |", "australia:"],
                "🇨🇦 Canada": ["ca:", "ca |", "canada:"]
            },
            "quality_patterns": {
                "4K": ["4k", "uhd", "2160p", "ultra hd"],
                "FHD": ["fhd", "1080p", "1080", "full hd"],
                "HD": ["hd", "720p", "720", "high definition"],
                "SD": ["sd", "480p", "360p", "standard"]
            },
            "adult_keywords": [
                "xxx", "adult", "porn", "sex", "erotic", "playboy", "18+", 
                "nude", "naked", "sexy", "babes"
            ]
        }
        
        if self.patterns_file.exists():
            try:
                with open(self.patterns_file, 'r', encoding='utf-8') as f:
                    user_patterns = json.load(f)
                    logging.info(f"Loaded enhanced patterns from {self.patterns_file}")
                    
                    # Validate that required sections exist
                    required_sections = ["country_patterns", "country_prefixes", "quality_patterns", "adult_keywords"]
                    for section in required_sections:
                        if section not in user_patterns:
                            logging.warning(f"Missing section '{section}' in patterns file, using minimal fallback")
                            user_patterns[section] = minimal_patterns.get(section, {})
                    
                    return user_patterns
            except (json.JSONDecodeError, IOError) as e:
                logging.warning(f"Could not load patterns, using minimal patterns: {e}")
        else:
            # Create minimal patterns file (user should update with enhanced version)
            with open(self.patterns_file, 'w', encoding='utf-8') as f:
                json.dump(minimal_patterns, f, indent=2, ensure_ascii=False)
            logging.info(f"Created minimal patterns file: {self.patterns_file}")
            logging.info("Update patterns.json with enhanced version for better detection")
        
        return minimal_patterns
    
    def get_country_detection_stats(self):
        """Get statistics about country detection capabilities."""
        stats = {
            'total_countries': len(self.patterns.get('country_patterns', {})),
            'total_prefixes': len(self.patterns.get('country_prefixes', {})),
            'total_patterns': 0,
            'quality_levels': len(self.patterns.get('quality_patterns', {})),
            'adult_keywords': len(self.patterns.get('adult_keywords', [])),
            'pure_country_mode': True
        }
        
        # Count total detection patterns
        for country, patterns in self.patterns.get('country_patterns', {}).items():
            stats['total_patterns'] += len(patterns)
        
        return stats
    
    def validate_patterns(self):
        """Validate pattern configuration and return any issues."""
        issues = []
        
        # Check for required sections
        required_sections = ['country_patterns', 'country_prefixes', 'quality_patterns', 'adult_keywords']
        for section in required_sections:
            if section not in self.patterns:
                issues.append(f"Missing required section: {section}")
        
        # Check for empty country patterns
        country_patterns = self.patterns.get('country_patterns', {})
        if not country_patterns:
            issues.append("No country patterns defined")
        else:
            for country, patterns in country_patterns.items():
                if not patterns or not isinstance(patterns, list):
                    issues.append(f"Invalid or empty patterns for country: {country}")
        
        # Check for duplicate patterns across countries
        all_patterns = []
        for country, patterns in country_patterns.items():
            for pattern in patterns:
                if pattern in all_patterns:
                    issues.append(f"Duplicate pattern '{pattern}' found in multiple countries")
                all_patterns.append(pattern)
        
        return issues
    
    def get_countries_list(self):
        """Get a list of all supported countries."""
        return list(self.patterns.get('country_patterns', {}).keys())
    
    def save_settings(self):
        """Save current settings to file."""
        try:
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2)
            logging.info("Settings saved successfully")
            return True
        except Exception as e:
            logging.error(f"Could not save settings: {e}")
            return False
    
    def update_setting(self, key, value):
        """Update a specific setting."""
        self.settings[key] = value
        logging.info(f"Updated setting: {key} = {value}")
    
    def is_pure_country_mode(self):
        """Check if pure country mode is enabled."""
        return self.settings.get('pure_country_mode', True)
    
    def get_detection_summary(self):
        """Get a summary of detection capabilities for logging."""
        stats = self.get_country_detection_stats()
        return (f"Country Detection: {stats['total_countries']} countries, "
                f"{stats['total_patterns']} patterns, "
                f"{stats['total_prefixes']} prefixes, "
                f"Mode: Pure Country")
    
    def cleanup_old_config_files(self):
        """Remove old group overrides file if it exists."""
        old_overrides_file = self.config_dir / "group_overrides.json"
        if old_overrides_file.exists():
            try:
                old_overrides_file.unlink()
                logging.info("Removed obsolete group_overrides.json file")
                return True
            except Exception as e:
                logging.warning(f"Could not remove old group_overrides.json: {e}")
        return False
