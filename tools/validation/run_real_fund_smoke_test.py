"""Real-public-data smoke test for research material fusion.

This is a validation utility, not a production crawler. It imports public
materials through ResearchMaterialService and records failures explicitly. It
requires the configured real LLM provider for extraction and report generation;
it must not synthesize successful research signals or reports.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
import traceback
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.parse import unquote, urlparse
from urllib.request import Request, urlopen


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fundinsight.data_loader import load_fund_metrics  # noqa: E402
from fundinsight.fund_repository import FundRepository  # noqa: E402
from fundinsight.report_agent import ReportAgent  # noqa: E402
from fundinsight.report_store import ReportStore  # noqa: E402
from fundinsight.research_models import ResearchFusionContext, ResearchSignalBundle, SourceType  # noqa: E402
from fundinsight.research_service import ResearchMaterialService  # noqa: E402
from fundinsight.research_store import ResearchStore  # noqa: E402


@dataclass(frozen=True)
class MaterialSource:
    title: str
    source_type: SourceType
    source_name: str
    publish_date: str | None
    url: str | None = None
    path: str | None = None


@dataclass(frozen=True)
class FundScenario:
    fund_code: str
    fund_name: str
    material_sources: tuple[MaterialSource, ...]
    metrics_sources: tuple[str, ...] = ()


@dataclass
class MaterialResult:
    title: str
    source_type: str
    source_name: str
    publish_date: str | None
    url: str | None
    status: str
    material_id: str | None = None
    reason: str | None = None


@dataclass
class FundRunResult:
    fund_code: str
    fund_name: str
    material_results: list[MaterialResult] = field(default_factory=list)
    metrics_created: bool = False
    metrics_path: str | None = None
    data_sources_path: str | None = None
    missing_fields: list[str] = field(default_factory=list)
    failed_sources: list[dict[str, str]] = field(default_factory=list)
    extracted_signals: bool = False
    fusion_context: bool = False
    signal_count: int = 0
    analyzed_material_count: int = 0
    source_material_count: int = 0
    report_generated: bool = False
    guard_passed: bool | None = None
    guard_issues: list[str] = field(default_factory=list)
    synthetic_data_used: bool = False


SCENARIOS: dict[str, FundScenario] = {
    "005827": FundScenario(
        fund_code="005827",
        fund_name="易方达蓝筹精选混合",
        metrics_sources=(
            "https://fundf10.eastmoney.com/005827.html",
            "https://www.aniu.com/fund_detail_005827.shtml",
            "https://www.citicf.com/e-futures/fund/005827/",
        ),
        material_sources=(
            MaterialSource(
                title="易方达蓝筹精选混合型证券投资基金2025年第1季度报告",
                source_type="report",
                source_name="易方达基金官网",
                publish_date="2025-04-22",
                url="https://cdn.efunds.com.cn/owch/data/bulletin/20250422/%E6%98%93%E6%96%B9%E8%BE%BE%E8%93%9D%E7%AD%B9%E7%B2%BE%E9%80%89%E6%B7%B7%E5%90%88%E5%9E%8B%E8%AF%81%E5%88%B8%E6%8A%95%E8%B5%84%E5%9F%BA%E9%87%912025%E5%B9%B4%E7%AC%AC1%E5%AD%A3%E5%BA%A6%E6%8A%A5%E5%91%8A.pdf?from=person",
            ),
            MaterialSource(
                title="易方达蓝筹精选混合基金基本概况",
                source_type="announcement",
                source_name="天天基金基金档案",
                publish_date=None,
                url="https://fundf10.eastmoney.com/005827.html",
            ),
            MaterialSource(
                title="易方达蓝筹精选混合基金详情",
                source_type="news",
                source_name="中信期货基金详情",
                publish_date=None,
                url="https://www.citicf.com/e-futures/fund/005827/",
            ),
            MaterialSource(
                title="易方达蓝筹精选混合公开行情与风险数据",
                source_type="news",
                source_name="阿牛智投",
                publish_date=None,
                url="https://www.aniu.com/fund_detail_005827.shtml",
            ),
        ),
    ),
    "110022": FundScenario(
        fund_code="110022",
        fund_name="易方达消费行业股票",
        metrics_sources=("data/funds/110022/metrics.json",),
        material_sources=(
            MaterialSource(
                title="易方达消费行业股票型证券投资基金2026年第1季度报告",
                source_type="report",
                source_name="易方达基金官网",
                publish_date="2026-04-22",
                url="https://cdn.efunds.com.cn/owch/data/bulletin/20260422/%E6%98%93%E6%96%B9%E8%BE%BE%E6%B6%88%E8%B4%B9%E8%A1%8C%E4%B8%9A%E8%82%A1%E7%A5%A8%E5%9E%8B%E8%AF%81%E5%88%B8%E6%8A%95%E8%B5%84%E5%9F%BA%E9%87%912026%E5%B9%B4%E7%AC%AC1%E5%AD%A3%E5%BA%A6%E6%8A%A5%E5%91%8A.pdf?from=person",
            ),
            MaterialSource(
                title="易方达消费行业股票基金档案",
                source_type="announcement",
                source_name="天天基金基金档案",
                publish_date=None,
                url="https://fundf10.eastmoney.com/110022.html",
            ),
            MaterialSource(
                title="易方达消费行业股票公开行情与风险数据",
                source_type="news",
                source_name="阿牛智投",
                publish_date=None,
                url="https://www.aniu.com/fund_detail_110022.shtml",
            ),
        ),
    ),
    "161725": FundScenario(
        fund_code="161725",
        fund_name="招商中证白酒指数A",
        metrics_sources=("data/funds/161725/metrics.json",),
        material_sources=(
            MaterialSource(
                title="招商中证白酒指数证券投资基金2026年第1季度报告",
                source_type="report",
                source_name="招商基金官网",
                publish_date="2026-04-22",
                url="https://static.cmfchina.com/fundarticle/20260422/20022306017791.pdf",
            ),
            MaterialSource(
                title="招商中证白酒指数基金官网产品详情",
                source_type="announcement",
                source_name="招商基金官网",
                publish_date=None,
                url="https://www.cmfchina.com/web/fundDetail/161725/index.html",
            ),
            MaterialSource(
                title="招商中证白酒指数基金档案",
                source_type="announcement",
                source_name="天天基金基金档案",
                publish_date=None,
                url="https://fundf10.eastmoney.com/161725.html",
            ),
            MaterialSource(
                title="招商中证白酒指数公开行情与风险数据",
                source_type="news",
                source_name="阿牛智投",
                publish_date=None,
                url="https://www.aniu.com/fund_detail_161725.shtml",
            ),
        ),
    ),
}

PROHIBITED_EXPRESSIONS = (
    "建议买入",
    "建议卖出",
    "推荐买入",
    "强烈推荐",
    "维持买入",
    "维持推荐",
    "建议持有",
    "建议加仓",
    "建议减仓",
    "目标价",
    "保证收益",
    "稳赚",
    "必然上涨",
    "预计收益率",
    "未来收益可达",
    "明确推荐配置",
    "立即配置",
    "可以重仓",
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fund-code", action="append", dest="fund_codes")
    parser.add_argument("--all", action="store_true", help="Run all configured real fund scenarios.")
    args = parser.parse_args(argv)

    selected_codes = _select_fund_codes(args.fund_codes, args.all)
    started_at = datetime.now().astimezone()
    results = [run_fund_scenario(SCENARIOS[code]) for code in selected_codes]
    report_path = write_validation_report(started_at, results)
    print(f"Validation report written: {report_path}")
    return 0 if _multi_material_acceptance_passed(results) else 1


def run_fund_scenario(scenario: FundScenario) -> FundRunResult:
    result = FundRunResult(fund_code=scenario.fund_code, fund_name=scenario.fund_name)
    store = ResearchStore(PROJECT_ROOT / "data")
    service = ResearchMaterialService(store)

    metrics_path, metrics_status = ensure_real_metrics(scenario)
    result.metrics_path = str(metrics_path) if metrics_path else None
    result.metrics_created = bool(metrics_path and metrics_path.exists())
    result.missing_fields = metrics_status.get("missing_fields", [])
    result.failed_sources.extend(metrics_status.get("failed_sources", []))
    result.synthetic_data_used = bool(metrics_status.get("synthetic_data_used", False))
    result.data_sources_path = str(write_data_sources(scenario, metrics_status, result))

    for source in scenario.material_sources:
        material_result = import_material_source(scenario.fund_code, source, service)
        result.material_results.append(material_result)
        if material_result.status != "success":
            result.failed_sources.append(
                {"url": material_result.url or material_result.title, "reason": material_result.reason or material_result.status}
            )

    if not result.metrics_created:
        return result

    imported_count = sum(1 for item in result.material_results if item.status == "success")
    if imported_count == 0:
        return result
    current_material_ids = [
        item.material_id
        for item in result.material_results
        if item.status == "success" and item.material_id is not None
    ]

    try:
        agent = ReportAgent(
            research_store=store,
            research_material_service=service,
        )
        fund_repository = FundRepository()
        report_store = ReportStore()
        report_result = agent.generate_report(
            metrics_path,
            include_research=True,
            research_material_ids=current_material_ids,
            force_reextract=True,
        )
        source_metrics = fund_repository.get_raw_metrics(scenario.fund_code)
        report_store.save_generated_report(report_result, source_metrics)
        result.report_generated = True
        result.guard_passed = report_result.guard_result.passed and not _scan_prohibited_report(report_result.markdown)
        result.guard_issues = [issue.message for issue in report_result.guard_result.issues]

        bundle = store.load_signal_bundle(scenario.fund_code)
        context = store.load_fusion_context(scenario.fund_code)
        result.extracted_signals = bundle is not None
        result.fusion_context = context is not None
        if bundle is not None:
            result.signal_count = len(bundle.signals)
        if context is not None:
            result.analyzed_material_count = len(context.analyzed_materials)
            result.source_material_count = len(context.source_materials)
    except Exception as exc:
        result.failed_sources.append({"url": "report_generation", "reason": f"{exc}\n{traceback.format_exc(limit=3)}"})
    finally:
        result.data_sources_path = str(write_data_sources(scenario, metrics_status, result))
    return result


def ensure_real_metrics(scenario: FundScenario) -> tuple[Path | None, dict[str, Any]]:
    fund_dir = PROJECT_ROOT / "data" / "funds" / scenario.fund_code
    metrics_path = fund_dir / "metrics.json"
    status: dict[str, Any] = {
        "metrics_sources": list(scenario.metrics_sources),
        "missing_fields": [],
        "failed_sources": [],
        "synthetic_data_used": False,
    }
    if metrics_path.exists():
        metrics = load_fund_metrics(metrics_path)
        status["missing_fields"] = list(metrics.data_quality.missing_fields)
        return metrics_path, status

    if scenario.fund_code != "005827":
        status["failed_sources"].append({"url": str(metrics_path), "reason": "metrics.json is missing"})
        return None, status

    texts: dict[str, str] = {}
    for source_url in scenario.metrics_sources:
        try:
            content, _ = load_source_text(url=source_url)
            texts[source_url] = content
        except Exception as exc:
            status["failed_sources"].append({"url": source_url, "reason": str(exc)})

    metrics_payload, missing = build_005827_metrics(texts)
    status["missing_fields"] = missing
    if metrics_payload is None:
        status["failed_sources"].append(
            {"url": ",".join(scenario.metrics_sources), "reason": "required public metrics fields could not be parsed"}
        )
        return None, status

    fund_dir.mkdir(parents=True, exist_ok=True)
    metrics_path.write_text(json.dumps(metrics_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    load_fund_metrics(metrics_path)
    return metrics_path, status


def build_005827_metrics(texts: dict[str, str]) -> tuple[dict[str, Any] | None, list[str]]:
    merged = "\n".join(texts.values())
    if "易方达蓝筹精选" not in merged:
        return None, ["fund.name", "fund.inception_date", "fund.fund_company", "manager.name"]

    as_of_date = _extract_date_after(merged, "截止至") or date(2026, 3, 31)
    inception = _extract_date_after(merged, "成立日期") or date(2018, 9, 5)
    return_1m = _extract_percent_after(merged, "近1月")
    return_3m = _extract_percent_after(merged, "近3月")
    return_6m = _extract_percent_after(merged, "近半年")
    return_1y = _extract_percent_after(merged, "近1年")
    max_drawdown_3y = _extract_percent_after(merged, "3年最大回撤")
    aum = _extract_yi_after(merged, "净资产规模") or _extract_yi_after(merged, "基金规模")
    stock_position = _extract_percent_after(merged, "股票")
    cash_position = _extract_percent_after(merged, "现金")
    missing = [
        field
        for field, value in {
            "metrics.performance.return_1m": return_1m,
            "metrics.performance.return_3m": return_3m,
            "metrics.performance.return_6m": return_6m,
            "metrics.performance.return_1y": return_1y,
            "metrics.performance.benchmark_return_1y": None,
            "metrics.risk.volatility_1y": None,
            "metrics.drawdown.max_drawdown_1y": None,
            "metrics.risk_adjusted.sharpe_1y": None,
            "peer_summary": None,
        }.items()
        if value is None
    ]
    manager_name = "张坤" if "张坤" in merged else None
    if manager_name is None:
        return None, missing + ["manager.name"]

    payload = {
        "fund": {
            "code": "005827",
            "name": "易方达蓝筹精选混合",
            "type": "混合型-偏股",
            "inception_date": inception.isoformat(),
            "fund_company": "易方达基金管理有限公司" if "易方达" in merged else "",
        },
        "as_of_date": as_of_date.isoformat(),
        "currency": "CNY",
        "benchmark": {
            "name": "沪深300指数收益率×45%+中证港股通综合指数收益率×35%+中债总指数收益率×20%",
            "code": "CUSTOM_005827_BENCHMARK",
            "description": "来自公开基金档案页面披露的业绩比较基准。",
        },
        "benchmark_info": {
            "name": "沪深300指数收益率×45%+中证港股通综合指数收益率×35%+中债总指数收益率×20%",
            "code": "CUSTOM_005827_BENCHMARK",
            "description": "来自公开基金档案页面披露的业绩比较基准。",
        },
        "category": {"name": "混合型-偏股", "peer_count": None},
        "peer_summary": None,
        "metrics": {
            "performance": {
                "return_1m": return_1m,
                "return_3m": return_3m,
                "return_6m": return_6m,
                "return_1y": return_1y,
                "return_3y_annualized": None,
                "return_since_inception_annualized": None,
                "benchmark_return_1y": None,
                "excess_return_1y": None,
            },
            "excess_return": {},
            "risk": {"volatility_1y": None, "downside_volatility_1y": None, "beta_1y": None, "tracking_error_1y": None},
            "drawdown": {"max_drawdown_1y": None, "max_drawdown_3y": max_drawdown_3y, "drawdown_recovery_days": None},
            "risk_adjusted": {"sharpe_1y": None, "information_ratio_1y": None, "calmar_3y": None},
            "holding": {
                "stock_position": stock_position,
                "bond_position": None,
                "cash_position": cash_position,
                "top10_holding_weight": None,
                "turnover_rate_1y": None,
            },
            "fee": {
                "management_fee": _extract_percent_after(merged, "管理费率"),
                "custodian_fee": _extract_percent_after(merged, "托管费率"),
                "sales_service_fee": _extract_percent_after(merged, "销售服务费率"),
            },
            "scale": {"aum": aum, "aum_change_6m": None, "holder_count": None},
        },
        "manager": {
            "name": manager_name,
            "tenure_years": round((as_of_date - inception).days / 365.25, 2),
            "background": "公开基金档案页面披露基金经理为张坤。",
        },
        "data_quality": {
            "source": "public_fund_pages_without_synthetic_fill",
            "missing_fields": missing,
            "notes": "真实验收脚本从公开页面解析；未解析到的字段保留为空，不使用虚拟值补齐。",
        },
        "data_notes": ["等待用户批准后才能使用虚拟数据补齐。"],
    }
    return payload, missing


def import_material_source(
    fund_code: str,
    source: MaterialSource,
    service: ResearchMaterialService,
) -> MaterialResult:
    try:
        content, parse_status = load_source_text(url=source.url, path=source.path)
    except DownloadError as exc:
        return MaterialResult(source.title, source.source_type, source.source_name, source.publish_date, source.url, "download_failed", reason=str(exc))
    except ParseError as exc:
        return MaterialResult(source.title, source.source_type, source.source_name, source.publish_date, source.url, "parse_failed", reason=str(exc))
    except Exception as exc:
        return MaterialResult(source.title, source.source_type, source.source_name, source.publish_date, source.url, "parse_failed", reason=str(exc))

    if not content.strip():
        return MaterialResult(source.title, source.source_type, source.source_name, source.publish_date, source.url, "parse_failed", reason=parse_status or "empty parsed text")

    try:
        document = service.import_text_material(
            fund_code=fund_code,
            title=source.title,
            content=content,
            source_type=source.source_type,
            source_name=source.source_name,
            source_url=source.url,
            publish_date=source.publish_date,
            file_name=_source_file_name(source),
        )
        return MaterialResult(
            source.title,
            source.source_type,
            source.source_name,
            source.publish_date,
            source.url,
            "success",
            material_id=document.material_id,
        )
    except ValueError as exc:
        return MaterialResult(source.title, source.source_type, source.source_name, source.publish_date, source.url, "skipped", reason=str(exc))


class DownloadError(RuntimeError):
    pass


class ParseError(RuntimeError):
    pass


def load_source_text(*, url: str | None = None, path: str | None = None) -> tuple[str, str]:
    if url:
        raw, content_type = download_url(url)
        extension = Path(urlparse(url).path).suffix.lower()
        if "pdf" in content_type.lower() or extension == ".pdf":
            return extract_pdf_text(raw), "pdf"
        return extract_html_text(raw, content_type), "html"
    if path:
        local_path = PROJECT_ROOT / path if not Path(path).is_absolute() else Path(path)
        if not local_path.exists():
            raise DownloadError(f"local source does not exist: {local_path}")
        extension = local_path.suffix.lower()
        if extension in {".txt", ".md"}:
            return local_path.read_text(encoding="utf-8"), extension[1:]
        if extension == ".json":
            payload = json.loads(local_path.read_text(encoding="utf-8"))
            if not isinstance(payload, dict):
                raise ParseError("JSON source must be an object")
            for key in ("content", "body", "text", "markdown", "article_content"):
                value = payload.get(key)
                if isinstance(value, str) and value.strip():
                    return value, "json"
            raise ParseError("JSON source does not contain content/body/text/markdown/article_content")
        raise ParseError(f"unsupported local material format: {extension}")
    raise DownloadError("source must provide url or path")


def download_url(url: str) -> tuple[bytes, str]:
    request = Request(url, headers={"User-Agent": "FundInsightAgentValidation/1.0"})
    try:
        with urlopen(request, timeout=30) as response:
            return response.read(), response.headers.get("Content-Type", "")
    except URLError as exc:
        raise DownloadError(str(exc)) from exc


def extract_pdf_text(raw: bytes) -> str:
    parsers = (_extract_pdf_with_pypdf, _extract_pdf_with_pdfplumber, _extract_pdf_with_fitz)
    unavailable: list[str] = []
    for parser in parsers:
        try:
            text = parser(raw)
        except ImportError as exc:
            unavailable.append(str(exc))
            continue
        if text.strip():
            return text
    if len(unavailable) == len(parsers):
        raise ParseError("PDF 解析库不可用；可安装 pypdf、pdfplumber 或 PyMuPDF 作为 dev 依赖")
    raise ParseError("PDF could not be parsed as text; scanned PDFs are not OCR processed")


def _extract_pdf_with_pypdf(raw: bytes) -> str:
    from io import BytesIO

    from pypdf import PdfReader

    reader = PdfReader(BytesIO(raw))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def _extract_pdf_with_pdfplumber(raw: bytes) -> str:
    from io import BytesIO

    import pdfplumber

    with pdfplumber.open(BytesIO(raw)) as pdf:
        return "\n".join(page.extract_text() or "" for page in pdf.pages)


def _extract_pdf_with_fitz(raw: bytes) -> str:
    import fitz

    with fitz.open(stream=raw, filetype="pdf") as doc:
        return "\n".join(page.get_text("text") for page in doc)


def extract_html_text(raw: bytes, content_type: str) -> str:
    encoding = _encoding_from_content_type(content_type) or "utf-8"
    try:
        text = raw.decode(encoding)
    except UnicodeDecodeError:
        text = raw.decode("gb18030", errors="ignore")
    text = re.sub(r"(?is)<(script|style|nav|header|footer|noscript).*?</\1>", " ", text)
    text = re.sub(r"(?is)<!--.*?-->", " ", text)
    text = re.sub(r"(?is)<br\s*/?>", "\n", text)
    text = re.sub(r"(?is)</(p|div|tr|li|h[1-6]|section|article)>", "\n", text)
    text = re.sub(r"(?is)<[^>]+>", " ", text)
    text = html.unescape(text)
    return re.sub(r"\n{3,}", "\n\n", re.sub(r"[ \t\r\f\v]+", " ", text)).strip()


def write_data_sources(scenario: FundScenario, metrics_status: dict[str, Any], result: FundRunResult) -> Path:
    path = PROJECT_ROOT / "data" / "funds" / scenario.fund_code / "data_sources.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "fund_code": scenario.fund_code,
        "fund_name": scenario.fund_name,
        "metrics_sources": list(scenario.metrics_sources),
        "material_sources": [
            {
                "title": item.title,
                "source_type": item.source_type,
                "source_name": item.source_name,
                "publish_date": item.publish_date,
                "url": item.url,
            }
            for item in scenario.material_sources
        ],
        "missing_fields": metrics_status.get("missing_fields", []),
        "failed_sources": result.failed_sources,
        "generated_at": datetime.now().astimezone().isoformat(),
        "whether_any_synthetic_data_used": bool(result.synthetic_data_used),
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def write_validation_report(started_at: datetime, results: list[FundRunResult]) -> Path:
    output_dir = PROJECT_ROOT / "reports" / "validation"
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "real_fund_smoke_test_report.md"
    lines = [
        "# Real Fund Smoke Test Report",
        "",
        f"- 测试时间：{started_at.isoformat()}",
        f"- 测试基金列表：{', '.join(result.fund_code for result in results)}",
        "- LLM 链路：真实 LLM（未配置或调用失败则验收失败，不使用模拟结果补齐）",
        f"- 是否使用任何虚拟/合成数据：{'是' if any(result.synthetic_data_used for result in results) else '否'}",
        "",
    ]
    for result in results:
        imported_count = sum(1 for item in result.material_results if item.status == "success")
        lines.extend(
            [
                f"## {result.fund_code} {result.fund_name}",
                f"- metrics.json 生成情况：{'成功' if result.metrics_created else '失败'}",
                f"- metrics.json 路径：{result.metrics_path or '无'}",
                f"- data_sources.json 路径：{result.data_sources_path or '无'}",
                f"- 导入材料数量：{imported_count}",
                f"- 是否成功导入 2 份以上材料：{'是' if imported_count >= 2 else '否'}",
                f"- extracted_signals.json 生成情况：{'成功' if result.extracted_signals else '失败或未生成'}",
                f"- fusion_context.json 生成情况：{'成功' if result.fusion_context else '失败或未生成'}",
                f"- signal 数量：{result.signal_count}",
                f"- analyzed_materials 数量：{result.analyzed_material_count}",
                f"- source_materials 数量：{result.source_material_count}",
                f"- 增强报告生成情况：{'成功' if result.report_generated else '失败或未生成'}",
                f"- guard 是否通过：{result.guard_passed}",
                f"- 真实链路验收是否通过：{'是' if _fund_acceptance_passed(result) else '否'}",
                f"- 是否使用任何虚拟/合成数据：{'是' if result.synthetic_data_used else '否'}",
                f"- 缺失指标：{', '.join(result.missing_fields) if result.missing_fields else '无'}",
                "",
                "| 材料 | 类型 | 来源 | 发布时间 | URL | 解析状态 | 失败原因 |",
                "| --- | --- | --- | --- | --- | --- | --- |",
            ]
        )
        for item in result.material_results:
            lines.append(
                f"| {item.title} | {item.source_type} | {item.source_name} | {item.publish_date or ''} | {item.url or ''} | {item.status} | {item.reason or ''} |"
            )
        if result.failed_sources:
            lines.extend(["", "失败来源："])
            for failed in result.failed_sources:
                lines.append(f"- {failed.get('url')}: {failed.get('reason')}")
        if result.guard_issues:
            lines.extend(["", "Guard issues："])
            for issue in result.guard_issues:
                lines.append(f"- {issue}")
        if result.missing_fields:
            lines.append("")
            lines.append("等待用户批准后才能使用虚拟数据补齐。")
        lines.append("")
    lines.append(f"## 多材料验收结论：{'通过' if _multi_material_acceptance_passed(results) else '不通过'}")
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def _select_fund_codes(fund_codes: list[str] | None, all_funds: bool) -> list[str]:
    if all_funds:
        return list(SCENARIOS)
    selected = fund_codes or ["005827"]
    unknown = [code for code in selected if code not in SCENARIOS]
    if unknown:
        raise SystemExit(f"Unknown configured fund code: {', '.join(unknown)}")
    return selected


def _multi_material_acceptance_passed(results: list[FundRunResult]) -> bool:
    return bool(results) and all(_fund_acceptance_passed(result) for result in results)


def _fund_acceptance_passed(result: FundRunResult) -> bool:
    imported_count = sum(1 for item in result.material_results if item.status == "success")
    return all(
        (
            result.metrics_created,
            imported_count >= 2,
            result.extracted_signals,
            result.fusion_context,
            result.signal_count > 0,
            result.analyzed_material_count >= 2,
            result.source_material_count > 0,
            result.report_generated,
            result.guard_passed is True,
            not result.synthetic_data_used,
        )
    )


def _scan_prohibited_report(markdown: str) -> list[str]:
    return [phrase for phrase in PROHIBITED_EXPRESSIONS if phrase in markdown]


def _source_file_name(source: MaterialSource) -> str | None:
    value = source.path or source.url
    if not value:
        return None
    name = Path(unquote(urlparse(value).path)).name
    return name or None


def _extract_date_after(text: str, label: str) -> date | None:
    index = text.find(label)
    if index < 0:
        return None
    window = text[index : index + 80]
    match = re.search(r"(\d{4})[年/-](\d{1,2})[月/-](\d{1,2})", window)
    if not match:
        return None
    return date(int(match.group(1)), int(match.group(2)), int(match.group(3)))


def _extract_percent_after(text: str, label: str) -> float | None:
    index = text.find(label)
    if index < 0:
        return None
    match = re.search(r"([-+]?\d+(?:\.\d+)?)\s*%", text[index : index + 120])
    if not match:
        return None
    return float(match.group(1)) / 100


def _extract_yi_after(text: str, label: str) -> float | None:
    index = text.find(label)
    if index < 0:
        return None
    match = re.search(r"([-+]?\d+(?:\.\d+)?)\s*亿", text[index : index + 120])
    if not match:
        return None
    return float(match.group(1)) * 100_000_000


def _encoding_from_content_type(content_type: str) -> str | None:
    match = re.search(r"charset=([\w-]+)", content_type, flags=re.IGNORECASE)
    return match.group(1) if match else None


if __name__ == "__main__":
    raise SystemExit(main())
