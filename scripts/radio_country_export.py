#!/usr/bin/env python3
"""
Multi-Country Radio M3U Playlist Generator
----------------------------------------
This script generates an M3U playlist file containing radio stations 
from multiple specified countries using the radio-browser.info API via the pyradios library.
Features include duplicate removal, default logos, rate limit handling, and country-based grouping.
"""

import sys
import os
import argparse
import time
import random
import requests
from datetime import datetime
from pyradios import RadioBrowser

class RateLimitError(Exception):
    """Exception raised when rate limit is hit"""
    pass

def get_workspace_safe_path(output_file):
    """
    Ensure output path is safe for CI/CD environments.
    If GITHUB_WORKSPACE is set and output_file is relative, use workspace as base.
    """
    if not output_file:
        return None
    
    # If already absolute path, return as-is
    if os.path.isabs(output_file):
        return output_file
    
    # Check if we're in a CI environment with GITHUB_WORKSPACE
    workspace = os.environ.get('GITHUB_WORKSPACE')
    if workspace and os.path.exists(workspace):
        return os.path.join(workspace, output_file)
    
    # Fallback to current working directory for relative paths
    return os.path.abspath(output_file)

def generate_safe_output_path(output_file, country_codes):
    """Generate a safe output path for the playlist file"""
    if not output_file:
        country_string = "_".join(country_codes[:5]).upper()
        if len(country_codes) > 5:
            country_string += "_etc"
        output_file = f"radio_playlist_{country_string}_{datetime.now().strftime('%Y%m%d')}.m3u"
    
    # Make sure the path is workspace-safe
    safe_path = get_workspace_safe_path(output_file)
    print(f"Output file will be created at: {safe_path}")
    return safe_path

def fetch_stations_with_retry(rb, country_code, max_retries=5, initial_backoff=10):
    """
    Fetch stations with retry logic for rate limiting
    
    Args:
        rb: RadioBrowser instance
        country_code: Country code to fetch stations for
        max_retries: Maximum number of retry attempts
        initial_backoff: Initial backoff time in seconds
    
    Returns:
        List of stations
    """
    retry_count = 0
    backoff_time = initial_backoff
    
    while retry_count < max_retries:
        try:
            return rb.stations_by_countrycode(country_code)
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:  # Too Many Requests
                retry_count += 1
                jitter = random.uniform(0.8, 1.2)  # Add some randomness to prevent thundering herd
                wait_time = backoff_time * jitter
                
                print(f"Rate limit exceeded. Waiting for {wait_time:.1f} seconds before retry {retry_count}/{max_retries}...")
                time.sleep(wait_time)
                
                # Exponential backoff: double the wait time for next attempt
                backoff_time *= 2
            else:
                # For other HTTP errors, raise the exception
                raise
    
    # If we've exhausted all retries
    raise RateLimitError(f"Failed to fetch stations for {country_code} after {max_retries} retries due to rate limiting")

def create_multi_country_playlist(country_codes, output_file=None, group_title="Radio Stations", 
                                 default_logo_url="https://amz.odjezdy.online/xbackbone/VUne9/HilOMeka75.png/raw",
                                 use_country_as_group=False):
    """
    Create an M3U playlist for radio stations from multiple specified countries.
    
    Args:
        country_codes (list): List of two-letter country codes (ISO 3166-1 alpha-2)
        output_file (str, optional): Path to output file. If None, generates a default name
        group_title (str, optional): Group title for stations in the playlist
        default_logo_url (str): Default logo URL to use when a station has no logo
        use_country_as_group (bool): If True, use full country name as the group-title
    
    Returns:
        str: Path to the created playlist file
    """
    # Initialize RadioBrowser client
    rb = RadioBrowser()
    
    # Generate safe output filename
    output_file = generate_safe_output_path(output_file, country_codes)
    
    # Get all country information for validation and display
    try:
        countries_info = rb.countries()
        country_dict = {country['iso_3166_1']: country['name'] for country in countries_info}
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 429:  # Too Many Requests
            print("Rate limit exceeded when fetching country list. Waiting 30 seconds and retrying...")
            time.sleep(30)
            countries_info = rb.countries()
            country_dict = {country['iso_3166_1']: country['name'] for country in countries_info}
        else:
            raise
    
    # Validate country codes
    invalid_codes = [code.upper() for code in country_codes if code.upper() not in country_dict]
    if invalid_codes:
        print(f"Warning: The following country codes are invalid: {', '.join(invalid_codes)}")
        country_codes = [code for code in country_codes if code.upper() in country_dict]
        if not country_codes:
            print("No valid country codes provided. Exiting.")
            sys.exit(1)
    
    # Dictionary to track unique stations and avoid duplicates
    # We'll use a combination of station name and URL as the key
    unique_stations = {}
    total_found = 0
    failed_countries = []
    
    # Process each country and collect stations
    for i, country_code in enumerate(country_codes):
        country_code = country_code.upper()
        country_name = country_dict.get(country_code, "Unknown Country")
        
        print(f"[{i+1}/{len(country_codes)}] Fetching stations for {country_name} ({country_code})...")
        try:
            # Use our retry function instead of direct API call
            stations = fetch_stations_with_retry(rb, country_code)
            valid_stations = [s for s in stations if s.get('url')]
            
            if not valid_stations:
                print(f"No stations found for {country_name} ({country_code}).")
                continue
            
            total_found += len(valid_stations)
            print(f"Found {len(valid_stations)} stations for {country_name}.")
            
            # Add each station to our unique stations dictionary
            for station in valid_stations:
                # Create a unique key based on the station name and URL
                # This helps identify genuinely unique stations
                station_key = f"{station['name'].lower()}_{station['url']}"
                
                if station_key not in unique_stations:
                    # Add country code and name to the station data
                    station['country_code'] = country_code
                    station['country_name'] = country_name
                    unique_stations[station_key] = station
                
        except RateLimitError as e:
            print(f"Error: {str(e)}")
            failed_countries.append(country_code)
            continue
        except Exception as e:
            print(f"Error fetching stations for {country_name}: {str(e)}")
            failed_countries.append(country_code)
            continue
        
        # Add a small delay between countries to avoid hitting rate limits
        if i < len(country_codes) - 1:
            time.sleep(random.uniform(0.5, 1.5))
    
    print(f"Found {total_found} total stations, {len(unique_stations)} unique after removing duplicates.")
    
    if failed_countries:
        print(f"Failed to process these countries: {', '.join(failed_countries)}")
        # In CI environment, don't ask for user input - just log and continue
        if os.environ.get('GITHUB_WORKSPACE') or os.environ.get('CI'):
            print("Running in CI environment - skipping retry prompt")
        else:
            retry_option = input("Would you like to retry failed countries? (y/n): ")
            if retry_option.lower() == 'y':
                print("Retrying failed countries...")
                # Wait a bit longer before retrying failed countries
                time.sleep(30)
                return create_multi_country_playlist(failed_countries, 
                                                    f"retry_{os.path.basename(output_file)}", 
                                                    group_title, 
                                                    default_logo_url,
                                                    use_country_as_group)
    
    # Create M3U playlist
    with open(output_file, 'w', encoding='utf-8') as f:
        # Write M3U header
        f.write("#EXTM3U\n")
        
        # Add each unique station to the playlist
        for station in unique_stations.values():
            # Clean station name to avoid issues with special characters
            station_name = station['name'].replace(',', ' ').strip()
            
            # Create the formatted station name with country code prefix
            country_code = station['country_code']
            formatted_name = f"{country_code} | {station_name}"
            
            # Get station logo if available, otherwise use the default logo
            logo_url = station.get('favicon', '')
            if not logo_url or logo_url == "null":
                logo_url = default_logo_url
            
            # Determine which group title to use
            if use_country_as_group:
                station_group = station['country_name']
            else:
                station_group = group_title
            
            # Write the entry in the requested format
            f.write(f'#EXTINF:-1 group-title="{station_group}" tvg-logo="{logo_url}",{formatted_name}\n')
            f.write(f"{station['url']}\n")
    
    print(f"Playlist created: {output_file}")
    print(f"Total unique stations in playlist: {len(unique_stations)}")
    return output_file

def parse_country_codes(countries_str):
    """Parse a comma-separated string of country codes into a list"""
    # Split by comma, strip whitespace, and filter out empty strings
    return [code.strip() for code in countries_str.split(',') if code.strip()]

def main():
    """Main function to handle command line arguments"""
    parser = argparse.ArgumentParser(description="Generate an M3U playlist for radio stations from multiple countries")
    
    # Add a different way to specify countries as a comma-separated string
    parser.add_argument("--countries", type=str, help="Comma-separated list of two-letter country codes (e.g., 'CZ, SK, DE, FR, US')")
    
    # Keep the positional argument for backward compatibility, but make it optional
    parser.add_argument("country_codes", nargs="*", help="Two-letter country codes (e.g., US CZ DE FR)")
    
    parser.add_argument("-o", "--output", help="Output file path")
    parser.add_argument("-g", "--group", default="Radio Stations", help="Group title for stations in the playlist")
    parser.add_argument("--logo", default="https://amz.odjezdy.online/xbackbone/VUne9/HilOMeka75.png/raw", 
                        help="Default logo URL for stations without logos")
    parser.add_argument("--use-country-as-group", "-ucag", action="store_true", 
                        help="Use full country name as the group-title instead of a single group")
    
    args = parser.parse_args()
    
    # Determine which method of specifying countries was used
    if args.countries:
        country_codes = parse_country_codes(args.countries)
    elif args.country_codes:
        country_codes = args.country_codes
    else:
        parser.print_help()
        print("\nError: You must specify country codes either with positional arguments or with --countries")
        sys.exit(1)
    
    try:
        create_multi_country_playlist(country_codes, args.output, args.group, args.logo, args.use_country_as_group)
    except KeyboardInterrupt:
        print("\nProcess interrupted by user. Exiting...")
        sys.exit(1)

if __name__ == "__main__":
    main()
