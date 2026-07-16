"""Domain fault codes aligned with graph/oem_product_catalog.py demo set."""

from __future__ import annotations

FAULT_CATALOG: list[dict] = [
    {"code": "UE", "description": "Unbalanced load — rebalance or calibration", "family": "washer"},
    {"code": "4E", "description": "Water supply error — inlet valve or pressure", "family": "washer"},
    {"code": "5E", "description": "Drain error — filter, hose, or pump", "family": "washer"},
    {"code": "OE", "description": "Drain timeout / overfill related", "family": "washer"},
    {"code": "IE", "description": "Water fill insufficient after 10 minutes", "family": "washer"},
    {"code": "HE", "description": "Heating error", "family": "washer"},
    {"code": "AE", "description": "Leak / overfill protection activated", "family": "washer"},
    {"code": "E24", "description": "Drain issue", "family": "dishwasher"},
    {"code": "E01", "description": "Pump failure", "family": "dishwasher"},
    {"code": "F9E1", "description": "Drain pump fault", "family": "dryer"},
    {"code": "F9E0", "description": "Drain system fault variant", "family": "dryer"},
    {"code": "22E", "description": "Evaporator fan error", "family": "fridge"},
    {"code": "33E", "description": "Ice maker fan error", "family": "fridge"},
    {"code": "39E", "description": "Ice maker function error", "family": "fridge"},
    {"code": "LC", "description": "Child lock / control lock", "family": "washer"},
    {"code": "OC", "description": "Over current / overload", "family": "generic"},
    {"code": "DE", "description": "Door error", "family": "washer"},
]

CODE_TO_IDX = {row["code"]: i for i, row in enumerate(FAULT_CATALOG)}
IDX_TO_CODE = {i: row["code"] for i, row in enumerate(FAULT_CATALOG)}
N_CLASSES = len(FAULT_CATALOG)


def is_closed_set_code(code: str) -> bool:
    return code.upper() in CODE_TO_IDX


def catalog_codes() -> list[str]:
    return [row["code"] for row in FAULT_CATALOG]
