from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass

from qa.e2e.netcorner.nuxt.pl.app.data.orders_smoke_data import (
    ORDER_SMOKE_CASES,
    DeliveryKind,
    OrderAs,
    OrderSmokeCase,
    PaymentKind,
)


@dataclass(frozen=True)
class ScenarioDefinition:
    case: OrderSmokeCase
    feature: str
    legacy_group: str
    tags: tuple[str, ...]
    risk: str
    source_flow: str
    max_duration_seconds: float


def _legacy_group(case_id: str) -> str:
    if case_id.startswith("delivery_at_home"):
        return "test_order_delivery"
    if case_id.startswith("self_pickup"):
        return "test_order_pickup"
    if case_id.startswith("digital_licence"):
        return "test_order_digital"
    return "test_order_mixed"


def build_order_smoke_scenarios() -> list[ScenarioDefinition]:
    scenarios: list[ScenarioDefinition] = []
    for case in ORDER_SMOKE_CASES:
        scenarios.append(
            ScenarioDefinition(
                case=case,
                feature="checkout",
                legacy_group=_legacy_group(case.case_id),
                tags=("e2e", "smoke"),
                risk="critical",
                source_flow="order_flow_service.run_full_checkout",
                max_duration_seconds=_duration_budget(case),
            )
        )
    return scenarios


def _duration_budget(case: OrderSmokeCase) -> float:
    if case.delivery_kind == DeliveryKind.COURIER:
        return 45.0
    if case.delivery_kind == DeliveryKind.STOREHOUSE:
        return 40.0
    return 35.0


def validate_smoke_coverage(scenarios: list[ScenarioDefinition]) -> list[str]:
    errors: list[str] = []
    if not scenarios:
        return ["No scenarios defined"]

    covered_order_as = {scenario.case.order_as for scenario in scenarios}
    covered_delivery = {scenario.case.delivery_kind for scenario in scenarios}
    covered_payment = {scenario.case.payment_kind for scenario in scenarios}

    missing_order_as = set(OrderAs) - covered_order_as
    missing_delivery = set(DeliveryKind) - covered_delivery
    missing_payment = set(PaymentKind) - covered_payment

    if missing_order_as:
        errors.append(f"Missing order_as coverage: {sorted(x.value for x in missing_order_as)}")
    if missing_delivery:
        errors.append(f"Missing delivery coverage: {sorted(x.value for x in missing_delivery)}")
    if missing_payment:
        errors.append(f"Missing payment coverage: {sorted(x.value for x in missing_payment)}")

    ids = [scenario.case.case_id for scenario in scenarios]
    duplicate_ids = sorted({case_id for case_id in ids if ids.count(case_id) > 1})
    if duplicate_ids:
        errors.append(f"Duplicate scenario ids: {duplicate_ids}")

    return errors


def expected_smoke_nodeids(scenarios: list[ScenarioDefinition]) -> set[str]:
    return {
        "qa/e2e/netcorner/nuxt/pl/tests/test_orders_smoke_full_process.py::"
        f"test_order_full_process[{scenario.case.case_id}]"
        for scenario in scenarios
    }


def collect_smoke_nodeids() -> set[str]:
    command = [
        sys.executable,
        "-m",
        "pytest",
        "qa/e2e/netcorner/nuxt/pl/tests/test_orders_smoke_full_process.py",
        "--collect-only",
        "-q",
    ]
    result = subprocess.run(command, check=False, capture_output=True, text=True)
    nodeids: set[str] = set()
    for line in result.stdout.splitlines():
        stripped = line.strip()
        if not stripped or "::" not in stripped:
            continue
        nodeids.add(stripped)
    return nodeids


def validate_smoke_mapping(scenarios: list[ScenarioDefinition], collected_nodeids: set[str]) -> list[str]:
    expected = expected_smoke_nodeids(scenarios)
    missing = sorted(expected - collected_nodeids)
    extra = sorted(
        nodeid
        for nodeid in collected_nodeids
        if "test_orders_smoke_full_process.py::test_order_full_process" in nodeid and nodeid not in expected
    )

    errors: list[str] = []
    if missing:
        errors.append(f"Missing scenario->test mappings: {missing}")
    if extra:
        errors.append(f"Unexpected full-process smoke tests: {extra}")
    return errors
