from __future__ import annotations

from pathlib import Path
from typing import Any, cast

import pytest

from framework.reporting.report_server.context import ReportServerContext
from framework.reporting.report_server.services import pdf as pdf_service

pytestmark = [pytest.mark.aso]


class _DummyBaselineStore:
    def resolve_baseline(self, *_args):
        return None


def test_configure_pdf_fonts_prefers_unicode_fonts_when_available() -> None:
    if not pdf_service._REPORTLAB_AVAILABLE:
        pytest.skip("reportlab is not available")

    regular, bold = pdf_service._configure_pdf_fonts()
    has_dejavu = (
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf").is_file()
        and Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf").is_file()
    )

    if has_dejavu:
        assert regular == "VRTDejaVuSans"
        assert bold == "VRTDejaVuSansBold"
    else:
        assert regular == "Helvetica"
        assert bold == "Helvetica-Bold"


def test_generate_bug_pdf_handles_polish_characters(tmp_path: Path) -> None:
    if not pdf_service._REPORTLAB_AVAILABLE:
        pytest.skip("reportlab is not available")

    ui_dist = tmp_path / "ui"
    ui_dist.mkdir(parents=True)
    report_dir = tmp_path / "artifacts" / "run-1" / "visual"
    report_dir.mkdir(parents=True)

    context = ReportServerContext(
        repo_root=tmp_path,
        ui_dist_dir=ui_dist,
        baseline_store=cast(Any, _DummyBaselineStore()),
        run_dirs={"run-1": report_dir},
    )

    row = {
        "scenario_id": "sc-1",
        "suite_id": "suite/pl",
        "viewport": "fhd",
        "browser": "chromium",
        "test_metadata": {
            "run": {"tester": "Łukasz", "run_note": "Notatka: Łódź"},
            "scenario": {
                "name": "Zażółć gęślą jaźń",
                "suite_id": "suite/pl",
                "target_url": "/produkt/łódź",
                "viewport": "fhd",
                "browser": "chromium",
                "capture": {"selector": "#produkt"},
            },
        },
    }
    case_state = {
        "bug": {"note": "Błąd: Łódź Bałuty, zażółć gęślą jaźń"},
        "aso": {"note": "Notatka ASO: żółw"},
    }

    output, pages = pdf_service._generate_bug_pdf(
        context=context,
        run_id="run-1",
        report_dir=report_dir,
        bug_rows=[(row, case_state)],
    )

    assert pages == 1
    assert output
    assert Path(output).is_file()
    assert Path(output).stat().st_size > 0
