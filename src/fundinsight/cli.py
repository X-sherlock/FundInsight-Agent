"""Command line interface for FundInsight Agent."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from fundinsight.report_agent import ReportAgent
from fundinsight.research_rag import ResearchIngestionService
from fundinsight.research_service import ResearchMaterialService


ALLOWED_SOURCE_TYPES = ("report", "announcement", "news", "internal_research")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="fundinsight")
    subparsers = parser.add_subparsers(dest="command", required=True)

    report_parser = subparsers.add_parser("report", help="Generate a Markdown fund report.")
    report_parser.add_argument("--input", required=True, help="Path to fund metrics JSON.")
    report_parser.add_argument("--output", required=True, help="Path to output Markdown report.")
    report_parser.add_argument(
        "--chart-output",
        help="Path to output chart_specs.json. Defaults to '<output stem>_chart_specs.json'.",
    )
    research_group = report_parser.add_mutually_exclusive_group()
    research_group.add_argument(
        "--include-research",
        dest="include_research",
        action="store_true",
        help="Use local research materials and RAG retrieval when generating the report.",
    )
    research_group.add_argument(
        "--no-research",
        dest="include_research",
        action="store_false",
        help="Generate from structured metrics only, even if research materials exist.",
    )
    report_parser.set_defaults(include_research=None)
    report_parser.add_argument(
        "--research-material-id",
        dest="research_material_ids",
        action="append",
        help="Restrict RAG retrieval to one material id. Repeat for multiple materials.",
    )
    report_parser.add_argument(
        "--force-reextract",
        action="store_true",
        help="Rebuild vector chunks for selected research materials before retrieval.",
    )
    report_parser.add_argument(
        "--fact-card-output",
        help="Optional path to write the RAG fact_card JSON used by the report prompt.",
    )
    report_parser.set_defaults(func=_run_report)

    research_parser = subparsers.add_parser("research", help="Manage local RAG research materials.")
    research_subparsers = research_parser.add_subparsers(dest="research_command", required=True)

    import_parser = research_subparsers.add_parser("import", help="Import and index one research material file.")
    import_parser.add_argument("--fund-code", required=True, help="Fund code, for example 000001.")
    import_parser.add_argument("--file", required=True, help="Path to a TXT, MD, or text-based PDF material.")
    import_parser.add_argument("--title", required=True, help="Material title shown in fact cards.")
    import_parser.add_argument("--source-type", required=True, choices=ALLOWED_SOURCE_TYPES)
    import_parser.add_argument("--source-name", help="Source name, such as issuer, media, or research desk.")
    import_parser.add_argument("--source-url", help="Original source URL when available.")
    import_parser.add_argument("--publish-date", help="Publish date in YYYY-MM-DD format when available.")
    import_parser.set_defaults(func=_run_research_import)

    list_parser = research_subparsers.add_parser("list", help="List local research materials for a fund.")
    list_parser.add_argument("--fund-code", required=True, help="Fund code, for example 000001.")
    list_parser.set_defaults(func=_run_research_list)

    return parser


def _run_report(args: argparse.Namespace) -> int:
    result = ReportAgent().generate_report(
        args.input,
        include_research=args.include_research,
        research_material_ids=args.research_material_ids,
        force_reextract=args.force_reextract,
    )
    if not result.guard_result.passed:
        for issue in result.guard_result.issues:
            print(f"guard:{issue.code}: {issue.message}", file=sys.stderr)
        return 2

    output_path = Path(args.output)
    chart_output_path = Path(args.chart_output) if args.chart_output else _default_chart_output(output_path)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    chart_output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(result.markdown, encoding="utf-8")
    chart_payload = {"charts": [chart.model_dump(mode="json") for chart in result.chart_specs]}
    chart_output_path.write_text(
        json.dumps(chart_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    if args.fact_card_output:
        fact_card_output_path = Path(args.fact_card_output)
        fact_card_output_path.parent.mkdir(parents=True, exist_ok=True)
        fact_card_output_path.write_text(
            json.dumps(result.fact_card, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"Wrote RAG fact card to {fact_card_output_path}")
    print(f"Wrote report to {output_path}")
    print(f"Wrote chart specs to {chart_output_path}")
    if result.research_processing_error:
        print(result.research_processing_error, file=sys.stderr)
    elif result.include_research is True and not result.research_used:
        print("RAG was requested, but no retrieved research chunks were available.", file=sys.stderr)
    return 0


def _run_research_import(args: argparse.Namespace) -> int:
    input_path = Path(args.file)
    if not input_path.exists():
        print(f"Research material file does not exist: {input_path}", file=sys.stderr)
        return 1

    document = ResearchIngestionService().import_file_material(
        fund_code=args.fund_code,
        title=args.title,
        file_name=input_path.name,
        content=input_path.read_bytes(),
        source_type=args.source_type,
        source_name=args.source_name,
        source_url=args.source_url,
        publish_date=args.publish_date,
    )
    print(f"Imported material {document.material_id}")
    print(f"Vector status: {document.vector_status}")
    if document.vector_error:
        print(f"Vector error: {document.vector_error}", file=sys.stderr)
    return 0


def _run_research_list(args: argparse.Namespace) -> int:
    materials = ResearchMaterialService().list_materials(args.fund_code)
    if not materials:
        print(f"No research materials found for fund {args.fund_code}.")
        return 0
    for material in materials:
        print(
            "\t".join(
                [
                    material.material_id,
                    material.source_type,
                    material.vector_status,
                    str(material.chunk_count or 0),
                    material.title,
                ]
            )
        )
    return 0


def _default_chart_output(output_path: Path) -> Path:
    return output_path.with_name(f"{output_path.stem}_chart_specs.json")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
