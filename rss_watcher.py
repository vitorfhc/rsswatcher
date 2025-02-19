#!/usr/bin/env python3
"""
rss_watcher.py

Usage:
    python rss_watcher.py --discord-webhook <WEBHOOK_URL>
                         [--feed-config <feeds_shelf.db>]
                         [--cache <feed_cache.db>]

This script reads feed configurations (name and URL) from a shelve database,
checks each RSS feed for new entries, and sends a Discord webhook notification
with a summary of all new entries found. Seen entries are tracked in a separate
shelve database so that only new entries trigger notifications.

Before running, ensure you have installed required packages:
    pip install feedparser requests
"""

import argparse
import feedparser
import shelve
import sys
import os
import requests


def get_entry_id(entry):
    """
    Return a unique identifier for a feed entry.
    Prefer the 'id' field; if missing, use the 'link'.
    """
    return entry.get("id", entry.get("link", None))


def process_feed(feed_name, feed_url, cache):
    """
    Process a single feed given its name and URL.
    Returns a list of new entry summaries (each a dict with 'feed', 'title', and 'link').
    Updates the cache of seen entry IDs for the feed.
    """
    print(f"Processing feed: {feed_name} ({feed_url})")
    feed = feedparser.parse(feed_url)
    if feed.bozo:
        print(f"  [Error] Could not parse feed: {feed_url}")
        return []

    # Get previously seen entry IDs; if none, initialize with an empty set.
    seen_entries = cache.get(feed_url, set())
    new_entries = []

    for entry in feed.entries:
        entry_id = get_entry_id(entry)
        if entry_id is None:
            continue  # Skip entries without an identifier
        if entry_id not in seen_entries:
            title = entry.get("title", "No title")
            link = entry.get("link", "No link")
            new_entries.append({"feed": feed_name, "title": title, "link": link})
            seen_entries.add(entry_id)

    # Update the persistent store with the new set of seen IDs.
    cache[feed_url] = seen_entries

    if new_entries:
        print(
            f"  Found {len(new_entries)} new entr{'y' if len(new_entries)==1 else 'ies'}."
        )
    else:
        print("  No new entries.")

    return new_entries


def send_discord_notification(new_entries, webhook_url):
    """
    Send a Discord webhook notification with a summary of all new entries.
    The message will list each new entry with its feed name, title, and link.
    """
    if not new_entries:
        return

    # Build a message summary.
    lines = ["**New RSS Feed Entries Found:**"]
    for entry in new_entries:
        # Each entry is a dict containing feed, title, and link.
        line = f"**{entry['feed']}**: [{entry['title']}]({entry['link']})"
        lines.append(line)
    message = "\n".join(lines)

    payload = {"content": message[0:2000]}  # Discord message limit is 2000 characters

    try:
        response = requests.post(webhook_url, json=payload)
        if response.status_code in (200, 204):
            print("Discord notification sent successfully.")
        else:
            print(
                f"Error sending Discord notification: HTTP {response.status_code} - {response.text}"
            )
    except Exception as e:
        print(f"Exception while sending Discord notification: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="RSS Feed Checker with Discord Notifications"
    )
    parser.add_argument(
        "--discord-webhook",
        required=True,
        help="Discord webhook URL to send notifications",
    )
    parser.add_argument(
        "--feed-config",
        default="feeds.db",
        help="Path to the shelve file containing feed configurations",
    )
    parser.add_argument(
        "--cache",
        default="feed_cache.db",
        help="Path to shelve cache file for storing seen entry IDs",
    )
    args = parser.parse_args()

    # Ensure the feed configuration shelf exists.
    if not os.path.exists(args.feed_config):
        print(f"[Error] Feed configuration shelf '{args.feed_config}' does not exist.")
        print("Please create it and add feed entries (name and URL) first.")
        sys.exit(1)

    new_entries_all = []

    # Open the feed configuration shelf.
    with shelve.open(args.feed_config) as feed_config:
        if not feed_config:
            print(f"[Error] No feed configurations found in '{args.feed_config}'.")
            sys.exit(1)

        # Open the cache shelf for seen entries.
        with shelve.open(args.cache) as cache:
            for feed_name in feed_config:
                feed_url = feed_config[feed_name]
                new_entries = process_feed(feed_name, feed_url, cache)
                new_entries_all.extend(new_entries)

    # Send a Discord notification if any new entries were found.
    if new_entries_all:
        send_discord_notification(new_entries_all, args.discord_webhook)
    else:
        print("No new entries found across all feeds.")


if __name__ == "__main__":
    main()
