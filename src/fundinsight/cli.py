"""Command line interface for FundInsight Agent."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from fundinsight.report_agent import ReportAgent


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="fundinsight")
    subparsers = parser.add_subparsers(dest="command", required=True)

    report_parser = subparsers.add_parser("report", help="Generate a Markdown fund report.")
    report_parser.add_argument("--input", required=True, help="Path to fund metrics JSON.")
    report_parser.add_argument("--output", required=True, help="Path to output Markdown report.")
    report_parser.set_defaults(func=_run_report)

    return parser


def _run_report(args: argparse.Namespace) -> int:
    result = ReportAgent().generate_report(args.input)
    if not result.guard_result.passed:
        for issue in result.guard_result.issues:
            print(f"guard:{issue.code}: {issue.message}", file=sys.stderr)
        return 2

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(result.markdown, encoding="utf-8")
    print(f"Wrote report to {output_path}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
