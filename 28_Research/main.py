"""
CLI interface for ArcanisResearch database.
"""

import argparse
import json
from pathlib import Path

from database.init import ResearchDatabase

def cmd_init(args):
    """Initialize the database"""
    db = ResearchDatabase()
    db.create_tables()
    print("Database initialized successfully")


def cmd_add(args):
    """Add a new research entry"""
    if not args.file:
        print("Error: --file argument is required")
        return

    with open(args.file, 'r') as f:
        content = f.read()

    db = ResearchDatabase()

    metadata = {}
    if args.type == 'paper':
        metadata['url'] = args.url
    elif args.type == 'comparison':
        metadata['entities'] = args.entities

    entry_id = db.insert_entry(
        title=args.title,
        entry_type=args.type,
        content=content,
        research_area=args.area,
        metadata=metadata
    )

    db.add_tags(entry_id, args.tags.split(',') if args.tags else [])

    print(f"Added entry with ID {entry_id}")


def cmd_get(args):
    """Get a research entry by ID"""
    db = ResearchDatabase()
    entry = db.get_entry(args.id)

    if entry:
        print(f"Title: {entry['title']}")
        print(f"Type: {entry['type']}")
        print(f"Area: {entry['research_area']}")
        print(f"Content:\n{entry['content']}")
    else:
        print(f"Entry with ID {args.id} not found")


def cmd_search(args):
    """Search research entries"""
    db = ResearchDatabase()
    entries = db.search_entries(args.query, args.area)

    for entry in entries:
        print(f"ID: {entry['id']}, Title: {entry['title']}, Type: {entry['type']}")


def main():
    parser = argparse.ArgumentParser(description="ArcanisResearch CLI")

    subparsers = parser.add_subparsers(dest='command', help='Command to execute')

    parser_init = subparsers.add_parser('init', help='Initialize database')
    parser_init.set_defaults(func=cmd_init)

    parser_add = subparsers.add_parser('add', help='Add research entry')
    parser_add.add_argument('--title', required=True, help='Entry title')
    parser_add.add_argument('--file', required=True, help='File containing entry content')
    parser_add.add_argument('--type', choices=['note', 'paper', 'summary', 'comparison'], help='Entry type')
    parser_add.add_argument('--area', required=True, choices=['operating-systems', 'ai', 'robotics', 'programming-languages', 'hardware', 'security', 'mathematics'], help='Research area')
    parser_add.add_argument('--tags', help='Comma-separated tags')
    parser_add.add_argument('--url', help='Paper URL (for paper entries)')
    parser_add.add_argument('--entities', help='JSON list of comparison entities (for comparison entries)')
    parser_add.set_defaults(func=cmd_add)

    parser_get = subparsers.add_parser('get', help='Get research entry by ID')
    parser_get.add_argument('--id', type=int, required=True, help='Entry ID')
    parser_get.set_defaults(func=cmd_get)

    parser_search = subparsers.add_parser('search', help='Search research entries')
    parser_search.add_argument('--query', required=True, help='Search query')
    parser_search.add_argument('--area', help='Research area filter')
    parser_search.set_defaults(func=cmd_search)

    args = parser.parse_args()

    if not hasattr(args, 'func'):
        parser.print_help()
        return

    args.func(args)


if __name__ == '__main__':
    main()
