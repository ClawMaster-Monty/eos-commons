#!/usr/bin/env python3
"""
EOS Commons — Findings After Dark Scanner
Scans Reddit RSS feeds for biohacking/peptide/longevity discussions.
Outputs JSON for the 3-agent review pipeline.
"""
import json
import sys
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime
import re
import html
import time

CATEGORIES = {
    "Peptides & Compounds": [
        "BPC-157", "TB-500", "Ipamorelin", "CJC-1295", "retatrutide",
        "semaglutide", "tirzepatide", "NAD+", "senolytic", "peptide stack",
        "GLP-1", "GH secretagogue", "AOD-9604", "MOTS-c", "SS-31"
    ],
    "Biomarkers & Tracking": [
        "HRV", "heart rate variability", "bloodwork", "biomarker",
        "lab results", "metabolic panel", "hormone panel",
        "continuous glucose monitor", "CGM", "sleep score", "VO2 max"
    ],
    "Metabolic Health": [
        "fasting protocol", "intermittent fasting", "insulin sensitivity",
        "glucose", "keto", "carnivore", "metabolic flexibility",
        "GLP-1", "A1C", "HbA1c"
    ],
    "Recovery & Performance": [
        "cold plunge", "ice bath", "sauna", "heat exposure", "zone 2",
        "VO2 max", "mobility", "recovery protocol", "injury rehab",
        "tendon", "ligament"
    ],
    "Sleep Optimization": [
        "sleep hygiene", "circadian", "melatonin", "magnesium glycinate",
        "apigenin", "L-theanine sleep", "chronotype", "mouth tape",
        "sleep tracking", "Oura ring", "whoop sleep"
    ],
    "Cognition & Nootropics": [
        "nootropic", "racetam", "modafinil", "alpha-GPC",
        "lion's mane", "creatine cognition", "focus protocol",
        "neuroplasticity", "BDNF"
    ],
    "Hormone Optimization": [
        "TRT", "testosterone", "hormone panel", "thyroid", "cortisol",
        "DHEA", "pregnenolone", "estradiol", "SHBG", "enclomiphene"
    ],
    "Self-Experimentation": [
        "n=1", "self-experiment", "protocol log", "biohacking stack",
        "what I learned", "my results", "tracking spreadsheet"
    ]
}

SUBREDDITS = ["peptides", "biohacking", "longevity", "supplements", "Nootropics", "Biohackers"]


def fetch_rss(subreddit):
    """Fetch Reddit RSS feed for a subreddit."""
    url = f"https://www.reddit.com/r/{subreddit}/.rss?limit=25"
    req = urllib.request.Request(url, headers={"User-Agent": "EOS-Commons/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.read()
    except Exception as e:
        print(f"  r/{subreddit}: {e}", file=sys.stderr)
        return None


def parse_rss(xml_data, subreddit):
    """Parse Reddit RSS XML into post dicts."""
    posts = []
    try:
        root = ET.fromstring(xml_data)
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        for entry in root.findall(".//entry"):
            title = entry.find("title")
            title_text = title.text if title is not None and title.text else ""

            # Skip stickied/pinned posts and mod announcements
            if title_text.lower().startswith("[mod]") or title_text.lower().startswith("weekly"):
                continue

            # Get content
            content_elem = entry.find("content")
            content_text = ""
            if content_elem is not None and content_elem.text:
                # Strip HTML tags for excerpt
                content_text = re.sub(r'<[^>]+>', ' ', content_elem.text)
                content_text = re.sub(r'\s+', ' ', content_text).strip()[:500]

            # Author
            author_elem = entry.find("author/name") or entry.find("author")
            author = author_elem.text if author_elem is not None and author_elem.text else "unknown"
            author = author.replace("/u/", "")

            # Link
            link_elem = entry.find("link")
            link = link_elem.get("href") if link_elem is not None else ""

            # Published date
            updated = entry.find("updated")
            published = updated.text if updated is not None and updated.text else ""

            # Category/tags
            tags = [cat.get("term", "") for cat in entry.findall("category") if cat.get("term")]

            # Score and comments count from content
            comments_match = re.search(r'(\d+)\s+comments', content_elem.text if content_elem is not None else "")
            score_match = re.search(r'score[:\s]+(\d+)', content_elem.text if content_elem is not None else "", re.I)

            num_comments = int(comments_match.group(1)) if comments_match else 0
            score = int(score_match.group(1)) if score_match else 0

            posts.append({
                "title": html.unescape(title_text),
                "selftext": content_text[:300],
                "subreddit": subreddit,
                "url": link,
                "score": score,
                "num_comments": num_comments,
                "author": author,
                "published": published,
                "tags": tags
            })
    except Exception as e:
        print(f"  Parse error r/{subreddit}: {e}", file=sys.stderr)
    return posts


def categorize_post(post):
    """Match a post to categories."""
    text = (post["title"] + " " + post["selftext"]).lower()
    matches = []
    for cat, keywords in CATEGORIES.items():
        for kw in keywords:
            if kw.lower() in text:
                matches.append(cat)
                break
    return matches if matches else ["General Discussion"]


def quality_score(post):
    """Heuristic quality score."""
    score = 0
    comments = post.get("num_comments", 0)
    upvotes = post.get("score", 0)
    if comments > 15: score += 3
    elif comments > 5: score += 1
    if upvotes > 30: score += 3
    elif upvotes > 10: score += 1
    if len(post.get("selftext", "")) > 200: score += 2
    elif len(post.get("selftext", "")) > 80: score += 1
    # Flair/tag bonus
    tags = " ".join(post.get("tags", [])).lower()
    if any(t in tags for t in ["science", "study", "research", "guide", "protocol"]): score += 2
    return score


def main():
    # Output header
    sys.stdout.write(json.dumps({
        "scan_time": datetime.now().isoformat(),
        "scanner": "EOS Commons — Findings After Dark",
        "sources": SUBREDDITS
    }, indent=2)[:-1] + ",\n")

    all_findings = []
    seen = set()
    count = 0

    for subreddit in SUBREDDITS:
        if count > 0:
            time.sleep(3)  # Respect Reddit rate limits
        count += 1
        xml_data = fetch_rss(subreddit)
        if not xml_data:
            continue
        posts = parse_rss(xml_data, subreddit)
        for post in posts:
            key = post["url"]
            if key and key not in seen:
                seen.add(key)
                post["categories"] = categorize_post(post)
                post["quality"] = quality_score(post)
                all_findings.append(post)

    all_findings.sort(key=lambda p: p["quality"], reverse=True)
    top = all_findings[:12]

    sys.stdout.write('  "findings": [\n')
    for i, f in enumerate(top):
        comma = "," if i < len(top) - 1 else ""
        sys.stdout.write(f'    {json.dumps(f)}{comma}\n')
    sys.stdout.write("  ],\n")
    sys.stdout.write(f'  "total_scanned": {len(all_findings)},\n')
    sys.stdout.write(f'  "top_count": {len(top)}\n')
    sys.stdout.write("}\n")


if __name__ == "__main__":
    main()
