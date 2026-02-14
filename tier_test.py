#!/usr/bin/env python3
"""
X API Tier Detection Script
This will tell us exactly what access level you have and what endpoints are available.
"""

import requests
import json
from datetime import datetime

# INSTRUCTIONS:
# 1. Get your Bearer Token from X Developer Portal
# 2. Replace 'YOUR_BEARER_TOKEN' below
# 3. Run: python3 api_tier_test.py

BEARER_TOKEN = "YOUR_BEARER_TOKEN_HERE"  # ← PUT YOUR TOKEN HERE

def make_request(url, params=None):
    """Make API request and return response with rate limit info"""
    headers = {
        "Authorization": f"Bearer {BEARER_TOKEN}",
        "User-Agent": "v2TierTestPython"
    }
    
    response = requests.get(url, headers=headers, params=params)
    
    return {
        "status_code": response.status_code,
        "rate_limit_remaining": response.headers.get("x-rate-limit-remaining"),
        "rate_limit_limit": response.headers.get("x-rate-limit-limit"),
        "rate_limit_reset": response.headers.get("x-rate-limit-reset"),
        "data": response.json() if response.status_code == 200 else response.text
    }

def test_tier():
    """Test different endpoints to determine tier"""
    
    print("=" * 60)
    print("X API TIER DETECTION TEST")
    print("=" * 60)
    print()
    
    # Test 1: Get your own user info (works on all tiers)
    print("TEST 1: Getting your user info...")
    result = make_request(
        "https://api.twitter.com/2/users/me",
        params={"user.fields": "public_metrics"}
    )
    
    if result["status_code"] == 200:
        user_data = result["data"]["data"]
        print(f"✓ SUCCESS - You are: @{user_data['username']}")
        print(f"  Followers: {user_data['public_metrics']['followers_count']}")
        print(f"  Rate limit: {result['rate_limit_remaining']}/{result['rate_limit_limit']} remaining")
    else:
        print(f"✗ FAILED - Status: {result['status_code']}")
        print(f"  Error: {result['data']}")
        return
    
    print()
    
    # Test 2: Search recent tweets (limits vary by tier)
    print("TEST 2: Testing search recent (CRITICAL for your use case)...")
    result = make_request(
        "https://api.twitter.com/2/tweets/search/recent",
        params={
            "query": "python backend -is:retweet",
            "max_results": 10,
            "tweet.fields": "public_metrics,created_at,author_id"
        }
    )
    
    if result["status_code"] == 200:
        print(f"✓ SEARCH WORKS!")
        print(f"  Rate limit: {result['rate_limit_remaining']}/{result['rate_limit_limit']} remaining")
        tweets = result["data"].get("data", [])
        print(f"  Found {len(tweets)} tweets")
    elif result["status_code"] == 403:
        print(f"✗ SEARCH BLOCKED - You likely have Free tier (no search access)")
    else:
        print(f"✗ SEARCH FAILED - Status: {result['status_code']}")
        print(f"  Response: {result['data']}")
    
    print()
    
    # Test 3: Get user by username (works on all tiers)
    print("TEST 3: Testing user lookup...")
    result = make_request(
        "https://api.twitter.com/2/users/by/username/elonmusk",
        params={"user.fields": "public_metrics"}
    )
    
    if result["status_code"] == 200:
        print(f"✓ USER LOOKUP WORKS")
        print(f"  Rate limit: {result['rate_limit_remaining']}/{result['rate_limit_limit']} remaining")
    else:
        print(f"✗ USER LOOKUP FAILED - Status: {result['status_code']}")
    
    print()
    
    # Test 4: Get user's tweets (critical for scraping accounts)
    print("TEST 4: Testing user timeline retrieval...")
    result = make_request(
        "https://api.twitter.com/2/users/44196397/tweets",  # Elon Musk's ID
        params={
            "max_results": 10,
            "tweet.fields": "public_metrics,created_at",
            "exclude": "retweets,replies"
        }
    )
    
    if result["status_code"] == 200:
        print(f"✓ USER TIMELINE WORKS")
        print(f"  Rate limit: {result['rate_limit_remaining']}/{result['rate_limit_limit']} remaining")
    else:
        print(f"✗ USER TIMELINE FAILED - Status: {result['status_code']}")
    
    print()
    
    # Test 5: Get conversation thread (critical for reply analysis)
    print("TEST 5: Testing conversation thread lookup...")
    # Using a known tweet ID
    result = make_request(
        "https://api.twitter.com/2/tweets/search/recent",
        params={
            "query": "conversation_id:1234567890",
            "max_results": 10
        }
    )
    
    if result["status_code"] == 200:
        print(f"✓ CONVERSATION LOOKUP WORKS")
        print(f"  Rate limit: {result['rate_limit_remaining']}/{result['rate_limit_limit']} remaining")
    elif result["status_code"] == 403:
        print(f"✗ CONVERSATION LOOKUP BLOCKED (needs Basic tier or higher)")
    else:
        print(f"✗ Status: {result['status_code']}")
    
    print()
    print("=" * 60)
    print("TIER ASSESSMENT:")
    print("=" * 60)
    
    # Determine tier based on what works
    print("""
Based on the tests above:

FREE TIER (App-only):
- ✓ User lookup works
- ✓ User timeline works (limited to ~1,500 tweets/month)
- ✗ Search recent doesn't work
- ✗ Conversation search doesn't work

BASIC TIER ($100/month):
- ✓ User lookup works
- ✓ User timeline works (~10,000 tweets/month)
- ✓ Search recent works (limited queries)
- ✓ Conversation search works

PRO TIER ($5,000/month):
- ✓ Everything works with high limits

Look at your test results above to determine your tier.
    """)
    
    print()
    print("MOST IMPORTANT FOR YOU:")
    print("- Can you use search/recent? → Needed for topic discovery")
    print("- What's your user timeline rate limit? → Determines how many accounts you can scrape")
    print()

if __name__ == "__main__":
    if BEARER_TOKEN == "YOUR_BEARER_TOKEN":
        print("ERROR: You need to add your Bearer Token to this script!")
        print()
        print("How to get your Bearer Token:")
        print("1. Go to: https://developer.twitter.com/en/portal/dashboard")
        print("2. Select your app")
        print("3. Go to 'Keys and tokens' tab")
        print("4. Generate/copy your 'Bearer Token'")
        print("5. Paste it in this script where it says YOUR_BEARER_TOKEN")
    else:
        test_tier()
