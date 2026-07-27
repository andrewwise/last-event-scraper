# Last.fm Event Scraper

Scripts for scraping [Last.fm](https://www.last.fm) event data as the Last.fm API does not provide event information.

## Scripts

### get_events_artists.py

Scrapes a Last.fm user's event pages and lists all artists in alphabetical order.

### get_events.py

Scrapes a Last.fm user's events and outputs event details (date, name, venue, city) in various formats (list, JSON, CSV).

---

## get_events_artists.py

### Setup

1. Install required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Usage

```bash
python get_events_artists.py <username> [start_year] [end_year] [options]
```

**Arguments:**
- `username`: Last.fm username (required)
- `start_year`: Starting year to search (optional, default: 2005)
- `end_year`: Ending year to search (optional, default: 2026)

**Options:**
- `--ignore-the`: Sort artists ignoring "The" at the start (e.g., "The Beatles" appears under "B")
- `--letter-headings`: Include alphabetical letter headings in output (# for numbers/symbols, then A-Z, showing all letters even empty ones)
- `-v, --verbose`: Print verbose debug information (shows HTTP status codes, URLs being processed, retry attempts, and detailed error messages)
- `-o, --output <file>`: Output results to a text file instead of printing to console

**Examples:**

```bash
# Scrape all events for user (2005-2026)
python get_events_artists.py yz_rules

# Scrape events for specific year range
python get_events_artists.py yz_rules 2020 2025

# Sort ignoring "The" at the start
python get_events_artists.py yz_rules --ignore-the

# Include letter headings (# for numbers/symbols, A, B, C, etc.)
python get_events_artists.py yz_rules --letter-headings

# Output to a text file
python get_events_artists.py yz_rules -o artists.txt

# Enable verbose mode for debugging
python get_events_artists.py yz_rules --verbose

# Combine all options
python get_events_artists.py yz_rules 2020 2025 --ignore-the --letter-headings --verbose -o artists.txt
```

### How it works

1. Scrapes the user's main events page: `https://www.last.fm/user/{username}/events`
2. Scrapes events from each year: `https://www.last.fm/user/{username}/events/{year}`
3. Extracts event URLs from these pages
4. Visits each event's lineup page to extract artist names
5. Outputs all unique artists in alphabetical order

### Output

The script will display:
- Progress as it fetches events from each year
- Number of events found
- List of unique artists in alphabetical order (or with letter headings if `--letter-headings` is used)
- Total count of unique artists

With `--verbose` flag enabled:
- HTTP status codes for each request
- Number of links found on each page
- Individual event URLs being processed
- Number of artists found per event
- Retry attempts and detailed error messages
- Summary statistics (events processed, events with no artists, total unique artists)

### Features

- **Automatic retry**: Requests that fail or return non-200 status codes are retried up to 3 times with 5-second delays
- **Rate limiting**: Built-in delays between requests to be respectful to Last.fm's servers
- **Flexible sorting**: Option to ignore "The" prefix when sorting artists
- **Letter headings**: Organize output by alphabetical sections (including # for numbers/symbols)
- **File output**: Save results to a text file for later use
- **Verbose debugging**: Detailed logging to troubleshoot issues

**Note:** The script includes delays between requests to be respectful to Last.fm's servers.

---

## get_events.py

### Setup

Same as above - install dependencies with `pip install -r requirements.txt`

### Usage

```bash
python get_events.py <username> [start_year] [end_year] [options]
```

**Arguments:**
- `username`: Last.fm username (required)
- `start_year`: Starting year to search (optional, default: 2005)
- `end_year`: Ending year to search (optional, default: 2026)

**Options:**
- `-f, --format {list,json,csv}`: Output format (default: list)
  - `list`: Human-readable text format: "Date - Event name @ Venue Name, Venue City"
  - `json`: JSON array with event objects
  - `csv`: CSV file with columns: date, event_name, venue_name, venue_city, url
- `-v, --verbose`: Print verbose debug information
- `-o, --output <file>`: Output results to a file (required for CSV, optional for list/json)

**Examples:**

```bash
# Get events in list format
python get_events.py yz_rules

# Get events in JSON format
python get_events.py yz_rules --format json

# Export to CSV file
python get_events.py yz_rules --format csv -o events.csv

# Get events for specific years with verbose output
python get_events.py yz_rules 2020 2025 --verbose

# Output as JSON to file
python get_events.py yz_rules --format json -o events.json
```

### Output Format Examples

**List format:**
```
15 Feb 2020 - Festival Name @ Venue Name, London
20 Mar 2020 - Band Name @ Club Name, Manchester
```

**JSON format:**
```json
[
  {
    "date": "15 Feb 2020",
    "event_name": "Festival Name",
    "venue_name": "Venue Name",
    "venue_city": "London",
    "url": "https://www.last.fm/event/..."
  }
]
```

**CSV format:**
```
date,event_name,venue_name,venue_city,url
15 Feb 2020,Festival Name,Venue Name,London,https://www.last.fm/event/...
```

### Features

- **Multiple output formats**: List, JSON, and CSV for different use cases
- **Automatic retry**: Same retry logic as get_events_artists.py
- **Comprehensive data**: Extracts date, event name, venue name, and city
- **Rate limiting**: Built-in delays to respect Last.fm's servers

---

## Common Functions

Both scripts use shared functions from `common.py`:
- `get_all_event_urls()`: Fetches event URLs from user pages
- `fetch_page()`: Fetches and parses web pages with retry logic
