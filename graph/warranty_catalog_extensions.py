"""
Enterprise warranty ontology extensions: model/SKU, BOM components, error codes,
diagnostic trees, asset/claim entities — merged into the knowledge catalog.
"""

from __future__ import annotations

# Per-product extensions keyed by product_id
PRODUCT_EXTENSIONS: dict[str, dict] = {
    "wm-001": {
        "model": {
            "model_id": "mdl-wm8k",
            "model_number": "AH-WM8K",
            "name": "AquaHome Front Load 8kg",
        },
        "skus": [
            {"sku_id": "SKU-WM8K-2023", "model_id": "mdl-wm8k", "revision": "A", "model_year": 2023},
            {"sku_id": "SKU-WM8K-2024", "model_id": "mdl-wm8k", "revision": "B", "model_year": 2024},
        ],
        "components": [
            {"component_id": "wm-c01", "name": "Drive System", "subsystem": "Mechanical Drive"},
            {"component_id": "wm-c02", "name": "Drain System", "subsystem": "Plumbing"},
            {"component_id": "wm-c03", "name": "Suspension System", "subsystem": "Structural"},
        ],
        "component_part_links": [
            {"component_id": "wm-c01", "part_id": "wm-p01"},
            {"component_id": "wm-c02", "part_id": "wm-p02"},
            {"component_id": "wm-c03", "part_id": "wm-p03"},
        ],
        "failure_mode_component_links": [
            {"failure_mode_id": "wm-fm01", "component_id": "wm-c01", "impact_severity": "primary"},
            {"failure_mode_id": "wm-fm02", "component_id": "wm-c02", "impact_severity": "primary"},
            {"failure_mode_id": "wm-fm03", "component_id": "wm-c03", "impact_severity": "primary"},
        ],
        "error_codes": [
            {"error_code_id": "wm-ec-e21", "code": "E21", "description": "Drain timeout — pump or blockage fault"},
        ],
        "error_code_failure_links": [
            {"error_code_id": "wm-ec-e21", "failure_mode_id": "wm-fm02", "confidence": 0.93},
        ],
        "diagnostic_step_failure_links": [
            {"step_id": "wm-d01", "failure_mode_id": "wm-fm01", "link_type": "CONFIRMS", "confidence": 0.82},
            {"step_id": "wm-d02", "failure_mode_id": "wm-fm01", "link_type": "CONFIRMS", "confidence": 0.95},
            {"step_id": "wm-d03", "failure_mode_id": "wm-fm02", "link_type": "CONFIRMS", "confidence": 0.90},
            {"step_id": "wm-d04", "failure_mode_id": "wm-fm03", "link_type": "CONFIRMS", "confidence": 0.88},
            {"step_id": "wm-d01", "failure_mode_id": "wm-fm02", "link_type": "RULES_OUT", "confidence": 0.60},
        ],
        "failure_mode_part_links": [
            {"failure_mode_id": "wm-fm01", "part_id": "wm-p01", "quantity": 1, "probability": 0.94, "is_primary": True},
            {"failure_mode_id": "wm-fm02", "part_id": "wm-p02", "quantity": 1, "probability": 0.91, "is_primary": True},
            {"failure_mode_id": "wm-fm03", "part_id": "wm-p03", "quantity": 1, "probability": 0.89, "is_primary": True},
        ],
        "sku_part_links": [
            {"sku_id": "SKU-WM8K-2023", "part_id": "wm-p01"},
            {"sku_id": "SKU-WM8K-2023", "part_id": "wm-p02"},
            {"sku_id": "SKU-WM8K-2023", "part_id": "wm-p03"},
            {"sku_id": "SKU-WM8K-2024", "part_id": "wm-p01"},
            {"sku_id": "SKU-WM8K-2024", "part_id": "wm-p02"},
            {"sku_id": "SKU-WM8K-2024", "part_id": "wm-p03"},
        ],
    },
    "dw-001": {
        "model": {
            "model_id": "mdl-dw12",
            "model_number": "CW-DW12",
            "name": "CleanWave Built-in 12 Place",
        },
        "skus": [
            {"sku_id": "SKU-DW12-2022", "model_id": "mdl-dw12", "revision": "A", "model_year": 2022},
        ],
        "components": [
            {"component_id": "dw-c01", "name": "Heating System", "subsystem": "Thermal"},
            {"component_id": "dw-c02", "name": "Drain System", "subsystem": "Plumbing"},
            {"component_id": "dw-c03", "name": "Wash Circulation", "subsystem": "Hydraulic"},
        ],
        "component_part_links": [
            {"component_id": "dw-c01", "part_id": "dw-p01"},
            {"component_id": "dw-c02", "part_id": "dw-p02"},
            {"component_id": "dw-c03", "part_id": "dw-p03"},
        ],
        "failure_mode_component_links": [
            {"failure_mode_id": "dw-fm01", "component_id": "dw-c01", "impact_severity": "primary"},
            {"failure_mode_id": "dw-fm02", "component_id": "dw-c02", "impact_severity": "primary"},
            {"failure_mode_id": "dw-fm03", "component_id": "dw-c03", "impact_severity": "primary"},
        ],
        "error_codes": [
            {"error_code_id": "dw-ec-f09", "code": "F09", "description": "Heating circuit fault"},
        ],
        "error_code_failure_links": [
            {"error_code_id": "dw-ec-f09", "failure_mode_id": "dw-fm01", "confidence": 0.92},
        ],
        "diagnostic_step_failure_links": [
            {"step_id": "dw-d01", "failure_mode_id": "dw-fm01", "link_type": "CONFIRMS", "confidence": 0.91},
            {"step_id": "dw-d02", "failure_mode_id": "dw-fm02", "link_type": "CONFIRMS", "confidence": 0.87},
            {"step_id": "dw-d03", "failure_mode_id": "dw-fm03", "link_type": "CONFIRMS", "confidence": 0.93},
        ],
        "failure_mode_part_links": [
            {"failure_mode_id": "dw-fm01", "part_id": "dw-p01", "quantity": 1, "probability": 0.90, "is_primary": True},
            {"failure_mode_id": "dw-fm02", "part_id": "dw-p02", "quantity": 1, "probability": 0.85, "is_primary": True},
            {"failure_mode_id": "dw-fm03", "part_id": "dw-p03", "quantity": 1, "probability": 0.92, "is_primary": True},
        ],
        "sku_part_links": [
            {"sku_id": "SKU-DW12-2022", "part_id": "dw-p01"},
            {"sku_id": "SKU-DW12-2022", "part_id": "dw-p02"},
            {"sku_id": "SKU-DW12-2022", "part_id": "dw-p03"},
        ],
    },
    "mw-001": {
        "model": {
            "model_id": "mdl-mw25",
            "model_number": "HP-MW25",
            "name": "HeatPro Convection 25L",
        },
        "skus": [
            {"sku_id": "SKU-MW25-2024", "model_id": "mdl-mw25", "revision": "A", "model_year": 2024},
        ],
        "components": [
            {"component_id": "mw-c01", "name": "Magnetron HV System", "subsystem": "RF Generation"},
            {"component_id": "mw-c02", "name": "Waveguide Assembly", "subsystem": "RF Delivery"},
            {"component_id": "mw-c03", "name": "Convection Airflow", "subsystem": "Thermal"},
        ],
        "component_part_links": [
            {"component_id": "mw-c01", "part_id": "mw-p01"},
            {"component_id": "mw-c02", "part_id": "mw-p02"},
            {"component_id": "mw-c03", "part_id": "mw-p03"},
        ],
        "failure_mode_component_links": [
            {"failure_mode_id": "mw-fm01", "component_id": "mw-c01", "impact_severity": "primary"},
            {"failure_mode_id": "mw-fm02", "component_id": "mw-c02", "impact_severity": "primary"},
            {"failure_mode_id": "mw-fm03", "component_id": "mw-c03", "impact_severity": "primary"},
        ],
        "error_codes": [
            {"error_code_id": "mw-ec-hv", "code": "HV", "description": "High-voltage / magnetron fault"},
        ],
        "error_code_failure_links": [
            {"error_code_id": "mw-ec-hv", "failure_mode_id": "mw-fm01", "confidence": 0.95},
        ],
        "diagnostic_step_failure_links": [
            {"step_id": "mw-d01", "failure_mode_id": "mw-fm01", "link_type": "CONFIRMS", "confidence": 0.94},
            {"step_id": "mw-d02", "failure_mode_id": "mw-fm02", "link_type": "CONFIRMS", "confidence": 0.92},
            {"step_id": "mw-d03", "failure_mode_id": "mw-fm03", "link_type": "CONFIRMS", "confidence": 0.88},
        ],
        "failure_mode_part_links": [
            {"failure_mode_id": "mw-fm01", "part_id": "mw-p01", "quantity": 1, "probability": 0.93, "is_primary": True},
            {"failure_mode_id": "mw-fm02", "part_id": "mw-p02", "quantity": 1, "probability": 0.96, "is_primary": True},
            {"failure_mode_id": "mw-fm03", "part_id": "mw-p03", "quantity": 1, "probability": 0.90, "is_primary": True},
        ],
        "sku_part_links": [
            {"sku_id": "SKU-MW25-2024", "part_id": "mw-p01"},
            {"sku_id": "SKU-MW25-2024", "part_id": "mw-p02"},
            {"sku_id": "SKU-MW25-2024", "part_id": "mw-p03"},
        ],
    },
}

SERIAL_TO_SKU: dict[str, str] = {
    "AH-WM8K-2023": "SKU-WM8K-2023",
    "AH-WM8K-2024": "SKU-WM8K-2024",
    "CW-DW12-2022": "SKU-DW12-2022",
    "HP-MW25-2024": "SKU-MW25-2024",
}


def resolve_sku_from_serial(serial_number: str) -> str | None:
    for prefix, sku_id in SERIAL_TO_SKU.items():
        if serial_number.upper().startswith(prefix):
            return sku_id
    return None


ENTERPRISE_ASSETS = [
    {
        "asset_id": "AST-WM-4421",
        "customer_id": "CUST-10042",
        "product_id": "wm-001",
        "sku_id": "SKU-WM8K-2023",
        "model_number": "AH-WM8K",
        "serial_number": "AH-WM8K-2023-99421",
        "purchase_date": "2023-06-15",
        "warranty_status": "active",
        "warranty_expiry": "2027-06-15",
        "policy_id": "WP-STANDARD-24M",
    },
    {
        "asset_id": "AST-DW-1180",
        "customer_id": "CUST-10087",
        "product_id": "dw-001",
        "sku_id": "SKU-DW12-2022",
        "model_number": "CW-DW12",
        "serial_number": "CW-DW12-2022-33180",
        "purchase_date": "2022-11-03",
        "warranty_status": "active",
        "warranty_expiry": "2027-11-03",
        "policy_id": "WP-STANDARD-24M",
    },
    {
        "asset_id": "AST-MW-7702",
        "customer_id": "CUST-10042",
        "product_id": "mw-001",
        "sku_id": "SKU-MW25-2024",
        "model_number": "HP-MW25",
        "serial_number": "HP-MW25-2024-07702",
        "purchase_date": "2024-02-20",
        "warranty_status": "active",
        "warranty_expiry": "2027-02-20",
        "policy_id": "WP-STANDARD-24M",
    },
]

WARRANTY_POLICIES = [
    {
        "policy_id": "WP-STANDARD-24M",
        "description": "Standard 24-month manufacturer warranty",
        "coverage_months": 24,
        "covers_parts": True,
        "covers_labor": True,
        "max_parts_cost_usd": 500.0,
    },
]

ENTERPRISE_CLAIMS = [
    {
        "claim_id": "CLM-2026-00481",
        "asset_id": "AST-WM-4421",
        "product_id": "wm-001",
        "symptom_id": "wm-s03",
        "confirmed_failure_mode_id": "wm-fm02",
        "used_part_id": "wm-p02",
        "resolution_summary": "Approved drain pump replacement under warranty.",
        "closed_date": "2026-02-01",
    },
    {
        "claim_id": "CLM-2025-01933",
        "asset_id": "AST-MW-7702",
        "product_id": "mw-001",
        "symptom_id": "mw-s02",
        "confirmed_failure_mode_id": "mw-fm02",
        "used_part_id": "mw-p02",
        "resolution_summary": "Waveguide cover replaced; arcing resolved.",
        "closed_date": "2025-12-10",
    },
]


def merge_product_extensions(product_data: dict) -> dict:
    """Attach enterprise ontology extensions to a product catalog entry."""
    pid = product_data["product"]["product_id"]
    ext = PRODUCT_EXTENSIONS.get(pid, {})
    merged = {**product_data, **ext}
    if ext.get("failure_mode_part_links"):
        merged["failure_mode_part_links"] = ext["failure_mode_part_links"]
    return merged


def build_enterprise_catalog_payload(products: list[dict]) -> dict:
    return {
        "products": [merge_product_extensions(p) for p in products],
        "assets": ENTERPRISE_ASSETS,
        "warranty_policies": WARRANTY_POLICIES,
        "claims": ENTERPRISE_CLAIMS,
    }
