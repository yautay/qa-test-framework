from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

import pytest

from qa.e2e.netcorner.lib import data_dump_to_logs
from qa.e2e.netcorner.lib.data_dump_to_logs import (
    dump_data,
    pop_test_data_dump,
    start_test_data_dump,
    stop_test_data_dump,
)

pytestmark = [pytest.mark.aso]


class _Mode(Enum):
    READY = "ready"


@dataclass(frozen=True)
class _Payload:
    name: str
    mode: _Mode


def test_dump_data_serializes_dataclass_and_enum() -> None:
    token = start_test_data_dump("qa/test_sample.py::test_case[a]")
    try:
        dump_data(payload=_Payload(name="sample", mode=_Mode.READY), values=(1, 2, 3))
    finally:
        stop_test_data_dump(token)

    payload = pop_test_data_dump("qa/test_sample.py::test_case[a]")

    assert payload == {
        "payload": {"name": "sample", "mode": "ready"},
        "values": [1, 2, 3],
    }


def test_dump_data_last_write_wins_per_top_level_key() -> None:
    token = start_test_data_dump("qa/test_sample.py::test_case[b]")
    try:
        dump_data(user={"email": "first@test.pl"}, auth_case={"authenticated": False})
        dump_data(user={"email": "second@test.pl"})
    finally:
        stop_test_data_dump(token)

    payload = pop_test_data_dump("qa/test_sample.py::test_case[b]")

    assert payload == {
        "user": {"email": "second@test.pl"},
        "auth_case": {"authenticated": False},
    }


def test_dump_data_raises_outside_active_test_context() -> None:
    token = data_dump_to_logs._CURRENT_TEST_NODEID.set("")
    try:
        with pytest.raises(RuntimeError, match="active test context"):
            dump_data(user={"email": "outside@test.pl"})
    finally:
        data_dump_to_logs._CURRENT_TEST_NODEID.reset(token)
