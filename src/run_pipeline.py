from __future__ import annotations

import argparse
import traceback

from build_dwh import build_dwh
from build_staging import build_staging
from load_raw_csv import load_raw
from pipeline_utils import get_engine, print_kpi_smoke_test, print_row_counts
from run_data_quality import run_data_quality


def run(skip_raw: bool = False, skip_dq: bool = False) -> None:
    engine = get_engine()
    if not skip_raw:
        print("\n[1/4] Load raw CSV")
        load_raw(truncate=True)
    else:
        print("\n[1/4] Skip raw load")

    print("\n[2/4] Build staging tables with Python")
    build_staging()

    print("\n[3/4] Build DWH tables with Python")
    build_dwh()

    if not skip_dq:
        print("\n[4/4] Run data quality checks with Python")
        dq = run_data_quality()
    else:
        print("\n[4/4] Skip data quality")
        dq = None

    print_row_counts(engine)
    print_kpi_smoke_test(engine)
    if dq is not None:
        print("\nData quality issues:")
        if dq.empty:
            print("  No issues recorded.")
        else:
            print(dq[["table_name", "rule_name", "issue_count"]].sort_values("issue_count", ascending=False).head(20).to_string(index=False))
    print("\nPipeline completed.")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-raw", action="store_true")
    parser.add_argument("--skip-dq", action="store_true")
    args = parser.parse_args()
    try:
        run(skip_raw=args.skip_raw, skip_dq=args.skip_dq)
    except Exception:
        traceback.print_exc()
        raise


if __name__ == "__main__":
    main()
