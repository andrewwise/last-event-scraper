#!/usr/bin/env python3
"""
Common functions shared across Last.fm scraping scripts.
"""

import requests
from bs4 import BeautifulSoup
import sys
import time
from typing import List
from urllib.parse import urljoin

BASE_URL = 'https://www.last.fm'


def get_event_urls_from_page(url: str, verbose: bool = False) -> List[str]:
    """
    Scrape event URLs from a user's events page.
    
    Args:
        url: URL of the events page
        verbose: Print verbose debug information
    
    Returns:
        List of event URLs
    """
    event_urls = []
    max_retries = 3
    
    for attempt in range(max_retries):
        try:
            if verbose:
                print(f"  Fetching: {url} (attempt {attempt + 1}/{max_retries})")
            response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
            
            if response.status_code == 200:
                if verbose:
                    print(f"  Status: {response.status_code}")
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Find all event links - look for links with specific classes used by Last.fm
                # Try multiple selectors to be more robust
                event_links = []
                
                # Look for event cards/items with specific classes
                event_cards = soup.find_all(['div', 'li', 'article'], class_=lambda x: x and ('event' in x.lower() or 'card' in x.lower()))
                for card in event_cards:
                    links = card.find_all('a', href=True)
                    event_links.extend(links)
                
                # Also get all links and filter
                all_links = soup.find_all('a', href=True)
                event_links.extend(all_links)
                
                if verbose:
                    print(f"  Total links found: {len(event_links)}")
                
                for link in event_links:
                    href = link['href']
                    if '/event/' in href:
                        if verbose:
                            print(f"    Found event link: {href}")
                        full_url = urljoin(BASE_URL, href)
                        # Clean up the URL - remove query params and unwanted paths
                        full_url = full_url.split('?')[0]
                        # Remove trailing paths like /attendance, /going, /interested
                        for suffix in ['/attendance', '/going', '/interested', '/lineup']:
                            if full_url.endswith(suffix):
                                full_url = full_url[:-len(suffix)]
                        if full_url not in event_urls:
                            event_urls.append(full_url)
                
                if verbose:
                    print(f"  Found {len(event_urls)} unique event URLs")
                break  # Success, exit retry loop
            else:
                print(f"  Status {response.status_code} for {url}, retrying in 30 seconds...", file=sys.stderr)
                if attempt < max_retries - 1:
                    time.sleep(30)
                else:
                    print(f"  Failed after {max_retries} attempts", file=sys.stderr)
        
        except requests.exceptions.RequestException as e:
            print(f"Error fetching {url}: {e}", file=sys.stderr)
            if verbose:
                print(f"  Full error: {repr(e)}")
            if attempt < max_retries - 1:
                print(f"  Retrying in 30 seconds...", file=sys.stderr)
                time.sleep(30)
            else:
                print(f"  Failed after {max_retries} attempts", file=sys.stderr)
    
    return event_urls


def get_all_event_urls(username: str, start_year: int = 2005, end_year: int = 2026, verbose: bool = False) -> List[str]:
    """
    Get all event URLs for a user across multiple years.
    
    Args:
        username: Last.fm username
        start_year: Starting year to search
        end_year: Ending year to search
        verbose: Print verbose debug information
    
    Returns:
        List of all event URLs
    """
    all_event_urls = []
    
    # Get events from main events page
    print(f"Fetching events from main page...")
    main_url = f"{BASE_URL}/user/{username}/events"
    event_urls = get_event_urls_from_page(main_url, verbose)
    all_event_urls.extend(event_urls)
    print(f"Found {len(event_urls)} events on main page")
    time.sleep(5)  # Be nice to the server
    
    # Get events from each year
    for year in range(start_year, end_year + 1):
        print(f"Fetching events from {year}...")
        year_url = f"{BASE_URL}/user/{username}/events/{year}"
        event_urls = get_event_urls_from_page(year_url, verbose)
        
        # Add only new URLs
        new_urls = [url for url in event_urls if url not in all_event_urls]
        all_event_urls.extend(new_urls)
        print(f"Found {len(new_urls)} new events in {year}")
        time.sleep(5)  # Be nice to the server
    
    return all_event_urls


def fetch_page(url: str, verbose: bool = False, max_retries: int = 3) -> BeautifulSoup:
    """
    Fetch and parse a web page with retry logic.
    
    Args:
        url: URL to fetch
        verbose: Print verbose debug information
        max_retries: Maximum number of retry attempts
    
    Returns:
        BeautifulSoup object or None if failed
    """
    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
            
            if response.status_code == 200:
                return BeautifulSoup(response.content, 'html.parser')
            else:
                if verbose or attempt == max_retries - 1:
                    print(f"\n  Status {response.status_code} for {url}, retrying in 30 seconds...", file=sys.stderr)
                if attempt < max_retries - 1:
                    time.sleep(30)
                else:
                    print(f"  Failed after {max_retries} attempts", file=sys.stderr)
        
        except requests.exceptions.RequestException as e:
            if verbose or attempt == max_retries - 1:
                print(f"\nError fetching {url}: {e}", file=sys.stderr)
            if verbose:
                print(f"  Full error: {repr(e)}")
            if attempt < max_retries - 1:
                if verbose:
                    print(f"  Retrying in 30 seconds...", file=sys.stderr)
                time.sleep(30)
            else:
                if verbose:
                    print(f"  Failed after {max_retries} attempts", file=sys.stderr)
    
    return None
