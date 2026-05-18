#!/usr/bin/env python3
"""
seed_agents.py --config <path>

Reads a JSON file of agent configs, submits them via POST /api/v1/agents/batch-publish,
then polls GET /api/v1/agents/batches/{id} every 2s until the batch reaches a terminal
status (completed | partial_failure). Prints a summary at the end.

Environment variables required:
    ADMIN_USERNAME   — admin account username
    ADMIN_PASSWORD   — admin account password
    API_BASE_URL     — base URL of the API (default: http://localhost:8000)
"""

import argparse
import json
import os
import sys
import time

import requests


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Seed agents via batch-publish API")
    parser.add_argument("--config", required=True, help="Path to JSON file with agent configs")
    return parser.parse_args()


def login(base_url: str, username: str, password: str) -> str:
    resp = requests.post(
        f"{base_url}/api/v1/auth/login",
        json={"username": username, "password": password},
        timeout=10,
    )
    if resp.status_code != 200:
        print(f"Login failed ({resp.status_code}): {resp.text}", file=sys.stderr)
        sys.exit(1)
    token = resp.json()["access_token"]
    print(f"Logged in as {username}")
    return token


def submit_batch(base_url: str, token: str, agents: list[dict]) -> str:
    resp = requests.post(
        f"{base_url}/api/v1/agents/batch-publish",
        json={"agents": agents},
        headers={"Authorization": f"Bearer {token}"},
        timeout=30,
    )
    if resp.status_code not in (200, 202):
        print(f"Batch submit failed ({resp.status_code}): {resp.text}", file=sys.stderr)
        sys.exit(1)
    data = resp.json()
    batch_id = data["batch_id"]
    print(f"Batch submitted: {batch_id} ({data['total_count']} agents)")
    return batch_id


def poll_batch(base_url: str, token: str, batch_id: str) -> dict:
    terminal = {"completed", "partial_failure"}
    while True:
        resp = requests.get(
            f"{base_url}/api/v1/agents/batches/{batch_id}",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10,
        )
        if resp.status_code != 200:
            print(f"Poll failed ({resp.status_code}): {resp.text}", file=sys.stderr)
            sys.exit(1)
        data = resp.json()
        current_status = data["status"]
        print(f"  Status: {current_status} — success={data['success_count']} failure={data['failure_count']}")
        if current_status in terminal:
            return data
        time.sleep(2)


def print_summary(data: dict) -> None:
    print("\n=== Batch Publish Summary ===")
    print(f"Batch ID   : {data['batch_id']}")
    print(f"Status     : {data['status']}")
    print(f"Total      : {data['total_count']}")
    print(f"Succeeded  : {data['success_count']}")
    print(f"Failed     : {data['failure_count']}")

    failures = [item for item in data.get("items", []) if item["status"] == "failed"]
    if failures:
        print("\nFailed items:")
        for item in failures:
            print(f"  index={item['index']}  error={item.get('error', 'unknown')}")


def main() -> None:
    args = parse_args()

    with open(args.config, "r", encoding="utf-8") as fh:
        agents = json.load(fh)

    if not isinstance(agents, list):
        print("Config file must contain a JSON array of agent objects", file=sys.stderr)
        sys.exit(1)

    base_url = os.environ.get("API_BASE_URL", "http://localhost:8000").rstrip("/")
    username = os.environ.get("ADMIN_USERNAME", "")
    password = os.environ.get("ADMIN_PASSWORD", "")

    if not username or not password:
        print("ADMIN_USERNAME and ADMIN_PASSWORD environment variables are required", file=sys.stderr)
        sys.exit(1)

    token = login(base_url, username, password)
    batch_id = submit_batch(base_url, token, agents)
    result = poll_batch(base_url, token, batch_id)
    print_summary(result)

    if result["status"] == "partial_failure":
        sys.exit(2)


if __name__ == "__main__":
    main()
