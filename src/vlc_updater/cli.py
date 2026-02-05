from __future__ import annotations

import argparse
from pathlib import Path

from .checker import DEFAULT_SOURCE_URL, format_row_json, run_check
from .db import connect, fetch_history, init_db, insert_check

DEFAULT_DB = Path("data/vlc_updates.sqlite3")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="vlc-updater",
        description="Sjekk om VLC har ny versjon og lagre resultat i SQLite.",
    )
    parser.add_argument("--db", default=str(DEFAULT_DB), help="Sti til SQLite databasefil")

    subparsers = parser.add_subparsers(dest="command", required=True)

    check_parser = subparsers.add_parser("check", help="Kjør en ny sjekk")
    check_parser.add_argument(
        "--installed-version",
        help="Lokalt installert VLC-versjon (f.eks. 3.0.20)",
    )
    check_parser.add_argument(
        "--source-url",
        default=DEFAULT_SOURCE_URL,
        help="Kilde-URL som inneholder siste VLC-versjon",
    )

    history_parser = subparsers.add_parser("history", help="Vis historikk")
    history_parser.add_argument("--limit", type=int, default=20, help="Antall rader å vise")

    subparsers.add_parser("init-db", help="Opprett tabeller i databasen")
    return parser


def cmd_init_db(db_path: str) -> int:
    conn = connect(db_path)
    try:
        init_db(conn)
    finally:
        conn.close()
    print(f"Database klar: {db_path}")
    return 0


def cmd_check(db_path: str, installed_version: str | None, source_url: str) -> int:
    conn = connect(db_path)
    try:
        init_db(conn)
        result = run_check(installed_version=installed_version, source_url=source_url)
        row_id = insert_check(conn, result.as_dict())
    finally:
        conn.close()

    payload = result.as_dict() | {"id": row_id}
    print(format_row_json(payload))
    return 0 if result.status == "ok" else 1


def cmd_history(db_path: str, limit: int) -> int:
    conn = connect(db_path)
    try:
        init_db(conn)
        rows = fetch_history(conn, limit=limit)
    finally:
        conn.close()

    for row in rows:
        print(format_row_json(dict(row)))
    if not rows:
        print("Ingen historikk enda.")
    return 0


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "init-db":
        return cmd_init_db(args.db)
    if args.command == "check":
        return cmd_check(args.db, args.installed_version, args.source_url)
    if args.command == "history":
        return cmd_history(args.db, args.limit)

    parser.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
