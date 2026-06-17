from __future__ import annotations

import argparse
import uuid
from datetime import datetime, timezone

from pipeline_utils import TABLE_FILES, ensure_schemas, get_engine, read_csv_tables, write_df


def load_raw(truncate: bool = True) -> None:
    engine = get_engine()
    ensure_schemas(engine)
    tables = read_csv_tables()
    batch_id = str(uuid.uuid4())
    loaded_at = datetime.now(timezone.utc).replace(tzinfo=None)

    print(f"Loading raw CSV files. batch_id={batch_id}")
    for name, df in tables.items():
        df = df.copy()
        df["source_file"] = TABLE_FILES[name]
        df["loaded_at"] = loaded_at
        df["batch_id"] = batch_id
        write_df(engine, df, "raw", name, if_exists="replace" if truncate else "append")
        print(f"  raw.{name}: {len(df):,} rows")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--append", action="store_true", help="Append instead of replacing raw tables.")
    args = parser.parse_args()
    load_raw(truncate=not args.append)


if __name__ == "__main__":
    main()
