#!/usr/bin/env python3
"""
Quick test script to verify RSS feed fetching with proper headers.
"""

import feedparser
import requests
from io import BytesIO

username = "sama"
query = f"site:twitter.com/{username} OR site:x.com/{username} when:1h"

# URL encode the query
import urllib.parse
encoded_query = urllib.parse.quote(query)
url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"

print(f"Testing RSS feed for @{username}")
print(f"URL: {url}\n")

# Create session with proper headers
session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/rss+xml, application/xml, text/xml, */*',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'DNT': '1',
    'Connection': 'keep-alive',
})

print("Fetching feed with proper headers...")
try:
    response = session.get(url, timeout=10)
    print(f"HTTP Status: {response.status_code}")
    
    if response.status_code == 200:
        feed = feedparser.parse(BytesIO(response.content))
        print(f"Number of entries: {len(feed.entries)}\n")
        
        if feed.entries:
            print("✅ SUCCESS! First entry:")
            entry = feed.entries[0]
            print(f"  Title: {entry.get('title', 'N/A')}")
            print(f"  Link: {entry.get('link', 'N/A')}")
            print(f"  Published: {entry.get('published', 'N/A')}")
        else:
            print("⚠️  No entries found (might be no recent tweets)")
    else:
        print(f"❌ HTTP Error: {response.status_code}")
        print(f"Response: {response.text[:200]}")
        
except Exception as e:
    print(f"❌ Error: {e}")
