"""File-based storage for unstructured fund research materials."""

from __future__ import annotations

import json
import re
from pathlib import Path

from fundinsight.research_models import (
    ResearchDocument,
    ResearchFusionContext,
    ResearchSignalBundle,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATA_ROOT = PROJECT_ROOT / "data"
_SAFE_SEGMENT_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")


class ResearchStore:
    def __init__(self, data_root: str | Path = DEFAULT_DATA_ROOT) -> None:
        self.data_root = Path(data_root)

    def save_material(self, fund_code: str, document: ResearchDocument, content: str) -> None:
        if document.fund_code != fund_code:
            raise ValueError("Document fund_code does not match storage fund_code.")
        material_id = self._safe_material_id(document.material_id)
        materials_dir = self.materials_dir(fund_code)
        materials_dir.mkdir(parents=True, exist_ok=True)

        self._material_metadata_path(fund_code, material_id).write_text(
            self._dump_json(document),
            encoding="utf-8",
        )
        self._material_content_path(fund_code, material_id).write_text(content, encoding="utf-8")

    def list_materials(self, fund_code: str) -> list[ResearchDocument]:
        materials_dir = self.materials_dir(fund_code)
        if not materials_dir.exists():
            return []

        documents: list[ResearchDocument] = []
        for path in sorted(materials_dir.glob("*.json")):
            payload = json.loads(path.read_text(encoding="utf-8"))
            documents.append(ResearchDocument.model_validate(payload))
        return documents

    def read_material_content(self, fund_code: str, material_id: str) -> str | None:
        safe_material_id = self._safe_material_id(material_id)
        path = self._material_content_path(fund_code, safe_material_id)
        if not path.exists():
            return None
        return path.read_text(encoding="utf-8")

    def delete_material(self, fund_code: str, material_id: str) -> bool:
        safe_material_id = self._safe_material_id(material_id)
        deleted = False
        for path in (
            self._material_metadata_path(fund_code, safe_material_id),
            self._material_content_path(fund_code, safe_material_id),
        ):
            if path.exists():
                path.unlink()
                deleted = True
        return deleted

    def save_signal_bundle(self, fund_code: str, bundle: ResearchSignalBundle) -> None:
        if bundle.fund_code != fund_code:
            raise ValueError("Signal bundle fund_code does not match storage fund_code.")
        research_dir = self.research_dir(fund_code)
        research_dir.mkdir(parents=True, exist_ok=True)
        self._signal_bundle_path(fund_code).write_text(self._dump_json(bundle), encoding="utf-8")

    def load_signal_bundle(self, fund_code: str) -> ResearchSignalBundle | None:
        path = self._signal_bundle_path(fund_code)
        if not path.exists():
            return None
        return ResearchSignalBundle.model_validate(json.loads(path.read_text(encoding="utf-8")))

    def save_fusion_context(self, fund_code: str, context: ResearchFusionContext) -> None:
        if context.fund_code != fund_code:
            raise ValueError("Fusion context fund_code does not match storage fund_code.")
        research_dir = self.research_dir(fund_code)
        research_dir.mkdir(parents=True, exist_ok=True)
        self._fusion_context_path(fund_code).write_text(self._dump_json(context), encoding="utf-8")

    def load_fusion_context(self, fund_code: str) -> ResearchFusionContext | None:
        path = self._fusion_context_path(fund_code)
        if not path.exists():
            return None
        return ResearchFusionContext.model_validate(json.loads(path.read_text(encoding="utf-8")))

    def research_dir(self, fund_code: str) -> Path:
        safe_fund_code = self._safe_segment(fund_code, "fund_code")
        return self.data_root / "funds" / safe_fund_code / "research"

    def materials_dir(self, fund_code: str) -> Path:
        return self.research_dir(fund_code) / "materials"

    def _material_metadata_path(self, fund_code: str, material_id: str) -> Path:
        return self.materials_dir(fund_code) / f"{material_id}.json"

    def _material_content_path(self, fund_code: str, material_id: str) -> Path:
        return self.materials_dir(fund_code) / f"{material_id}.txt"

    def _signal_bundle_path(self, fund_code: str) -> Path:
        return self.research_dir(fund_code) / "extracted_signals.json"

    def _fusion_context_path(self, fund_code: str) -> Path:
        return self.research_dir(fund_code) / "fusion_context.json"

    def _safe_material_id(self, material_id: str) -> str:
        return self._safe_segment(material_id, "material_id")

    def _safe_segment(self, value: str, label: str) -> str:
        candidate = value.strip()
        if not _SAFE_SEGMENT_RE.fullmatch(candidate):
            raise ValueError(f"Invalid {label}: path traversal or unsafe characters are not allowed.")
        return candidate

    def _dump_json(self, model: ResearchDocument | ResearchSignalBundle | ResearchFusionContext) -> str:
        return json.dumps(model.model_dump(mode="json"), ensure_ascii=False, indent=2)
