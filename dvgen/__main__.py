"""Command-line entry point for the Data Vault DDL generator."""

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

from .generator import ContractError, generate_ddl


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate BigQuery Data Vault 2.0 DDL from a JSON contract."
    )
    parser.add_argument("contract", type=Path, help="Path to the JSON contract.")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("generated"),
        help="Output directory (default: generated).",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        count = generate_ddl(args.contract, args.output)
    except (ContractError, OSError, json.JSONDecodeError) as exc:
        print(f"Generation failed: {exc}", file=sys.stderr)
        return 1
    print(f"Generated BigQuery DDL for {count} Data Vault tables in {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
