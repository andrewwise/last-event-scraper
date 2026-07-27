#!/usr/bin/env python3
"""
Script to scrape Last.fm user events and list all artists alphabetically.
"""

import sys
import time
import argparse
from typing import Set, List
from common import get_all_event_urls, fetch_page, BASE_URL


def get_artists_from_event(event_url: str, verbose: bool = False) -> Set[str]:
    """
    Scrape artists from an event lineup page.
    
    Args:
        event_url: URL of the event lineup page (should end with /lineup)
        verbose: Print verbose debug information
    
    Returns:
        Set of artist names
    """
    artists = set()
    
    # Add /lineup if not already present
    if not event_url.endswith('/lineup'):
        event_url = event_url + '/lineup'
    
    soup = fetch_page(event_url, verbose)
    if not soup:
        return artists
    
    try:
        # Look for artist links in the lineup
        # They typically have class 'link-block-target' or are in the lineup section
        artist_links = soup.find_all('a', class_='link-block-target')
        for link in artist_links:
            artist_name = link.get_text(strip=True)
            if artist_name:
                artists.add(artist_name)
        
        # Also check for headliner and artists in h1/h2 tags
        for tag in soup.find_all(['h1', 'h2', 'h3']):
            if 'event-detail-artists' in tag.get('class', []):
                artist_name = tag.get_text(strip=True)
                if artist_name:
                    artists.add(artist_name)
        
        # Check for artist list items
        lineup_section = soup.find('section', class_='lineup-section') or soup.find('div', class_='lineup')
        if lineup_section:
            for item in lineup_section.find_all('li'):
                artist_link = item.find('a')
                if artist_link:
                    artist_name = artist_link.get_text(strip=True)
                    if artist_name:
                        artists.add(artist_name)
        
        if verbose and not artists:
            print(f"\n  Warning: No artists found for {event_url}")
    
    except Exception as e:
        if verbose:
            print(f"\n  Error extracting artists: {e}")
    
    return artists


def sort_artists(artists: Set[str], ignore_the: bool = False) -> List[str]:
    """
    Sort artists alphabetically.
    
    Args:
        artists: Set of artist names
        ignore_the: If True, ignore "The" at the start when sorting
    
    Returns:
        Sorted list of artist names
    """
    def sort_key(artist: str) -> str:
        if ignore_the and artist.lower().startswith('the '):
            # Remove "The " for sorting purposes
            return artist[4:].lower()
        return artist.lower()
    
    return sorted(artists, key=sort_key)


def format_output_with_headings(sorted_artists: List[str], ignore_the: bool = False) -> List[str]:
    """
    Format output with alphabetical letter headings.
    
    Args:
        sorted_artists: Sorted list of artist names
        ignore_the: If True, group by letter ignoring "The" at the start
    
    Returns:
        List of output lines with headings
    """
    output_lines = []
    
    # First, handle numbers and symbols
    output_lines.append(f"\n=== # (Numbers & Symbols) ===")
    numbers_symbols = []
    for artist in sorted_artists:
        # Determine which character to check
        check_char = artist[0].upper()
        if ignore_the and artist.lower().startswith('the ') and len(artist) > 4:
            check_char = artist[4].upper()
        
        # If not A-Z, it's a number or symbol
        if not check_char.isalpha():
            numbers_symbols.append(artist)
    
    if numbers_symbols:
        output_lines.extend(numbers_symbols)
    else:
        output_lines.append("(none)")
    
    # Go through all letters A-Z
    for letter in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
        output_lines.append(f"\n=== {letter} ===")
        
        # Find artists that start with this letter
        artists_for_letter = []
        for artist in sorted_artists:
            # Determine which letter to group by
            group_letter = artist[0].upper()
            if ignore_the and artist.lower().startswith('the ') and len(artist) > 4:
                group_letter = artist[4].upper()
            
            if group_letter == letter:
                artists_for_letter.append(artist)
        
        if artists_for_letter:
            output_lines.extend(artists_for_letter)
        else:
            output_lines.append("(none)")
    
    return output_lines


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description='Scrape Last.fm user events and list all artists alphabetically.'
    )
    parser.add_argument('username', help='Last.fm username')
    parser.add_argument('start_year', nargs='?', type=int, default=2005,
                        help='Starting year to search (default: 2005)')
    parser.add_argument('end_year', nargs='?', type=int, default=2026,
                        help='Ending year to search (default: 2026)')
    parser.add_argument('--ignore-the', action='store_true',
                        help='Sort artists ignoring "The" at the start (e.g., "The Beatles" under "B")')
    parser.add_argument('--letter-headings', action='store_true',
                        help='Include alphabetical letter headings in output')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Print verbose debug information')
    parser.add_argument('-o', '--output', type=str,
                        help='Output results to a text file')
    
    args = parser.parse_args()
    
    username = args.username
    start_year = args.start_year
    end_year = args.end_year
    
    print(f"Scraping events for user: {username}")
    print(f"Searching from {start_year} to {end_year}")
    print("-" * 50)
    
    # Get all event URLs
    event_urls = get_all_event_urls(username, start_year, end_year, args.verbose)
    print(f"\nTotal events found: {len(event_urls)}")
    
    if args.verbose:
        print("\nEvent URLs:")
        for url in event_urls[:10]:  # Show first 10
            print(f"  {url}")
        if len(event_urls) > 10:
            print(f"  ... and {len(event_urls) - 10} more")
    
    if not event_urls:
        print(f"No events found for user: {username}")
        sys.exit(0)
    
    # Extract artists from each event
    print("\nExtracting artists from events...")
    all_artists = set()
    failed_count = 0
    
    for i, event_url in enumerate(event_urls, 1):
        if not args.verbose:
            print(f"Processing event {i}/{len(event_urls)}...", end='\r')
        else:
            print(f"\nProcessing event {i}/{len(event_urls)}: {event_url}")
        
        artists = get_artists_from_event(event_url, args.verbose)
        if artists:
            all_artists.update(artists)
            if args.verbose:
                print(f"  Found {len(artists)} artist(s): {', '.join(list(artists)[:3])}{'...' if len(artists) > 3 else ''}")
        else:
            failed_count += 1
        
        time.sleep(5)  # Be nice to the server
    
    print()  # New line after progress
    
    if args.verbose:
        print(f"\nEvents processed: {len(event_urls)}")
        print(f"Events with no artists found: {failed_count}")
        print(f"Total unique artists: {len(all_artists)}")
    for i, event_url in enumerate(event_urls, 1):
        print(f"Processing event {i}/{len(event_urls)}...", end='\r')
        artists = get_artists_from_event(event_url)
        all_artists.update(artists)
        time.sleep(5)  # Be nice to the server
    
    print()  # New line after progress
    
    # Sort artists alphabetically
    sorted_artists = sort_artists(all_artists, args.ignore_the)
    
    # Prepare output
    output_lines = [f"Artists ({len(sorted_artists)} unique):"]
    
    if args.letter_headings:
        output_lines.extend(format_output_with_headings(sorted_artists, args.ignore_the))
    else:
        output_lines.append("-" * 50)
        output_lines.extend(sorted_artists)
    
    # Output to file or stdout
    if args.output:
        try:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write('\n'.join(output_lines) + '\n')
            print(f"\nResults written to: {args.output}")
        except IOError as e:
            print(f"Error writing to file: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        for line in output_lines:
            print(line)


if __name__ == '__main__':
    main()
