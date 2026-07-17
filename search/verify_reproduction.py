#!/usr/bin/env python3
"""Audit the frozen search replay and independently validate its certificate."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
EXPECTED = {
    "near_witness.json": "9540153c3f9c67236ed3249948845bbd77d9d62d7a3ec68fc7a8b1feaa86f89f",
    "near_witness_reproduced.json": "9465cb0dcf00fc13533c0ef49cfcd11daba044370db5bbeab744f68eaeb6d6d4",
    "certificate_reproduced.json": "3d3a476aa481ac0e5a0fd51e3f4a677d8dadf5ec3c000ed0f972dee1982bf8db",
    "certificate_end_to_end.json": "98c1d1eef4182bde1679edd3e8f6aa6ec7522f1ae123e8baa68f467034e40222",
    "kempe_search.py": "8d07640def2df790dfba114ac62756940352cb1452239294e5888a98c79489df",
    "solve_lazy_sat.js": "91a7a83d9a73b1d48a3538b45d430a4f76798dee6c8061fc41c68cdc8f12c137",
    "verifier.py": "f770102c63e77d24a6c9298705388e4906250964587ec8a9a0280c1f71c31d91",
    "verifier_cleanroom.py": "8a9fae037cb222069ae3297c4ea757b856a86ee8f72478727a85dcb3f6d84e43",
}


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            value.update(block)
    return value.hexdigest()


def records(path: str) -> list[dict[str, object]]:
    return [json.loads(line) for line in
            (ROOT / path).read_text(encoding="utf-8").splitlines()]


def check_logs() -> None:
    exact_records = records("kempe_successful_run.log")
    found = [record for record in exact_records if record.get("result") == "found"]
    assert len(found) == 1, "expected exactly one exact-replay success record"
    assert found[0]["depth"] == 8
    assert found[0]["visited"] == 599257
    assert found[0]["quality"] == [0, 0, [1] * 9]
    assert exact_records[-1]["event"] == "finish"
    assert exact_records[-1]["exit_status"] == 0

    sat_records = records("lazy_sat_run.log")
    near = [record for record in sat_records if record.get("result") == "near_witness"]
    assert len(near) == 1, "expected exactly one SAT near-witness record"
    assert near[0]["rounds"] == 5067
    assert near[0]["cuts"] == 89540
    assert near[0]["bad_pairs"] == 1
    assert near[0]["component_excess"] == 2
    assert sat_records[-1]["event"] == "finish"
    assert sat_records[-1]["exit_status"] == 31

    end_records = records("end_to_end_run.log")
    found = [record for record in end_records if record.get("result") == "found"]
    assert len(found) == 1, "expected exactly one end-to-end success record"
    assert found[0]["depth"] == 12
    assert found[0]["visited"] == 1286206
    assert found[0]["quality"] == [0, 0, [1] * 9]
    assert end_records[-1]["event"] == "finish"
    assert end_records[-1]["exit_status"] == 0


def run_checker(command: list[str]) -> str:
    result = subprocess.run(command, cwd=ROOT, check=True, text=True,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return result.stdout.strip()


def main() -> int:
    observed = {name: digest(ROOT / name) for name in EXPECTED}
    assert observed == EXPECTED, {name: (EXPECTED[name], observed[name])
                                  for name in EXPECTED if observed[name] != EXPECTED[name]}
    check_logs()
    outputs = {
        "exact_primary": run_checker([sys.executable, "verifier.py",
                                      "certificate_reproduced.json"]),
        "exact_cleanroom": run_checker([sys.executable, "verifier_cleanroom.py",
                                        "certificate_reproduced.json"]),
        "exact_cleanroom_optimized": run_checker(
            [sys.executable, "-O", "verifier_cleanroom.py", "certificate_reproduced.json"]),
        "end_to_end_primary": run_checker([sys.executable, "verifier.py",
                                           "certificate_end_to_end.json"]),
        "end_to_end_cleanroom": run_checker([sys.executable, "verifier_cleanroom.py",
                                             "certificate_end_to_end.json"]),
        "end_to_end_cleanroom_optimized": run_checker(
            [sys.executable, "-O", "verifier_cleanroom.py", "certificate_end_to_end.json"]),
    }
    summary = {
        "result": "VALID REPRODUCTION",
        "exact_replay": {
            "depth": 8,
            "visited_states": 599257,
            "certificate_sha256": observed["certificate_reproduced.json"],
            "cleanroom": outputs["exact_cleanroom"],
        },
        "end_to_end_reproduction": {
            "sat_rounds": 5067,
            "sat_connectivity_cuts": 89540,
            "kempe_depth": 12,
            "kempe_visited_states": 1286206,
            "certificate_sha256": observed["certificate_end_to_end.json"],
            "cleanroom": outputs["end_to_end_cleanroom"],
        },
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
