from __future__ import annotations

import argparse
from pathlib import Path

from rich.console import Console

from metadata_etl.connection import connect

console = Console()


def split_sql(sql_text: str) -> list[str]:
    # Good enough for this repo because Snowflake procedure bodies use $$ blocks.
    statements: list[str] = []
    buf: list[str] = []
    in_dollar_block = False
    for line in sql_text.splitlines():
        if "$$" in line:
            in_dollar_block = not in_dollar_block
        buf.append(line)
        if line.strip().endswith(";") and not in_dollar_block:
            statements.append("\n".join(buf).strip().rstrip(";"))
            buf = []
    tail = "\n".join(buf).strip()
    if tail:
        statements.append(tail.rstrip(";"))
    return [s for s in statements if s]


def main() -> None:
    parser = argparse.ArgumentParser(description="Deploy SQL files to Snowflake")
    parser.add_argument("--sql-dir", default="sql")
    args = parser.parse_args()

    sql_files = sorted(Path(args.sql_dir).glob("*.sql"))
    if not sql_files:
        raise RuntimeError(f"No SQL files found in {args.sql_dir}")

    with connect() as conn:
        cur = conn.cursor()
        try:
            for path in sql_files:
                text = path.read_text(encoding="utf-8")
                statements = split_sql(text)
                console.print(f"[bold blue]Executing {path.name}[/bold blue] ({len(statements)} statements)")
                for stmt in statements:
                    cur.execute(stmt)
            console.print("[bold green]Deployment complete[/bold green]")
        finally:
            cur.close()


if __name__ == "__main__":
    main()
