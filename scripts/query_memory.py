#!/usr/bin/env python3
"""Simple script to query EchoGarden memory directly via API."""

import sys
import httpx
import json

API_BASE = "http://localhost:8000"

def search_memory(query: str, limit: int = 10):
    """Search through conversation history."""
    try:
        response = httpx.get(
            f"{API_BASE}/search",
            params={"q": query, "k": limit},
            timeout=30.0
        )
        response.raise_for_status()
        return response.json()
    except httpx.HTTPError as e:
        return {"error": f"API Error: {str(e)}"}

def get_timeline(conv_id: str):
    """Get full conversation timeline."""
    try:
        response = httpx.get(
            f"{API_BASE}/conversation/{conv_id}/timeline",
            timeout=30.0
        )
        response.raise_for_status()
        return response.json()
    except httpx.HTTPError as e:
        return {"error": f"API Error: {str(e)}"}

def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  Search: python3 query_memory.py search 'your query' [limit]")
        print("  Timeline: python3 query_memory.py timeline <conv_id>")
        print("")
        print("Examples:")
        print("  python3 query_memory.py search 'ADHD' 5")
        print("  python3 query_memory.py timeline 67b88f7b-2100-8004-8e80-8b445d2c93bc")
        sys.exit(1)

    command = sys.argv[1].lower()

    if command == "search":
        if len(sys.argv) < 3:
            print("Error: Search query required")
            sys.exit(1)

        query = sys.argv[2]
        limit = int(sys.argv[3]) if len(sys.argv) > 3 else 10

        print(f"🔍 Searching for: {query} (limit: {limit})\n")
        results = search_memory(query, limit)

        if "error" in results:
            print(f"❌ {results['error']}")
            sys.exit(1)

        hits = results.get("results", [])
        if not hits:
            print("No results found.")
            sys.exit(0)

        print(f"Found {len(hits)} results:\n")
        for i, hit in enumerate(hits, 1):
            print(f"{i}. [{hit['role']}] {hit['ts']}")
            print(f"   Conv: {hit['conv_id']}")
            print(f"   Score: {hit['score']:.2f}")
            print(f"   {hit['text'][:200]}...")
            print()

    elif command == "timeline":
        if len(sys.argv) < 3:
            print("Error: Conversation ID required")
            sys.exit(1)

        conv_id = sys.argv[2]

        print(f"📜 Getting timeline for: {conv_id}\n")
        result = get_timeline(conv_id)

        if "error" in result:
            print(f"❌ {result['error']}")
            sys.exit(1)

        messages = result.get("messages", [])
        if not messages:
            print("No messages found.")
            sys.exit(0)

        print(f"Conversation ({len(messages)} messages):\n")
        for msg in messages:
            print(f"[{msg['role']}] {msg['ts']}")
            print(f"{msg['text']}")
            print("---")

    else:
        print(f"Unknown command: {command}")
        print("Use 'search' or 'timeline'")
        sys.exit(1)

if __name__ == "__main__":
    main()
