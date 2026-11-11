# Server Health Verification Framework (Demo)

![CI](https://github.com/rudhrestam/server-health-verification-framework/actions/workflows/ci.yml/badge.svg) ![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)

After a fleet-wide reboot or patch cycle, someone has to prove every system actually came back healthy. Done by hand, that's hours of repetitive checking — and the checks that get skipped are the ones that matter. This demo shows the automation pattern: run every check, on every target, in parallel, and produce a report a human can trust.

> This is a representative demo of patterns used in production systems, built with simulated targets and original code. It contains no employer code, data, hostnames, or internal details.

## The pattern

1. **Configure, don't hardcode** — targets and check definitions live in `sample_targets.json`. Adding a target or a check is a config edit, not a code change.
2. **Run in parallel** — checks execute in a thread pool (`concurrent.futures`), so total runtime tracks the slowest check, not the sum of all checks.
3. **Validate per check** — every check returns a structured pass/fail result with a timestamp; a check that errors is reported, never silently skipped.
4. **Summarize** — `report.json` gives totals plus the full failure list, so an operator sees in seconds which targets need attention.
5. **Audit everything** — each run appends one line per check to `audit.log`, creating a durable record of what was verified and when.

## Failure scenarios (built in)

The sample config ships with two deliberate failures so you can see the reporting work:

- `sample-db-02` — service down: fails `service_running`, `port_open`, and `smoke_query`.
- `sample-worker-01` — fails `disk_space_ok`.

The script exits non-zero when any check fails, so it can gate a pipeline or alert an operator.

## Run it

```bash
python health_check.py                 # 4 parallel workers
python health_check.py --workers 8     # wider parallelism
```

No dependencies — Python 3.10+ standard library only.

## Making it real

`run_check()` is the only simulated piece. Replace its body with real probes — a socket connect for a port, an HTTP GET for a service, a lightweight query for a database — and the parallel execution, reporting, and audit layers work unchanged. Scheduling (cron, or any job scheduler) turns it into a standing verification step after every maintenance window.

## Tech stack

Python 3.10+ · concurrent.futures · JSON config · structured reporting / audit logging

## What it demonstrates

- Parallel execution design for fleet-scale verification
- Config-driven checks that extend without code changes
- Failure-scenario testing as a first-class feature
- Audit trails for operational verification
