#!/usr/bin/env python3
"""
Script to scrape Last.fm user events and output them in various formats.
"""

import sys
import time
import argparse
import json
import csv
from typing import List, Dict, Optional
from datetime import datetime
from common import get_all_event_urls, fetch_page, BASE_URL


def get_event_details(event_url: str, verbose: bool = False) -> Optional[Dict[str, str]]:
    """
    Scrape event details from an event page.
    
    Args:
        event_url: URL of the event page
        verbose: Print verbose debug information
    
    Returns:
        Dictionary with event details or None if failed
    """
    soup = fetch_page(event_url, verbose)
    if not soup:
        return None
    
    event_data = {
        'url': event_url,
        'date': '',
        'event_name': '',
        'venue_name': '',
        'venue_city': ''
    }
    
    try:
        # Extract event name (usually in h1)
        event_title = soup.find('h1', class_='event-detail-title')
        if event_title:
            event_data['event_name'] = event_title.get_text(strip=True)
        else:
            # Try alternative selectors
            title_tag = soup.find('h1')
            if title_tag:
                event_data['event_name'] = title_tag.get_text(strip=True)
        
        # Extract date
        date_tag = soup.find('time') or soup.find('abbr', class_='date')
        if date_tag:
            event_data['date'] = date_tag.get_text(strip=True)
        
        # Extract venue information
        venue_tag = soup.find('a', href=lambda x: x and '/venue/' in x)
        if venue_tag:
            event_data['venue_name'] = venue_tag.get_text(strip=True)
        
        # Extract city (often in location or near venue)
        location_tag = soup.find('p', class_='event-detail-location')
        if location_tag:
            location_text = location_tag.get_text(strip=True)
            # Try to extract city (usually after venue name)
            event_data['venue_city'] = location_text
        else:
            # Try to find city in other ways
            city_tag = soup.find('span', class_='venue-city') or soup.find('span', class_='location')
            if city_tag:
                event_data['venue_city'] = city_tag.get_text(strip=True)
        
        if verbose:
            print(f"  Extracted: {event_data['event_name']} @ {event_data['venue_name']}, {event_data['venue_city']} on {event_data['date']}")
    
    except Exception as e:
        if verbose:
            print(f"  Error extracting event details: {e}")
    
    return event_data


def format_as_list(events: List[Dict[str, str]]) -> str:
    """
    Format events as a text list.
    
    Args:
        events: List of event dictionaries
    
    Returns:
        Formatted string
    """
    lines = []
    for event in events:
        date = event.get('date', 'Unknown date')
        name = event.get('event_name', 'Unknown event')
        venue = event.get('venue_name', 'Unknown venue')
        city = event.get('venue_city', 'Unknown city')
        lines.append(f"{date} - {name} @ {venue}, {city}")
    return '\n'.join(lines)


def format_as_json(events: List[Dict[str, str]]) -> str:
    """
    Format events as JSON.
    
    Args:
        events: List of event dictionaries
    
    Returns:
        JSON string
    """
    return json.dumps(events, indent=2, ensure_ascii=False)


def write_as_csv(events: List[Dict[str, str]], filename: str):
    """
    Write events to a CSV file.
    
    Args:
        events: List of event dictionaries
        filename: Output filename
    """
    if not events:
        print("No events to write to CSV", file=sys.stderr)
        return
    
    fieldnames = ['date', 'event_name', 'venue_name', 'venue_city', 'url']
    
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for event in events:
            writer.writerow(event)


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description='Scrape Last.fm user events and output them in various formats.'
    )
    parser.add_argument('username', help='Last.fm username')
    parser.add_argument('start_year', nargs='?', type=int, default=2005,
                        help='Starting year to search (default: 2005)')
    parser.add_argument('end_year', nargs='?', type=int, default=2026,
                        help='Ending year to search (default: 2026)')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Print verbose debug information')
    parser.add_argument('-f', '--format', choices=['list', 'json', 'csv'], default='list',
                        help='Output format (default: list)')
    parser.add_argument('-o', '--output', type=str,
                        help='Output results to a file')
    
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
    
    # Extract event details
    print("\nExtracting event details...")
    events = []
    failed_count = 0
    
    for i, event_url in enumerate(event_urls, 1):
        if not args.verbose:
            print(f"Processing event {i}/{len(event_urls)}...", end='\r')
        else:
            print(f"\nProcessing event {i}/{len(event_urls)}: {event_url}")
        
        event_data = get_event_details(event_url, args.verbose)
        if event_data:
            events.append(event_data)
        else:
            failed_count += 1
        
        time.sleep(5)  # Be nice to the server
    
    print()  # New line after progress
    
    if args.verbose:
        print(f"\nEvents processed: {len(event_urls)}")
        print(f"Events with extraction failures: {failed_count}")
        print(f"Total events extracted: {len(events)}")
    
    # Format and output
    if args.format == 'list':
        output = format_as_list(events)
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(output)
            print(f"\nResults written to: {args.output}")
        else:
            print(f"\nEvents ({len(events)}):")
            print("-" * 50)
            print(output)
    
    elif args.format == 'json':
        output = format_as_json(events)
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(output)
            print(f"\nResults written to: {args.output}")
        else:
            print(f"\nEvents ({len(events)}):")
            print(output)
    
    elif args.format == 'csv':
        if args.output:
            write_as_csv(events, args.output)
            print(f"\nResults written to: {args.output}")
        else:
            # Output to stdout as CSV
            import io
            output = io.StringIO()
            fieldnames = ['date', 'event_name', 'venue_name', 'venue_city', 'url']
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            for event in events:
                writer.writerow(event)
            print(f"\nEvents ({len(events)}):")
            print(output.getvalue())


if __name__ == '__main__':
    main()
