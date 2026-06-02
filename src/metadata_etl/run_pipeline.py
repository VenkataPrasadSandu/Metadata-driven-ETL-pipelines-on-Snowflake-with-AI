from __future__ import annotations

import argparse
import json

from rich.console import Console

from metadata_etl.connection import connect

console = Console()


def main() -> None:
    parser = argparse.ArgumentParser(description="Run metadata-driven ETL wrapper procedure")
    parser.add_argument("--days-back", type=int, default=7)
    parser.add_argument("--max-retries", type=int, default=3)
    args = parser.parse_args()

    with connect() as conn:
        cur = conn.cursor()
        try:
            cur.execute("CALL CONTROL.SP_PROCESS_CHANGED_DATASETS(%s, %s)", (args.days_back, args.max_retries))
            row = cur.fetchone()
            result = row[0] if row else None
            console.print("[bold green]Pipeline call completed[/bold green]")
            if isinstance(result, str):
                try:
                    console.print_json(json.dumps(json.loads(result)))
                except Exception:
                    console.print(result)
            else:
                console.print(result)
        finally:
            cur.close()


if __name__ == "__main__":
    main()
