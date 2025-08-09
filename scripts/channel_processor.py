def detect_country_from_channel(self, channel_name: str, epg_id: str = "", logo_url: str = "") -> str:
        """Enhanced country detection with priority rules and platform detection."""
        # Create cache key
        cache_key = f"{channel_name}|{epg_id}|{logo_url}"
        if cache_key in self._country_cache:
            return self._country_cache[cache_key]
        
        # Combine all text for analysis
        all_text = f"{channel_name.lower().strip()} {epg_id.lower().strip()} {logo_url.lower().strip()}"
        channel_lower = channel_name.lower()
        
        # PRIORITY 1: EPG ID suffix detection (most reliable)
        if ".ca" in epg_id.lower():
            result = "🇨🇦 Canada"
            self._country_cache[cache_key] = result
            self.logger.debug(f"Detected {result} for: {channel_name} (EPG: .ca)")
            return result
        elif ".us" in epg_id.lower():
            result = "🇺🇸 United States"
            self._country_cache[cache_key] = result
            self.logger.debug(f"Detected {result} for: {channel_name} (EPG: .us)")
            return result
        elif ".uk" in epg_id.lower():
            result = "🇬🇧 United Kingdom"
            self._country_cache[cache_key] = result
            self.logger.debug(f"Detected {result} for: {channel_name} (EPG: .uk)")
            return result
        elif ".ph" in epg_id.lower():
            result = "🇵🇭 Philippines"
            self._country_cache[cache_key] = result
            self.logger.debug(f"Detected {result} for: {channel_name} (EPG: .ph)")
            return result
        elif ".au" in epg_id.lower():
            result = "🇦🇺 Australia"
            self._country_cache[cache_key] = result
            self.logger.debug(f"Detected {result} for: {channel_name} (EPG: .au)")
            return result
        elif ".jp" in epg_id.lower():
            result = "🇯🇵 Japan"
            self._country_cache[cache_key] = result
            self.logger.debug(f"Detected {result} for: {channel_name} (EPG: .jp)")
            return result
        
        # PRIORITY 2: Specific channel fixes for misclassified channels
        
        # Canadian sports channels (TSN series)
        if any(x in channel_lower for x in ["tsn 1", "tsn 2", "tsn 3", "tsn 4", "tsn 5", "tsn1", "tsn2", "tsn3", "tsn4", "tsn5"]):
            result = "🇨🇦 Canada"
            self._country_cache[cache_key] = result
            self.logger.debug(f"Detected {result} for: {channel_name} (TSN Sports)")
            return result
        
        # CBC News Toronto (Canadian)
        if "cbc news toronto" in channel_lower:
            result = "🇨🇦 Canada"
            self._country_cache[cache_key] = result
            self.logger.debug(f"Detected {result} for: {channel_name} (CBC Toronto)")
            return result
        
        # US channels that were misclassified
        if any(x in channel_lower for x in ["tv land", "tvland", "we tv", "wetv", "all weddings we tv", "cheaters", "cheers", "christmas 365"]):
            result = "🇺🇸 United States"
            self._country_cache[cache_key] = result
            self.logger.debug(f"Detected {result} for: {channel_name} (US Network)")
            return result
        
        # UK shows/channels
        if "come dine with me" in channel_lower:
            result = "🇬🇧 United Kingdom"
            self._country_cache[cache_key] = result
            self.logger.debug(f"Detected {result} for: {channel_name} (UK Show)")
            return result
        
        # Philippines news channels
        if any(x in channel_lower for x in ["anc global", "anc ph"]):
            result = "🇵🇭 Philippines"
            self._country_cache[cache_key] = result
            self.logger.debug(f"Detected {result} for: {channel_name} (Philippines News)")
            return result
        
        # Japan anime channels
        if "animax" in channel_lower:
            result = "🇯🇵 Japan"
            self._country_cache[cache_key] = result
            self.logger.debug(f"Detected {result} for: {channel_name} (Japanese Anime)")
            return result
        
        # PRIORITY 3: Platform-based detection
        
        # Pluto TV special handling
        if "pluto.tv" in all_text or "images.pluto.tv" in all_text or "jmp2.uk/plu-" in all_text:
            # Pluto TV regional overrides
            pluto_overrides = {
                "cbc news toronto": "🇨🇦 Canada",
                "come dine with me": "🇬🇧 United Kingdom"
            }
            
            for channel_pattern, country in pluto_overrides.items():
                if channel_pattern in channel_lower:
                    result = country
                    self._country_cache[cache_key] = result
                    self.logger.debug(f"Detected {result} for: {channel_name} (Pluto TV Regional)")
                    return result
            
            # Default Pluto TV to US
            result = "🇺🇸 United States"
            self._country_cache[cache_key] = result
            self.logger.debug(f"Detected {result} for: {channel_name} (Pluto TV Default)")
            return result
        
        # Plex TV handling (mostly US)
        if "plex.tv" in all_text or "provider-static.plex.tv" in all_text:
            result = "🇺🇸 United States"
            self._country_cache[cache_key] = result
            self.logger.debug(f"Detected {result} for: {channel_name} (Plex TV)")
            return result
        
        # PRIORITY 4: Check prefixes (existing logic)
        for country, prefixes in self.config.patterns["country_prefixes"].items():
            for prefix in prefixes:
                if prefix in all_text:
                    self._country_cache[cache_key] = country
                    self.logger.debug(f"Detected {country} for: {channel_name} (prefix: '{prefix}')")
                    return country
        
        # PRIORITY 5: Check general patterns (existing logic)
        for country, keywords in self.config.patterns["country_patterns"].items():
            for keyword in keywords:
                if keyword in all_text:
                    self._country_cache[cache_key] = country
                    self.logger.debug(f"Detected {country} for: {channel_name} (keyword: '{keyword}')")
                    return country
        
        # Cache negative result too
        self._country_cache[cache_key] = "Uncategorized"
        self.logger.debug(f"No country detected for: {channel_name} - marked as Uncategorized")
        return "Uncategorized"
