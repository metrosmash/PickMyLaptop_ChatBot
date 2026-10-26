"""Search methods for the laptop dataset.

All SQL for the chatbot lives here (instead of being inlined in Backend.py) so the
provider-agnostic DB layer owns the dialect. Each method validates inputs against
:mod:`database.schema` before building a query, and returns either rows or an
``{"error": ...}`` dict.
"""
from __future__ import annotations

from typing import Any, Optional

from .db import run_query
from . import schema


def search_by_attribute(attribute: str, value: Any, state: Optional[dict] = None) -> Any:
    """
    Search laptops where a specific column matches a given value.
    Example: search_by_attribute("Brand", "Dell")
    """
    if attribute not in schema.ALLOWED_COLUMNS:
        return {"error": f"Invalid attribute name: {attribute}"}

    query = f"SELECT * FROM {schema.TABLE_QUOTED} WHERE LOWER(`{attribute}`) LIKE %s LIMIT 10;"
    like_value = f"%{str(value).lower()}%"
    if state is not None:
        state["query_type"] = "use_value"
    return run_query(query, state, (like_value,))


def search_specific_laptop(keyword: Any, state: Optional[dict] = None) -> Any:
    """
    Search for a laptop by brand, product description, or processor containing the keyword.
    Example: search_specific_laptop("MacBook")
    """
    query = f"""SELECT * FROM {schema.TABLE_QUOTED}
    WHERE Brand LIKE %s OR Product_Description LIKE %s OR Processor LIKE %s OR Screen_Size LIKE %s OR RAM LIKE %s OR
    GPU LIKE %s OR GPU_Type LIKE %s OR Condition1 Like %s LIMIT 10"""

    keyword = f"%{keyword}%"
    if state is not None:
        state["query_type"] = "use_keyword"

    values = (keyword,) * query.count("%s")
    return run_query(query, state, values)


def search_by_range(attribute: str, min_value: int, max_value: int, state: Optional[dict] = None) -> Any:
    """
    Search laptop where a numeric attribute falls between two values.
    Example: search_by_range("Price", 500, 1000)
    """
    if attribute not in schema.ALLOWED_COLUMNS:
        return {"error": f"Invalid attribute name: {attribute}"}

    query = f"SELECT * FROM {schema.TABLE_QUOTED} WHERE {attribute} BETWEEN %s AND %s LIMIT 10;"
    if state is not None:
        state["query_type"] = "use_range"
    return run_query(query, state, (min_value, max_value))


def attribute_range_search(
    attribute: str,
    value: str,
    range_column: str,
    min_value: int,
    max_value: int,
    state: Optional[dict] = None,
) -> Any:
    """
    Search laptops where a specific attribute matches a value AND a numeric column
    falls within a range.

    Example:
        attribute_range_search(
            attribute="Brand", value="Dell",
            range_column="Price", min_value=100, max_value=500
        )
    """
    if attribute not in schema.ALLOWED_TEXT_COLUMNS:
        return {"error": f"Invalid text column: {attribute}"}
    if range_column not in schema.ALLOWED_NUMERIC_COLUMNS:
        return {"error": f"Invalid numeric column: {range_column}"}

    query = f"""
    SELECT * FROM {schema.TABLE_QUOTED}
    WHERE LOWER(`{attribute}`) LIKE %s
    AND `{range_column}` BETWEEN %s AND %s
    LIMIT 10;
    """
    like_value = f"%{str(value).lower()}%"
    values = (like_value, min_value, max_value)
    if state is not None:
        state["query_type"] = "specific_range"
    return run_query(query, state, values)
