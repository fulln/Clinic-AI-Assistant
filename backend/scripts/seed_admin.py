#!/usr/bin/env python3
"""
seed_admin.py --username <> --password <> --display-name <>

Creates an admin user directly via SQLAlchemy (bypasses the API).
Idempotent: skips creation if the username already exists.

Requires the same environment variables as the main application:
    POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB
    POSTGRES_HOST  (default: localhost)
    POSTGRES_PORT  (default: 5432)
"""

import argparse
import asyncio
import sys


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Seed an admin user into the database")
    parser.add_argument("--username", required=True, help="Admin username")
    parser.add_argument("--password", required=True, help="Admin password (plain text)")
    parser.add_argument("--display-name", required=True, dest="display_name", help="Display name")
    return parser.parse_args()


async def create_admin(username: str, password: str, display_name: str) -> None:
    from sqlalchemy import select

    from src.interfaces.api.dependencies import AsyncSessionLocal
    from src.infrastructure.db.models import UserModel, UserRole
    from src.domains.auth.value_objects import Password

    password_hash = Password.hash(password)

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(UserModel).where(UserModel.username == username)
        )
        existing = result.scalar_one_or_none()

        if existing is not None:
            print(f"User '{username}' already exists — skipping.")
            return

        user = UserModel(
            username=username,
            password_hash=password_hash,
            role=UserRole.ADMIN,
            display_name=display_name,
            is_active=True,
        )
        session.add(user)
        await session.commit()
        print(f"Admin user '{username}' created successfully (id={user.id}).")


def main() -> None:
    args = parse_args()
    asyncio.run(create_admin(args.username, args.password, args.display_name))


if __name__ == "__main__":
    main()
