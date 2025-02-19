#!/usr/bin/env python3
"""
rss_cli.py

A CLI tool to perform CRUD operations on your RSS feed configurations stored in feeds.db.

Commands:
    add     : Add a new feed.
              Example: python rss_cli.py add --name "Example Feed" --url "https://example.com/rss"

    edit    : Edit an existing feed. You can update the feed name and/or URL.
              Example: python rss_cli.py edit --name "Example Feed" --new-name "New Example" --url "https://example.com/newrss"

    update  : Update only the URL of an existing feed.
              Example: python rss_cli.py update --name "Example Feed" --url "https://example.com/updatedrss"

    delete  : Delete an existing feed.
              Example: python rss_cli.py delete --name "Example Feed"

    list    : List all feeds.
              Example: python rss_cli.py list

Optional:
    --db   : Specify a custom feeds database file (default: feeds.db).
"""

import argparse
import shelve
import sys


def add_feed(db_path, name, url):
    with shelve.open(db_path, writeback=True) as db:
        if name in db:
            print(f"Error: A feed with the name '{name}' already exists.")
            sys.exit(1)
        db[name] = url
        print(f"Feed '{name}' added with URL: {url}")


def edit_feed(db_path, name, new_name, url):
    with shelve.open(db_path, writeback=True) as db:
        if name not in db:
            print(f"Error: No feed found with the name '{name}'.")
            sys.exit(1)
        current_url = db[name]
        # Determine the final name and URL
        final_name = new_name if new_name else name
        final_url = url if url else current_url

        # If renaming, ensure the new name doesn't already exist.
        if new_name and new_name != name and new_name in db:
            print(f"Error: A feed with the name '{new_name}' already exists.")
            sys.exit(1)

        # If the name is changing, remove the old key.
        if new_name and new_name != name:
            del db[name]
        db[final_name] = final_url
        print(f"Feed updated: Name='{final_name}', URL='{final_url}'")


def update_feed(db_path, name, url):
    with shelve.open(db_path, writeback=True) as db:
        if name not in db:
            print(f"Error: No feed found with the name '{name}'.")
            sys.exit(1)
        db[name] = url
        print(f"Feed '{name}' updated with new URL: {url}")


def delete_feed(db_path, name):
    with shelve.open(db_path, writeback=True) as db:
        if name not in db:
            print(f"Error: No feed found with the name '{name}'.")
            sys.exit(1)
        del db[name]
        print(f"Feed '{name}' deleted.")


def list_feeds(db_path):
    with shelve.open(db_path) as db:
        if not db:
            print("No feeds found.")
            return
        print("Current feeds:")
        for name in sorted(db.keys()):
            print(f" - {name}: {db[name]}")


def main():
    parser = argparse.ArgumentParser(
        description="Manage RSS feed configurations stored in feeds.db"
    )
    parser.add_argument(
        "--db",
        default="feeds.db",
        help="Path to the feeds database file (default: feeds.db)",
    )

    subparsers = parser.add_subparsers(
        dest="command", required=True, help="CRUD command to execute"
    )

    # Add command
    parser_add = subparsers.add_parser("add", help="Add a new feed")
    parser_add.add_argument("--name", required=True, help="Name of the feed")
    parser_add.add_argument("--url", required=True, help="URL of the RSS feed")

    # Edit command (update name and/or URL)
    parser_edit = subparsers.add_parser("edit", help="Edit an existing feed")
    parser_edit.add_argument(
        "--name", required=True, help="Current name of the feed to edit"
    )
    parser_edit.add_argument("--new-name", help="New name for the feed")
    parser_edit.add_argument("--url", help="New URL for the feed")

    # Update command (update URL only)
    parser_update = subparsers.add_parser(
        "update", help="Update the URL of an existing feed"
    )
    parser_update.add_argument(
        "--name", required=True, help="Name of the feed to update"
    )
    parser_update.add_argument("--url", required=True, help="New URL for the feed")

    # Delete command
    parser_delete = subparsers.add_parser("delete", help="Delete an existing feed")
    parser_delete.add_argument(
        "--name", required=True, help="Name of the feed to delete"
    )

    # List command (read)
    parser_list = subparsers.add_parser("list", help="List all feeds")

    args = parser.parse_args()

    if args.command == "add":
        add_feed(args.db, args.name, args.url)
    elif args.command == "edit":
        if not args.new_name and not args.url:
            print(
                "Error: Provide at least one option to update (--new-name and/or --url)."
            )
            sys.exit(1)
        edit_feed(args.db, args.name, args.new_name, args.url)
    elif args.command == "update":
        update_feed(args.db, args.name, args.url)
    elif args.command == "delete":
        delete_feed(args.db, args.name)
    elif args.command == "list":
        list_feeds(args.db)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
