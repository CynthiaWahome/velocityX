"""
Constants based on X/Twitter's open-source algorithm.

Source: https://github.com/twitter/the-algorithm-ml
Reference: projects/home/recap/README.md

These weights are from the Heavy Ranker model that scores tweets
for the "For You" timeline. Understanding these helps us identify
high-value reply opportunities.
"""

# X Algorithm Engagement Weights (as of April 2023)
# Source: projects/home/recap/README.md in the-algorithm-ml repo
ALGORITHM_WEIGHTS = {
    "like": 0.5,  # Weakest signal
    "retweet": 1.0,  # Standard engagement
    "reply": 13.5,  # HIGH VALUE - our main target
    "profile_click": 12.0,  # User interest signal
    "video_playback_50": 0.005,  # Video engagement
    "reply_engaged_by_author": 75.0,  # JACKPOT - author responds to you
    "good_click": 11.0,  # Click into conversation + engage
    "good_click_v2": 10.0,  # Click into conversation + 2min dwell
    "negative_feedback": -74.0,  # User hides/blocks
    "report": -369.0,  # User reports
}

# Scoring Formula (from algorithm):
# score = sum_i { (weight of engagement i) * (probability of engagement i) }

# Recency Multipliers (our interpretation based on algorithm behavior)
# X's algorithm heavily favors fresh content
RECENCY_BOOSTS = {
    "under_10_min": 2.0,  # Freshest content gets 2x boost
    "under_15_min": 1.8,  # Still very fresh
    "under_30_min": 1.5,  # Good opportunity
    "under_60_min": 1.2,  # Decent
    "over_60_min": 1.0,  # Standard
}

# Conversation indicators (high reply ratio = more likely to get replies)
# If replies/likes > 0.2, it indicates an active conversation
CONVERSATION_THRESHOLD = 0.2

# Alert Emojis based on opportunity score
ALERT_EMOJIS = {
    "critical": "🔥🔥🔥",  # Score >= 80
    "high": "🚨",  # Score >= 50
    "medium": "📢",  # Score >= 30
    "low": "ℹ️",  # Below threshold
}

# Default monitored account categories
# These are high-signal accounts across different tech domains
DEFAULT_ACCOUNT_CATEGORIES = {
    "tech_visionaries": [
        "sama",  # Sam Altman (OpenAI CEO)
        "karpathy",  # Andrej Karpathy - AI research
        "ylecun",  # Yann LeCun (Meta AI)
        "gdb",  # Greg Brockman (OpenAI)
        "JeffDean",  # Jeff Dean (Google AI)
        "fchollet",  # François Chollet (Google)
        "goodfellow_i",  # Ian Goodfellow - GANs
        "timnitGebru",  # Timnit Gebru - AI ethics
        "hardmaru",  # David Ha - Creative AI
        "pooleparty",  # AI commentary
    ],
    "python_django": [
        "jacobian",  # Jacob Kaplan-Moss (Django co-creator)
        "adrianholovaty",  # Adrian Holovaty (Django co-creator)
        "freakboy3742",  # Russell Keith-Magee (Django core)
        "nnja",  # Nina Zakharenko - Python educator
        "mkennedy",  # Michael Kennedy (Talk Python)
        "dbader_org",  # Dan Bader - Python tutorials
        "raymondh",  # Raymond Hettinger - Python core dev
        "nedbat",  # Ned Batchelder - Coverage.py
        "willmcgugan",  # Will McGugan (Rich, Textual)
        "treyhunner",  # Trey Hunner - Python trainer
    ],
    "backend_devops": [
        "kelseyhightower",  # Kelsey Hightower - Kubernetes
        "jessfraz",  # Jessie Frazelle - Containers
        "b0rk",  # Julia Evans - Tech explanations
        "mipsytipsy",  # Charity Majors - Observability
        "bridgetkromhout",  # Bridget Kromhout - Ops
        "mattstratton",  # Matt Stratton - DevOps culture
        "littleidea",  # Andrew Clay Shafer - DevOps
        "DEVOPS_BORAT",  # DevOps Borat - Satire
        "swardley",  # Simon Wardley - Strategy
        "copyconstruct",  # Cindy Sridharan - Distributed systems
    ],
    "tech_memes": [
        "programming_wisdom",  # Programming quotes
        "CommitStrip",  # Developer comics
        "ThePracticalDev",  # DEV community humor
        "nixcraft",  # Linux/Unix sysadmin humor
        "devrant",  # Developer rants
        "PR0GRAMMERHUM0R",  # Programming memes
        "iamdeveloper",  # Web dev humor
        "ThePrimeagen",  # Vim enthusiast
        "t3dotgg",  # Theo - tech hot takes
        "levelsio",  # Pieter Levels - indie hacker
    ],
    "security": [
        "SwiftOnSecurity",  # Security humor + tips
        "thegrugq",  # Security researcher
        "schneierblog",  # Bruce Schneier
        "troyhunt",  # Troy Hunt (Have I Been Pwned)
        "hacks4pancakes",  # Security, infosec humor
        "malwareunicorn",  # Amanda Rousseau - Reverse engineering
        "todb",  # Tod Beardsley - Metasploit
        "taviso",  # Tavis Ormandy - Google Project Zero
        "TinkerSec",  # Security research
        "0xInfection",  # Security, writeups
    ],
}
