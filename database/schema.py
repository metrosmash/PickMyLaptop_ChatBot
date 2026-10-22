"""Single source of truth for the laptop dataset schema.

Keeping table + column knowledge in ONE place (instead of copy-pasting allow-lists
into every tool function in Backend.py) means:
  * adding a column to the DB never breaks an allow-list silently, and
  * the LLM can never inject arbitrary SQL via tool arguments -- every column name
    used in a query must be in ``ALLOWED_COLUMNS``.
"""
from __future__ import annotations

TABLE = "laptop_dataset"
TABLE_QUOTED = f"`{TABLE}`"

ALLOWED_COLUMNS = {
    "id", "Brand", "Product_Description", "Screen_Size", "RAM", "Processor",
    "GPU", "GPU_Type", "Resolution", "Condition1", "Price", "SSD", "HDD",
}

# For the text + numeric combined search tool: which columns are valid TEXT columns
# and which are valid NUMERIC columns respectively.
ALLOWED_TEXT_COLUMNS = {
    "Brand", "Product_Description", "Processor", "Condition1", "GPU", "GPU_Type", "Resolution",
}
ALLOWED_NUMERIC_COLUMNS = {"Price", "RAM", "SSD", "HDD", "Screen_Size"}

DDL = """
CREATE TABLE IF NOT EXISTS laptop_dataset (
  id INT AUTO_INCREMENT PRIMARY KEY,
  Brand VARCHAR(255),
  Product_Description TEXT,
  Screen_Size FLOAT,
  RAM INT,
  Processor VARCHAR(255),
  GPU VARCHAR(255),
  GPU_Type VARCHAR(255),
  Resolution VARCHAR(100),
  Condition1 VARCHAR(255),
  Price DECIMAL(10,2),
  SSD INT,
  HDD INT
);
"""
