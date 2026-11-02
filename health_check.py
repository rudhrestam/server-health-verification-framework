#!/usr/bin/env python3
"""
Parallel health-verification framework (demo).

Runs a configurable set of checks against a list of sample targets, in
parallel, then writes a summary report and an audit log. Targets are
simulated (see sample_targets.json) so the demo runs anywhere with no
real infrastructure — swap `run_check` for real probes (port, HTTP, SQL)
to use the same pattern against actual systems.

Usage:
    python health_check.py [--config sample_targets.json] [--workers 4]
Outputs:
    report.json  - machine-readable summary
    audit.log    - one line per check execution, appended each run
"""

import argparse
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).parent


def run_check(target: dict, check: dict) -> dict:
    """Simulated check. In production this is where a real probe goes —
    a port connect, an HTTP GET, a lightweight query — with the same
    contract: return a result dict, never raise."""
    time.sleep(0.05)  # stand-in for probe latency
    simulated = target.get("simulated_state", {})
    passed = simulated.get(check["name"], True)
    return {
        "target": target["name"],
        "check": check["name"],
        "status": "PASS" if passed else "FAIL",
        "detail": check.get("description", ""),
        "checked_at": datetime.now(timezone.utc).isoformat(),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default=str(BASE / "sample_targets.json"))
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()

    config = json.loads(Path(args.config).read_text(encoding="utf-8"))
    targets, check_defs = config["targets"], config["checks"]

    jobs = [(t, c) for t in targets for c in check_defs]
    print(f"Running {len(jobs)} checks on {len(targets)} targets "
          f"with {args.workers} parallel workers...\n")

    results = []
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(run_check, t, c): (t, c) for t, c in jobs}
        for future in as_completed(futures):
            results.append(future.result())

    results.sort(key=lambda r: (r["target"], r["check"]))
    failed = [r for r in results if r["status"] == "FAIL"]

    for r in results:
        mark = "✓" if r["status"] == "PASS" else "✗"
        print(f"{mark} {r['target']:<18} {r['check']:<22} {r['status']}")

    summary = {
        "run_at": datetime.now(timezone.utc).isoformat(),
        "targets": len(targets),
        "checks_total": len(results),
        "passed": len(results) - len(failed),
        "failed": len(failed),
        "failures": failed,
        "results": results,
    }
    (BASE / "report.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    with open(BASE / "audit.log", "a", encoding="utf-8") as log:
        for r in results:
            log.write(f"{r['checked_at']} {r['target']} {r['check']} {r['status']}\n")

    print(f"\n{summary['passed']}/{summary['checks_total']} checks passed. "
          f"Report: report.json · Audit log: audit.log")
    if failed:
        print(f"FAILED targets: {sorted({r['target'] for r in failed})} — "
              "these are the built-in failure scenarios; see README.")
    raise SystemExit(1 if failed else 0)


if __name__ == "__main__":
    main()
