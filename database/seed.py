"""Seed the laptop dataset into the configured database.

Reads ``Data/laptop_dataset.csv`` and loads it into the ``laptop_dataset`` table
created from :data:`database.schema.DDL`.

Usage:
    python -m database.seed             # create table + insert (refuses if not empty)
    python -m database.seed --force     # truncate first, then insert
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Optional

import mysql.connector

from . import db, schema
from .exceptions import DatabaseConnectionError, DatabaseError

DATA_DIR = Path(__file__).resolve().parent.parent / "Data"
CSV_PATH = DATA_DIR / "laptop_dataset.csv"

COLUMNS = (
    "Brand", "Product_Description", "Screen_Size", "RAM", "Processor", "GPU",
    "GPU_Type", "Resolution", "Condition1", "Price", "SSD", "HDD",
)
BATCH_SIZE = 200  # keep the statement well below any free-tier max_allowed_packet
EXPECTED_ROWS = 2952


def _to_float(value) -> Optional[float]:
    text = str(value).strip() if value is not None else ""
    if text in {"", "nan", "None"}:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _to_int(value) -> Optional[int]:
    number = _to_float(value)
    return int(number) if number is not None else None


def _read_rows() -> list:
    with CSV_PATH.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _row_values(record: dict) -> list:
    """Convert one CSV record into DB-ready values (types match schema.DDL)."""
    return [
        record.get("Brand"),
        record.get("Product_Description"),
        _to_float(record.get("Screen_Size")),
        _to_int(record.get("RAM")),
        record.get("Processor"),
        record.get("GPU"),
        record.get("GPU_Type"),
        record.get("Resolution"),
        record.get("Condition1"),
        _to_float(record.get("Price")),
        _to_int(record.get("SSD")),
        _to_int(record.get("HDD")),
    ]


def _insert(conn, rows: list, batch_size: int = BATCH_SIZE) -> int:
    """Insert rows in multi-row batches (way faster than one round-trip per row)."""
    tuple_sql = "(" + ", ".join(["%s"] * len(COLUMNS)) + ")"
    column_sql = ", ".join(f"`{column}`" for column in COLUMNS)
    inserted = 0

    with conn.cursor() as cursor:
        for start in range(0, len(rows), batch_size):
            batch = rows[start:start + batch_size]
            sql = f"INSERT INTO {schema.TABLE_QUOTED} ({column_sql}) VALUES " + ", ".join(
                [tuple_sql] * len(batch)
            )
            params = tuple(value for record in batch for value in _row_values(record))
            cursor.execute(sql, params)
            inserted += len(batch)

    conn.commit()
    return inserted


def seed(settings=None, force: bool = False) -> dict:
    """Create the table (if needed) and load the CSV dataset."""
    conn = db.get_db_connection(settings)
    try:
        with conn.cursor() as cursor:
            cursor.execute(schema.DDL)
        conn.commit()

        with conn.cursor() as cursor:
            cursor.execute(f"SELECT COUNT(*) FROM {schema.TABLE_QUOTED}")
            (existing,) = cursor.fetchone()

        if existing and not force:
            raise DatabaseError(
                f"{schema.TABLE} already contains {existing} rows. "
                "Re-run with --force to truncate and reload."
            )
        if force and existing:
            with conn.cursor() as cursor:
                cursor.execute(f"TRUNCATE TABLE {schema.TABLE_QUOTED}")
            conn.commit()

        rows = _read_rows()
        inserted = _insert(conn, rows)

        with conn.cursor() as cursor:
            cursor.execute(f"SELECT COUNT(*) FROM {schema.TABLE_QUOTED}")
            (count,) = cursor.fetchone()
        return {"inserted": inserted, "total_in_table": int(count)}
    except mysql.connector.Error as error:
        raise DatabaseConnectionError(f"Failed to seed database: {error}") from error
    finally:
        db.release_connection(conn)


def main() -> None:
    parser = argparse.ArgumentParser(description="Load Data/laptop_dataset.csv into MySQL.")
    parser.add_argument("--force", action="store_true", help="truncate the table before inserting")
    args = parser.parse_args()

    result = seed(force=args.force)
    print(f"Inserted {result['inserted']} rows.")
    print(f"Table now has {result['total_in_table']} rows (CSV expects {EXPECTED_ROWS}).")


if __name__ == "__main__":
    main()
