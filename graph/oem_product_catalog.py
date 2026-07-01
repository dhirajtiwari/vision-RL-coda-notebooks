"""
Enterprise OEM product blueprint catalog.

Data is sourced from publicly available OEM support documentation (error codes,
troubleshooting flows, model numbers). Part numbers are representative service
BOM categories — not proprietary internal OEM SKUs unless publicly listed.

Sources cited per product in `oem_sources` field.
"""

from __future__ import annotations

from graph.synthetic_data_generator import (
    build_dishwasher,
    build_microwave,
    build_washing_machine,
)
from graph.warranty_catalog_extensions import build_enterprise_catalog_payload


def _bp(
    *,
    product_id: str,
    oem: str,
    name: str,
    category: str,
    brand: str,
    model_year: int,
    model_id: str,
    model_number: str,
    model_name: str,
    sku_id: str,
    sku_revision: str = "A",
    components: list[dict],
    symptoms: list[dict],
    failure_modes: list[dict],
    diagnostic_steps: list[dict],
    parts: list[dict],
    symptom_failure_links: list[dict],
    failure_mode_part_links: list[dict],
    failure_mode_component_links: list[dict],
    component_part_links: list[dict],
    error_codes: list[dict],
    error_code_failure_links: list[dict],
    diagnostic_step_failure_links: list[dict],
    diagnostic_tree_links: list[dict] | None = None,
    historical_resolutions: list[dict] | None = None,
    oem_sources: list[str],
) -> dict:
    sku_part_links = [{"sku_id": sku_id, "part_id": p["part_id"]} for p in parts]
    return {
        "product": {
            "product_id": product_id,
            "name": name,
            "category": category,
            "brand": brand,
            "model_year": model_year,
            "oem": oem,
        },
        "model": {"model_id": model_id, "model_number": model_number, "name": model_name},
        "skus": [{"sku_id": sku_id, "model_id": model_id, "revision": sku_revision, "model_year": model_year}],
        "components": components,
        "symptoms": symptoms,
        "failure_modes": failure_modes,
        "diagnostic_steps": diagnostic_steps,
        "parts": parts,
        "symptom_failure_links": symptom_failure_links,
        "failure_mode_part_links": failure_mode_part_links,
        "failure_mode_component_links": failure_mode_component_links,
        "component_part_links": component_part_links,
        "error_codes": error_codes,
        "error_code_failure_links": error_code_failure_links,
        "diagnostic_step_failure_links": diagnostic_step_failure_links,
        "diagnostic_tree_links": diagnostic_tree_links or [],
        "sku_part_links": sku_part_links,
        "historical_resolutions": historical_resolutions or [],
        "oem_sources": oem_sources,
    }


def samsung_wf45t6000aw() -> dict:
    pid = "oem-sam-wf45"
    return _bp(
        product_id=pid,
        oem="Samsung",
        name="Samsung WF45T6000AW Front Load Washer",
        category="Laundry",
        brand="Samsung",
        model_year=2022,
        model_id="mdl-sam-wf45",
        model_number="WF45T6000AW",
        model_name="Samsung 4.5 cu. ft. Front Load Washer",
        sku_id="SKU-SAM-WF45-2022",
        components=[
            {"component_id": f"{pid}-c-drive", "name": "Drum Drive System", "subsystem": "Mechanical"},
            {"component_id": f"{pid}-c-drain", "name": "Drain & Pump Assembly", "subsystem": "Plumbing"},
            {"component_id": f"{pid}-c-motor", "name": "Drive Motor & Inverter", "subsystem": "Electrical"},
        ],
        symptoms=[
            {"symptom_id": f"{pid}-s01", "description": "Washer does not spin at all during cycle", "severity": "high"},
            {"symptom_id": f"{pid}-s02", "description": "Clothes extremely wet after final spin", "severity": "medium"},
            {"symptom_id": f"{pid}-s03", "description": "UE error — unbalanced load repeated", "severity": "medium"},
            {"symptom_id": f"{pid}-s04", "description": "4E or 5E water supply error displayed", "severity": "high"},
        ],
        failure_modes=[
            {
                "failure_mode_id": f"{pid}-fm01",
                "name": "Clogged Pump Filter / Drain Blockage",
                "description": "Pump filter obstructed preventing drain before spin phase.",
                "estimated_repair_time_minutes": 40,
                "safety_notes": "Unplug unit; residual water in filter housing.",
            },
            {
                "failure_mode_id": f"{pid}-fm02",
                "name": "Drain Hose Siphoning / Install Fault",
                "description": "Incorrect drain hose depth causes siphoning; washer cannot drain.",
                "estimated_repair_time_minutes": 30,
                "safety_notes": "Drain hose must be 6-8 inches into standpipe.",
            },
            {
                "failure_mode_id": f"{pid}-fm03",
                "name": "Drive Motor or Inverter Fault",
                "description": "Motor does not engage after drain completes; calibration fails.",
                "estimated_repair_time_minutes": 120,
                "safety_notes": "Certified technician for motor/inverter service.",
            },
        ],
        diagnostic_steps=[
            {
                "step_id": f"{pid}-d01",
                "description": "Clean front-load pump filter and verify impeller turns freely.",
                "order": 1,
                "expected_outcome": "Debris removed; impeller spins",
            },
            {
                "step_id": f"{pid}-d02",
                "description": "Verify drain hose 6-8 in standpipe, no airtight seal, 18-96 in height.",
                "order": 2,
                "expected_outcome": "Hose routed per Samsung install spec",
            },
            {
                "step_id": f"{pid}-d03",
                "description": "Run Calibration Mode (Temp + Delay End 3 sec → Cb → Start).",
                "order": 3,
                "expected_outcome": "Tub rotates in calibration or shows En/End",
            },
            {
                "step_id": f"{pid}-d04",
                "description": "If no spin after calibration, test motor engagement in spin cycle.",
                "order": 4,
                "expected_outcome": "Motor hums without drum rotation → motor fault",
            },
        ],
        parts=[
            {
                "part_id": f"{pid}-p01",
                "name": "Drain Pump Assembly",
                "part_number": "DC31-00098A",
                "estimated_cost_usd": 78.00,
            },
            {
                "part_id": f"{pid}-p02",
                "name": "Drive Belt Kit",
                "part_number": "6602-001655",
                "estimated_cost_usd": 32.00,
            },
            {
                "part_id": f"{pid}-p03",
                "name": "Motor Inverter Board",
                "part_number": "DC92-01583A",
                "estimated_cost_usd": 185.00,
            },
        ],
        symptom_failure_links=[
            {"symptom_id": f"{pid}-s01", "failure_mode_id": f"{pid}-fm01", "confidence": 0.88},
            {"symptom_id": f"{pid}-s01", "failure_mode_id": f"{pid}-fm03", "confidence": 0.72},
            {"symptom_id": f"{pid}-s02", "failure_mode_id": f"{pid}-fm01", "confidence": 0.80},
            {"symptom_id": f"{pid}-s03", "failure_mode_id": f"{pid}-fm02", "confidence": 0.65},
            {"symptom_id": f"{pid}-s04", "failure_mode_id": f"{pid}-fm02", "confidence": 0.70},
        ],
        failure_mode_part_links=[
            {
                "failure_mode_id": f"{pid}-fm01",
                "part_id": f"{pid}-p01",
                "quantity": 1,
                "probability": 0.86,
                "is_primary": True,
            },
            {
                "failure_mode_id": f"{pid}-fm02",
                "part_id": f"{pid}-p02",
                "quantity": 1,
                "probability": 0.55,
                "is_primary": False,
            },
            {
                "failure_mode_id": f"{pid}-fm03",
                "part_id": f"{pid}-p03",
                "quantity": 1,
                "probability": 0.82,
                "is_primary": True,
            },
        ],
        failure_mode_component_links=[
            {"failure_mode_id": f"{pid}-fm01", "component_id": f"{pid}-c-drain", "impact_severity": "primary"},
            {"failure_mode_id": f"{pid}-fm02", "component_id": f"{pid}-c-drain", "impact_severity": "primary"},
            {"failure_mode_id": f"{pid}-fm03", "component_id": f"{pid}-c-motor", "impact_severity": "primary"},
        ],
        component_part_links=[
            {"component_id": f"{pid}-c-drain", "part_id": f"{pid}-p01"},
            {"component_id": f"{pid}-c-drive", "part_id": f"{pid}-p02"},
            {"component_id": f"{pid}-c-motor", "part_id": f"{pid}-p03"},
        ],
        error_codes=[
            {
                "error_code_id": f"{pid}-ec-ue",
                "code": "UE",
                "description": "Unbalanced load — rebalance or calibration",
            },
            {
                "error_code_id": f"{pid}-ec-4e",
                "code": "4E",
                "description": "Water supply error — inlet valve or pressure",
            },
            {"error_code_id": f"{pid}-ec-5e", "code": "5E", "description": "Drain error — filter, hose, or pump"},
        ],
        error_code_failure_links=[
            {"error_code_id": f"{pid}-ec-ue", "failure_mode_id": f"{pid}-fm02", "confidence": 0.75},
            {"error_code_id": f"{pid}-ec-4e", "failure_mode_id": f"{pid}-fm02", "confidence": 0.68},
            {"error_code_id": f"{pid}-ec-5e", "failure_mode_id": f"{pid}-fm01", "confidence": 0.92},
        ],
        diagnostic_step_failure_links=[
            {"step_id": f"{pid}-d01", "failure_mode_id": f"{pid}-fm01", "link_type": "CONFIRMS", "confidence": 0.90},
            {"step_id": f"{pid}-d02", "failure_mode_id": f"{pid}-fm02", "link_type": "CONFIRMS", "confidence": 0.85},
            {"step_id": f"{pid}-d03", "failure_mode_id": f"{pid}-fm03", "link_type": "RULES_OUT", "confidence": 0.70},
            {"step_id": f"{pid}-d04", "failure_mode_id": f"{pid}-fm03", "link_type": "CONFIRMS", "confidence": 0.88},
        ],
        diagnostic_tree_links=[
            {"from_step_id": f"{pid}-d01", "to_step_id": f"{pid}-d02", "condition": "spin_still_fails"},
            {"from_step_id": f"{pid}-d02", "to_step_id": f"{pid}-d03", "condition": "install_ok_spin_fails"},
            {"from_step_id": f"{pid}-d03", "to_step_id": f"{pid}-d04", "condition": "calibration_no_spin"},
        ],
        oem_sources=[
            "https://www.samsung.com/us/support/troubleshoot/TSG10003486/",
            "https://www.samsung.com/ph/support/home-appliances/samsung-front-load-washer-error-codes/",
        ],
    )


def lg_ldf5545st() -> dict:
    pid = "oem-lg-ldf5545"
    return _bp(
        product_id=pid,
        oem="LG",
        name="LG LDF5545ST Built-in Dishwasher",
        category="Kitchen",
        brand="LG",
        model_year=2021,
        model_id="mdl-lg-ldf5545",
        model_number="LDF5545ST",
        model_name="LG Front Control Dishwasher",
        sku_id="SKU-LG-LDF5545-2021",
        components=[
            {"component_id": f"{pid}-c-inlet", "name": "Water Inlet System", "subsystem": "Plumbing"},
            {"component_id": f"{pid}-c-drain", "name": "Drain Pump & Hose", "subsystem": "Plumbing"},
            {"component_id": f"{pid}-c-heat", "name": "Heating & Thermistor", "subsystem": "Thermal"},
            {"component_id": f"{pid}-c-spray", "name": "Vario Motor & Spray Arms", "subsystem": "Hydraulic"},
        ],
        symptoms=[
            {"symptom_id": f"{pid}-s01", "description": "Standing water in tub after cycle", "severity": "high"},
            {"symptom_id": f"{pid}-s02", "description": "Dishes not drying; water not heating", "severity": "medium"},
            {"symptom_id": f"{pid}-s03", "description": "AE or E1 leak protection triggered", "severity": "critical"},
            {"symptom_id": f"{pid}-s04", "description": "Long cycle or delayed wash time", "severity": "low"},
        ],
        failure_modes=[
            {
                "failure_mode_id": f"{pid}-fm01",
                "name": "Drain Obstruction / OE Condition",
                "description": "Drain hose kinked, disposal knockout not removed, or pump blocked.",
                "estimated_repair_time_minutes": 45,
                "safety_notes": "Disconnect power before checking drain.",
            },
            {
                "failure_mode_id": f"{pid}-fm02",
                "name": "Inadequate Water Fill / IE Condition",
                "description": "Water valve closed, low pressure <20 PSI, or siphoning drain install.",
                "estimated_repair_time_minutes": 35,
                "safety_notes": "Verify 20-120 PSI water pressure.",
            },
            {
                "failure_mode_id": f"{pid}-fm03",
                "name": "Heater or Thermistor Fault / HE",
                "description": "Heating element open or water overheated above 149°F.",
                "estimated_repair_time_minutes": 75,
                "safety_notes": "Allow cool-down before service.",
            },
            {
                "failure_mode_id": f"{pid}-fm04",
                "name": "Vario Motor / Spray Arm Fault / nE",
                "description": "Spray arm motor or wiring harness issue.",
                "estimated_repair_time_minutes": 90,
                "safety_notes": "Do not run with obstructed spray arms.",
            },
        ],
        diagnostic_steps=[
            {
                "step_id": f"{pid}-d01",
                "description": "Check drain hose for kinks; verify disposal knockout removed.",
                "order": 1,
                "expected_outcome": "Hose clear; not floor-drained",
            },
            {
                "step_id": f"{pid}-d02",
                "description": "Confirm water supply on, 20+ PSI, inlet hose not kinked.",
                "order": 2,
                "expected_outcome": "Adequate fill within 10 minutes",
            },
            {
                "step_id": f"{pid}-d03",
                "description": "Power cycle breaker 10s; rerun cycle to clear HE/PF.",
                "order": 3,
                "expected_outcome": "Heating restores or HE persists",
            },
            {
                "step_id": f"{pid}-d04",
                "description": "Inspect door gasket seal for E1/AE overfill trigger.",
                "order": 4,
                "expected_outcome": "Gasket intact; no obstructions at door",
            },
        ],
        parts=[
            {
                "part_id": f"{pid}-p01",
                "name": "Drain Pump Motor",
                "part_number": "ABQ75742501",
                "estimated_cost_usd": 68.00,
            },
            {
                "part_id": f"{pid}-p02",
                "name": "Inlet Valve Assembly",
                "part_number": "5221DD1001H",
                "estimated_cost_usd": 42.00,
            },
            {
                "part_id": f"{pid}-p03",
                "name": "Heating Element",
                "part_number": "Mee61841401",
                "estimated_cost_usd": 55.00,
            },
            {
                "part_id": f"{pid}-p04",
                "name": "Spray Arm Vario Motor",
                "part_number": "ABQ75742504",
                "estimated_cost_usd": 95.00,
            },
        ],
        symptom_failure_links=[
            {"symptom_id": f"{pid}-s01", "failure_mode_id": f"{pid}-fm01", "confidence": 0.91},
            {"symptom_id": f"{pid}-s02", "failure_mode_id": f"{pid}-fm03", "confidence": 0.89},
            {"symptom_id": f"{pid}-s03", "failure_mode_id": f"{pid}-fm01", "confidence": 0.60},
            {"symptom_id": f"{pid}-s04", "failure_mode_id": f"{pid}-fm02", "confidence": 0.45},
        ],
        failure_mode_part_links=[
            {
                "failure_mode_id": f"{pid}-fm01",
                "part_id": f"{pid}-p01",
                "quantity": 1,
                "probability": 0.88,
                "is_primary": True,
            },
            {
                "failure_mode_id": f"{pid}-fm02",
                "part_id": f"{pid}-p02",
                "quantity": 1,
                "probability": 0.84,
                "is_primary": True,
            },
            {
                "failure_mode_id": f"{pid}-fm03",
                "part_id": f"{pid}-p03",
                "quantity": 1,
                "probability": 0.90,
                "is_primary": True,
            },
            {
                "failure_mode_id": f"{pid}-fm04",
                "part_id": f"{pid}-p04",
                "quantity": 1,
                "probability": 0.87,
                "is_primary": True,
            },
        ],
        failure_mode_component_links=[
            {"failure_mode_id": f"{pid}-fm01", "component_id": f"{pid}-c-drain", "impact_severity": "primary"},
            {"failure_mode_id": f"{pid}-fm02", "component_id": f"{pid}-c-inlet", "impact_severity": "primary"},
            {"failure_mode_id": f"{pid}-fm03", "component_id": f"{pid}-c-heat", "impact_severity": "primary"},
            {"failure_mode_id": f"{pid}-fm04", "component_id": f"{pid}-c-spray", "impact_severity": "primary"},
        ],
        component_part_links=[
            {"component_id": f"{pid}-c-drain", "part_id": f"{pid}-p01"},
            {"component_id": f"{pid}-c-inlet", "part_id": f"{pid}-p02"},
            {"component_id": f"{pid}-c-heat", "part_id": f"{pid}-p03"},
            {"component_id": f"{pid}-c-spray", "part_id": f"{pid}-p04"},
        ],
        error_codes=[
            {
                "error_code_id": f"{pid}-ec-oe",
                "code": "OE",
                "description": "Drain error — hose, pump, or disposal connection",
            },
            {"error_code_id": f"{pid}-ec-ie", "code": "IE", "description": "Water fill insufficient after 10 minutes"},
            {
                "error_code_id": f"{pid}-ec-he",
                "code": "HE",
                "description": "Heater error — element or over-temperature",
            },
            {"error_code_id": f"{pid}-ec-ae", "code": "AE", "description": "Leak / overfill protection activated"},
        ],
        error_code_failure_links=[
            {"error_code_id": f"{pid}-ec-oe", "failure_mode_id": f"{pid}-fm01", "confidence": 0.94},
            {"error_code_id": f"{pid}-ec-ie", "failure_mode_id": f"{pid}-fm02", "confidence": 0.93},
            {"error_code_id": f"{pid}-ec-he", "failure_mode_id": f"{pid}-fm03", "confidence": 0.92},
            {"error_code_id": f"{pid}-ec-ae", "failure_mode_id": f"{pid}-fm01", "confidence": 0.55},
        ],
        diagnostic_step_failure_links=[
            {"step_id": f"{pid}-d01", "failure_mode_id": f"{pid}-fm01", "link_type": "CONFIRMS", "confidence": 0.92},
            {"step_id": f"{pid}-d02", "failure_mode_id": f"{pid}-fm02", "link_type": "CONFIRMS", "confidence": 0.90},
            {"step_id": f"{pid}-d03", "failure_mode_id": f"{pid}-fm03", "link_type": "CONFIRMS", "confidence": 0.85},
            {"step_id": f"{pid}-d04", "failure_mode_id": f"{pid}-fm01", "link_type": "RULES_OUT", "confidence": 0.50},
        ],
        diagnostic_tree_links=[
            {"from_step_id": f"{pid}-d01", "to_step_id": f"{pid}-d02", "condition": "oe_persists"},
            {"from_step_id": f"{pid}-d02", "to_step_id": f"{pid}-d03", "condition": "heating_issue"},
            {"from_step_id": f"{pid}-d03", "to_step_id": f"{pid}-d04", "condition": "ae_or_leak"},
        ],
        oem_sources=[
            "https://www.lg.com/us/support/help-library/lg-dishwasher-error-code-list--20150933422943",
            "https://www.lg.com/us/support/help-library/lg-dishwashers-troubleshooting-an-oe-error-code--1440686618796",
        ],
    )


def whirlpool_wtw5000dw() -> dict:
    pid = "oem-whi-wtw5000"
    return _bp(
        product_id=pid,
        oem="Whirlpool",
        name="Whirlpool WTW5000DW Top Load Washer",
        category="Laundry",
        brand="Whirlpool",
        model_year=2020,
        model_id="mdl-whi-wtw5000",
        model_number="WTW5000DW",
        model_name="Whirlpool 4.3 cu. ft. Top Load Washer",
        sku_id="SKU-WHI-WTW5000-2020",
        components=[
            {"component_id": f"{pid}-c1", "name": "Agitator Drive", "subsystem": "Mechanical"},
            {"component_id": f"{pid}-c2", "name": "Lid Lock Switch", "subsystem": "Safety"},
            {"component_id": f"{pid}-c3", "name": "Drain Pump", "subsystem": "Plumbing"},
        ],
        symptoms=[
            {
                "symptom_id": f"{pid}-s01",
                "description": "Washer fills but will not agitate or spin",
                "severity": "high",
            },
            {
                "symptom_id": f"{pid}-s02",
                "description": "Lid lock flashing; cycle will not start",
                "severity": "medium",
            },
            {"symptom_id": f"{pid}-s03", "description": "F9 E1 drain pump error code", "severity": "high"},
        ],
        failure_modes=[
            {
                "failure_mode_id": f"{pid}-fm01",
                "name": "Shift Actuator Failure",
                "description": "Actuator cannot shift transmission between agitate and spin.",
                "estimated_repair_time_minutes": 60,
                "safety_notes": "Unplug before accessing console.",
            },
            {
                "failure_mode_id": f"{pid}-fm02",
                "name": "Lid Lock Assembly Fault",
                "description": "Lid lock fails to engage preventing cycle start.",
                "estimated_repair_time_minutes": 40,
                "safety_notes": "Do not bypass lid lock.",
            },
            {
                "failure_mode_id": f"{pid}-fm03",
                "name": "Drain Pump Failure",
                "description": "Pump unable to evacuate water; F9 E1 displayed.",
                "estimated_repair_time_minutes": 55,
                "safety_notes": "Check coin trap first.",
            },
        ],
        diagnostic_steps=[
            {
                "step_id": f"{pid}-d01",
                "description": "Run automatic diagnostic mode from console.",
                "order": 1,
                "expected_outcome": "Stored error code retrieved",
            },
            {
                "step_id": f"{pid}-d02",
                "description": "Test lid lock engagement with lid closed.",
                "order": 2,
                "expected_outcome": "Lock clicks; LED stops flashing",
            },
            {
                "step_id": f"{pid}-d03",
                "description": "Inspect coin trap and drain pump for obstruction.",
                "order": 3,
                "expected_outcome": "Pump impeller clear",
            },
        ],
        parts=[
            {
                "part_id": f"{pid}-p01",
                "name": "Shift Actuator",
                "part_number": "W10913953",
                "estimated_cost_usd": 72.00,
            },
            {
                "part_id": f"{pid}-p02",
                "name": "Lid Lock Switch",
                "part_number": "W10810403",
                "estimated_cost_usd": 48.00,
            },
            {"part_id": f"{pid}-p03", "name": "Drain Pump", "part_number": "W10840948", "estimated_cost_usd": 58.00},
        ],
        symptom_failure_links=[
            {"symptom_id": f"{pid}-s01", "failure_mode_id": f"{pid}-fm01", "confidence": 0.90},
            {"symptom_id": f"{pid}-s02", "failure_mode_id": f"{pid}-fm02", "confidence": 0.93},
            {"symptom_id": f"{pid}-s03", "failure_mode_id": f"{pid}-fm03", "confidence": 0.95},
        ],
        failure_mode_part_links=[
            {
                "failure_mode_id": f"{pid}-fm01",
                "part_id": f"{pid}-p01",
                "quantity": 1,
                "probability": 0.91,
                "is_primary": True,
            },
            {
                "failure_mode_id": f"{pid}-fm02",
                "part_id": f"{pid}-p02",
                "quantity": 1,
                "probability": 0.94,
                "is_primary": True,
            },
            {
                "failure_mode_id": f"{pid}-fm03",
                "part_id": f"{pid}-p03",
                "quantity": 1,
                "probability": 0.92,
                "is_primary": True,
            },
        ],
        failure_mode_component_links=[
            {"failure_mode_id": f"{pid}-fm01", "component_id": f"{pid}-c1", "impact_severity": "primary"},
            {"failure_mode_id": f"{pid}-fm02", "component_id": f"{pid}-c2", "impact_severity": "primary"},
            {"failure_mode_id": f"{pid}-fm03", "component_id": f"{pid}-c3", "impact_severity": "primary"},
        ],
        component_part_links=[
            {"component_id": f"{pid}-c1", "part_id": f"{pid}-p01"},
            {"component_id": f"{pid}-c2", "part_id": f"{pid}-p02"},
            {"component_id": f"{pid}-c3", "part_id": f"{pid}-p03"},
        ],
        error_codes=[{"error_code_id": f"{pid}-ec-f9e1", "code": "F9E1", "description": "Drain pump fault"}],
        error_code_failure_links=[
            {"error_code_id": f"{pid}-ec-f9e1", "failure_mode_id": f"{pid}-fm03", "confidence": 0.96},
        ],
        diagnostic_step_failure_links=[
            {"step_id": f"{pid}-d01", "failure_mode_id": f"{pid}-fm01", "link_type": "CONFIRMS", "confidence": 0.80},
            {"step_id": f"{pid}-d02", "failure_mode_id": f"{pid}-fm02", "link_type": "CONFIRMS", "confidence": 0.92},
            {"step_id": f"{pid}-d03", "failure_mode_id": f"{pid}-fm03", "link_type": "CONFIRMS", "confidence": 0.94},
        ],
        diagnostic_tree_links=[
            {"from_step_id": f"{pid}-d01", "to_step_id": f"{pid}-d02", "condition": "lid_lock_symptom"},
            {"from_step_id": f"{pid}-d02", "to_step_id": f"{pid}-d03", "condition": "drain_error"},
        ],
        oem_sources=["https://producthelp.whirlpool.com/Laundry/Washers/Top_Load_Washer"],
    )


def bosch_shpm88z75n() -> dict:
    pid = "oem-bos-shpm88"
    return _bp(
        product_id=pid,
        oem="Bosch",
        name="Bosch SHPM88Z75N 800 Series Dishwasher",
        category="Kitchen",
        brand="Bosch",
        model_year=2023,
        model_id="mdl-bos-shpm88",
        model_number="SHPM88Z75N",
        model_name="Bosch 800 Series Dishwasher",
        sku_id="SKU-BOS-SHPM88-2023",
        components=[
            {"component_id": f"{pid}-c1", "name": "Circulation Pump", "subsystem": "Hydraulic"},
            {"component_id": f"{pid}-c2", "name": "Heat Exchanger", "subsystem": "Thermal"},
            {"component_id": f"{pid}-c3", "name": "AquaStop Inlet", "subsystem": "Plumbing"},
        ],
        symptoms=[
            {"symptom_id": f"{pid}-s01", "description": "E24 drain error on display", "severity": "high"},
            {"symptom_id": f"{pid}-s02", "description": "Dishes not clean; low spray pressure", "severity": "medium"},
            {"symptom_id": f"{pid}-s03", "description": "E01 pump failure code", "severity": "high"},
        ],
        failure_modes=[
            {
                "failure_mode_id": f"{pid}-fm01",
                "name": "Drain Hose Blockage / E24",
                "description": "Blocked drain hose or air gap.",
                "estimated_repair_time_minutes": 35,
                "safety_notes": "Check installation per Bosch spec.",
            },
            {
                "failure_mode_id": f"{pid}-fm02",
                "name": "Circulation Pump Fault / E01",
                "description": "Main circulation pump failure.",
                "estimated_repair_time_minutes": 95,
                "safety_notes": "Authorized service recommended.",
            },
            {
                "failure_mode_id": f"{pid}-fm03",
                "name": "Heat Exchanger Scaling",
                "description": "Hard water scale reducing heat transfer.",
                "estimated_repair_time_minutes": 50,
                "safety_notes": "Recommend descale program.",
            },
        ],
        diagnostic_steps=[
            {
                "step_id": f"{pid}-d01",
                "description": "Verify drain hose loop and air gap per install guide.",
                "order": 1,
                "expected_outcome": "No kinks; proper high loop",
            },
            {
                "step_id": f"{pid}-d02",
                "description": "Run Bosch test program for pump operation.",
                "order": 2,
                "expected_outcome": "Pump runs or E01 logged",
            },
            {
                "step_id": f"{pid}-d03",
                "description": "Inspect heat exchanger and run machine care cycle.",
                "order": 3,
                "expected_outcome": "Scale reduced; heat restored",
            },
        ],
        parts=[
            {"part_id": f"{pid}-p01", "name": "Drain Hose Kit", "part_number": "00611468", "estimated_cost_usd": 28.00},
            {
                "part_id": f"{pid}-p02",
                "name": "Circulation Pump",
                "part_number": "12004119",
                "estimated_cost_usd": 165.00,
            },
            {
                "part_id": f"{pid}-p03",
                "name": "Heat Exchanger",
                "part_number": "12008380",
                "estimated_cost_usd": 120.00,
            },
        ],
        symptom_failure_links=[
            {"symptom_id": f"{pid}-s01", "failure_mode_id": f"{pid}-fm01", "confidence": 0.92},
            {"symptom_id": f"{pid}-s02", "failure_mode_id": f"{pid}-fm02", "confidence": 0.85},
            {"symptom_id": f"{pid}-s03", "failure_mode_id": f"{pid}-fm02", "confidence": 0.94},
        ],
        failure_mode_part_links=[
            {
                "failure_mode_id": f"{pid}-fm01",
                "part_id": f"{pid}-p01",
                "quantity": 1,
                "probability": 0.70,
                "is_primary": True,
            },
            {
                "failure_mode_id": f"{pid}-fm02",
                "part_id": f"{pid}-p02",
                "quantity": 1,
                "probability": 0.93,
                "is_primary": True,
            },
            {
                "failure_mode_id": f"{pid}-fm03",
                "part_id": f"{pid}-p03",
                "quantity": 1,
                "probability": 0.80,
                "is_primary": True,
            },
        ],
        failure_mode_component_links=[
            {"failure_mode_id": f"{pid}-fm01", "component_id": f"{pid}-c3", "impact_severity": "primary"},
            {"failure_mode_id": f"{pid}-fm02", "component_id": f"{pid}-c1", "impact_severity": "primary"},
            {"failure_mode_id": f"{pid}-fm03", "component_id": f"{pid}-c2", "impact_severity": "primary"},
        ],
        component_part_links=[
            {"component_id": f"{pid}-c3", "part_id": f"{pid}-p01"},
            {"component_id": f"{pid}-c1", "part_id": f"{pid}-p02"},
            {"component_id": f"{pid}-c2", "part_id": f"{pid}-p03"},
        ],
        error_codes=[
            {"error_code_id": f"{pid}-ec-e24", "code": "E24", "description": "Drain issue"},
            {"error_code_id": f"{pid}-ec-e01", "code": "E01", "description": "Pump failure"},
        ],
        error_code_failure_links=[
            {"error_code_id": f"{pid}-ec-e24", "failure_mode_id": f"{pid}-fm01", "confidence": 0.95},
            {"error_code_id": f"{pid}-ec-e01", "failure_mode_id": f"{pid}-fm02", "confidence": 0.96},
        ],
        diagnostic_step_failure_links=[
            {"step_id": f"{pid}-d01", "failure_mode_id": f"{pid}-fm01", "link_type": "CONFIRMS", "confidence": 0.90},
            {"step_id": f"{pid}-d02", "failure_mode_id": f"{pid}-fm02", "link_type": "CONFIRMS", "confidence": 0.93},
            {"step_id": f"{pid}-d03", "failure_mode_id": f"{pid}-fm03", "link_type": "CONFIRMS", "confidence": 0.82},
        ],
        diagnostic_tree_links=[
            {"from_step_id": f"{pid}-d01", "to_step_id": f"{pid}-d02", "condition": "e24_cleared_poor_wash"},
            {"from_step_id": f"{pid}-d02", "to_step_id": f"{pid}-d03", "condition": "heat_or_dry_issue"},
        ],
        oem_sources=["https://www.bosch-home.com/us/support"],
    )


def ge_jvm3160rfss() -> dict:
    pid = "oem-ge-jvm3160"
    return _bp(
        product_id=pid,
        oem="GE Appliances",
        name="GE JVM3160RFSS Over-the-Range Microwave",
        category="Kitchen",
        brand="GE",
        model_year=2021,
        model_id="mdl-ge-jvm3160",
        model_number="JVM3160RFSS",
        model_name="GE 1.6 cu. ft. OTR Microwave",
        sku_id="SKU-GE-JVM3160-2021",
        components=[
            {"component_id": f"{pid}-c1", "name": "Magnetron & HV Circuit", "subsystem": "RF"},
            {"component_id": f"{pid}-c2", "name": "Door Switch Interlock", "subsystem": "Safety"},
            {"component_id": f"{pid}-c3", "name": "Turntable Drive Motor", "subsystem": "Mechanical"},
        ],
        symptoms=[
            {
                "symptom_id": f"{pid}-s01",
                "description": "Microwave runs but does not heat food",
                "severity": "critical",
            },
            {
                "symptom_id": f"{pid}-s02",
                "description": "Door error or won't start when door closed",
                "severity": "high",
            },
            {"symptom_id": f"{pid}-s03", "description": "Turntable not rotating", "severity": "low"},
        ],
        failure_modes=[
            {
                "failure_mode_id": f"{pid}-fm01",
                "name": "Magnetron or HV Diode Failure",
                "description": "No microwave energy produced.",
                "estimated_repair_time_minutes": 110,
                "safety_notes": "HV capacitor discharge required.",
            },
            {
                "failure_mode_id": f"{pid}-fm02",
                "name": "Door Switch Interlock Fault",
                "description": "Primary or monitor switch fails continuity.",
                "estimated_repair_time_minutes": 45,
                "safety_notes": "Do not operate with faulty interlock.",
            },
            {
                "failure_mode_id": f"{pid}-fm03",
                "name": "Turntable Motor Failure",
                "description": "Coupler or motor not driving turntable.",
                "estimated_repair_time_minutes": 35,
                "safety_notes": "Check coupler alignment first.",
            },
        ],
        diagnostic_steps=[
            {
                "step_id": f"{pid}-d01",
                "description": "Heat 1 cup water 60 seconds; measure temperature rise.",
                "order": 1,
                "expected_outcome": "<5°F rise indicates no RF heating",
            },
            {
                "step_id": f"{pid}-d02",
                "description": "Test door switch continuity with multimeter.",
                "order": 2,
                "expected_outcome": "Switch opens/closes with door",
            },
            {
                "step_id": f"{pid}-d03",
                "description": "Inspect turntable coupler and motor shaft.",
                "order": 3,
                "expected_outcome": "Coupler seated; motor shaft turns",
            },
        ],
        parts=[
            {
                "part_id": f"{pid}-p01",
                "name": "Magnetron Assembly",
                "part_number": "WB27X11213",
                "estimated_cost_usd": 105.00,
            },
            {
                "part_id": f"{pid}-p02",
                "name": "Door Switch Kit",
                "part_number": "WB24X829",
                "estimated_cost_usd": 38.00,
            },
            {
                "part_id": f"{pid}-p03",
                "name": "Turntable Motor",
                "part_number": "WB26X10038",
                "estimated_cost_usd": 22.00,
            },
        ],
        symptom_failure_links=[
            {"symptom_id": f"{pid}-s01", "failure_mode_id": f"{pid}-fm01", "confidence": 0.94},
            {"symptom_id": f"{pid}-s02", "failure_mode_id": f"{pid}-fm02", "confidence": 0.91},
            {"symptom_id": f"{pid}-s03", "failure_mode_id": f"{pid}-fm03", "confidence": 0.88},
        ],
        failure_mode_part_links=[
            {
                "failure_mode_id": f"{pid}-fm01",
                "part_id": f"{pid}-p01",
                "quantity": 1,
                "probability": 0.90,
                "is_primary": True,
            },
            {
                "failure_mode_id": f"{pid}-fm02",
                "part_id": f"{pid}-p02",
                "quantity": 1,
                "probability": 0.93,
                "is_primary": True,
            },
            {
                "failure_mode_id": f"{pid}-fm03",
                "part_id": f"{pid}-p03",
                "quantity": 1,
                "probability": 0.85,
                "is_primary": True,
            },
        ],
        failure_mode_component_links=[
            {"failure_mode_id": f"{pid}-fm01", "component_id": f"{pid}-c1", "impact_severity": "primary"},
            {"failure_mode_id": f"{pid}-fm02", "component_id": f"{pid}-c2", "impact_severity": "primary"},
            {"failure_mode_id": f"{pid}-fm03", "component_id": f"{pid}-c3", "impact_severity": "primary"},
        ],
        component_part_links=[
            {"component_id": f"{pid}-c1", "part_id": f"{pid}-p01"},
            {"component_id": f"{pid}-c2", "part_id": f"{pid}-p02"},
            {"component_id": f"{pid}-c3", "part_id": f"{pid}-p03"},
        ],
        error_codes=[],
        error_code_failure_links=[],
        diagnostic_step_failure_links=[
            {"step_id": f"{pid}-d01", "failure_mode_id": f"{pid}-fm01", "link_type": "CONFIRMS", "confidence": 0.95},
            {"step_id": f"{pid}-d02", "failure_mode_id": f"{pid}-fm02", "link_type": "CONFIRMS", "confidence": 0.92},
            {"step_id": f"{pid}-d03", "failure_mode_id": f"{pid}-fm03", "link_type": "CONFIRMS", "confidence": 0.88},
        ],
        diagnostic_tree_links=[
            {"from_step_id": f"{pid}-d01", "to_step_id": f"{pid}-d02", "condition": "no_start"},
            {"from_step_id": f"{pid}-d02", "to_step_id": f"{pid}-d03", "condition": "turntable_issue"},
        ],
        oem_sources=["https://www.geappliances.com/ge/service-and-support.htm"],
    )


def samsung_rf28r7351sg() -> dict:
    pid = "oem-sam-rf28"
    return _bp(
        product_id=pid,
        oem="Samsung",
        name="Samsung RF28R7351SG French Door Refrigerator",
        category="Refrigeration",
        brand="Samsung",
        model_year=2021,
        model_id="mdl-sam-rf28",
        model_number="RF28R7351SG",
        model_name="Samsung 28 cu. ft. French Door Refrigerator",
        sku_id="SKU-SAM-RF28-2021",
        components=[
            {"component_id": f"{pid}-c1", "name": "Evaporator Fan Motor", "subsystem": "Cooling"},
            {"component_id": f"{pid}-c2", "name": "Ice Maker Assembly", "subsystem": "Ice/Water"},
            {"component_id": f"{pid}-c3", "name": "Defrost System", "subsystem": "Thermal"},
        ],
        symptoms=[
            {
                "symptom_id": f"{pid}-s01",
                "description": "Refrigerator section not cooling; freezer OK",
                "severity": "high",
            },
            {"symptom_id": f"{pid}-s02", "description": "22E error — evaporator fan fault", "severity": "high"},
            {"symptom_id": f"{pid}-s03", "description": "33E error — ice maker fan fault", "severity": "medium"},
            {"symptom_id": f"{pid}-s04", "description": "Excessive frost in freezer compartment", "severity": "medium"},
        ],
        failure_modes=[
            {
                "failure_mode_id": f"{pid}-fm01",
                "name": "Evaporator Fan Motor Failure / 22E",
                "description": "Fan motor not circulating cold air to refrigerator section.",
                "estimated_repair_time_minutes": 75,
                "safety_notes": "Unplug before accessing evaporator cover.",
            },
            {
                "failure_mode_id": f"{pid}-fm02",
                "name": "Ice Maker Fan or Duct Blockage / 33E",
                "description": "Ice room fan blocked by frost or motor failure.",
                "estimated_repair_time_minutes": 60,
                "safety_notes": "Allow manual defrost if heavily iced.",
            },
            {
                "failure_mode_id": f"{pid}-fm03",
                "name": "Defrost Heater or Bi-Metal Failure",
                "description": "Defrost cycle not clearing evaporator frost buildup.",
                "estimated_repair_time_minutes": 90,
                "safety_notes": "Extended defrost may be required before test.",
            },
        ],
        diagnostic_steps=[
            {
                "step_id": f"{pid}-d01",
                "description": "Verify condenser coils clean and doors seal properly.",
                "order": 1,
                "expected_outcome": "Coils clear; gaskets intact",
            },
            {
                "step_id": f"{pid}-d02",
                "description": "Remove evaporator cover; test fan motor for obstruction/spin.",
                "order": 2,
                "expected_outcome": "Fan spins freely or 22E confirmed",
            },
            {
                "step_id": f"{pid}-d03",
                "description": "Inspect ice maker fan duct for ice blockage.",
                "order": 3,
                "expected_outcome": "Duct clear or 33E persists",
            },
            {
                "step_id": f"{pid}-d04",
                "description": "Force defrost mode; check heater continuity.",
                "order": 4,
                "expected_outcome": "Frost melts; heater shows continuity",
            },
        ],
        parts=[
            {
                "part_id": f"{pid}-p01",
                "name": "Evaporator Fan Motor",
                "part_number": "DA97-17376A",
                "estimated_cost_usd": 89.00,
            },
            {
                "part_id": f"{pid}-p02",
                "name": "Ice Maker Fan Motor",
                "part_number": "DA97-15217D",
                "estimated_cost_usd": 72.00,
            },
            {
                "part_id": f"{pid}-p03",
                "name": "Defrost Heater Assembly",
                "part_number": "DA47-00244U",
                "estimated_cost_usd": 48.00,
            },
        ],
        symptom_failure_links=[
            {"symptom_id": f"{pid}-s01", "failure_mode_id": f"{pid}-fm01", "confidence": 0.88},
            {"symptom_id": f"{pid}-s02", "failure_mode_id": f"{pid}-fm01", "confidence": 0.95},
            {"symptom_id": f"{pid}-s03", "failure_mode_id": f"{pid}-fm02", "confidence": 0.94},
            {"symptom_id": f"{pid}-s04", "failure_mode_id": f"{pid}-fm03", "confidence": 0.86},
        ],
        failure_mode_part_links=[
            {
                "failure_mode_id": f"{pid}-fm01",
                "part_id": f"{pid}-p01",
                "quantity": 1,
                "probability": 0.91,
                "is_primary": True,
            },
            {
                "failure_mode_id": f"{pid}-fm02",
                "part_id": f"{pid}-p02",
                "quantity": 1,
                "probability": 0.88,
                "is_primary": True,
            },
            {
                "failure_mode_id": f"{pid}-fm03",
                "part_id": f"{pid}-p03",
                "quantity": 1,
                "probability": 0.85,
                "is_primary": True,
            },
        ],
        failure_mode_component_links=[
            {"failure_mode_id": f"{pid}-fm01", "component_id": f"{pid}-c1", "impact_severity": "primary"},
            {"failure_mode_id": f"{pid}-fm02", "component_id": f"{pid}-c2", "impact_severity": "primary"},
            {"failure_mode_id": f"{pid}-fm03", "component_id": f"{pid}-c3", "impact_severity": "primary"},
        ],
        component_part_links=[
            {"component_id": f"{pid}-c1", "part_id": f"{pid}-p01"},
            {"component_id": f"{pid}-c2", "part_id": f"{pid}-p02"},
            {"component_id": f"{pid}-c3", "part_id": f"{pid}-p03"},
        ],
        error_codes=[
            {"error_code_id": f"{pid}-ec-22e", "code": "22E", "description": "Evaporator fan error"},
            {"error_code_id": f"{pid}-ec-33e", "code": "33E", "description": "Ice maker fan error"},
            {"error_code_id": f"{pid}-ec-39e", "code": "39E", "description": "Ice maker function error"},
        ],
        error_code_failure_links=[
            {"error_code_id": f"{pid}-ec-22e", "failure_mode_id": f"{pid}-fm01", "confidence": 0.96},
            {"error_code_id": f"{pid}-ec-33e", "failure_mode_id": f"{pid}-fm02", "confidence": 0.95},
            {"error_code_id": f"{pid}-ec-39e", "failure_mode_id": f"{pid}-fm02", "confidence": 0.70},
        ],
        diagnostic_step_failure_links=[
            {"step_id": f"{pid}-d02", "failure_mode_id": f"{pid}-fm01", "link_type": "CONFIRMS", "confidence": 0.93},
            {"step_id": f"{pid}-d03", "failure_mode_id": f"{pid}-fm02", "link_type": "CONFIRMS", "confidence": 0.90},
            {"step_id": f"{pid}-d04", "failure_mode_id": f"{pid}-fm03", "link_type": "CONFIRMS", "confidence": 0.87},
        ],
        diagnostic_tree_links=[
            {"from_step_id": f"{pid}-d01", "to_step_id": f"{pid}-d02", "condition": "warm_fridge_section"},
            {"from_step_id": f"{pid}-d02", "to_step_id": f"{pid}-d03", "condition": "33e_or_ice_room"},
            {"from_step_id": f"{pid}-d03", "to_step_id": f"{pid}-d04", "condition": "heavy_frost"},
        ],
        oem_sources=[
            "https://www.samsung.com/us/support/troubleshoot/TSG10007315/",
            "https://www.partselect.com/blog/samsung-refrigerator-22E-error-code/",
        ],
    )


def lg_dle3400w() -> dict:
    pid = "oem-lg-dle3400"
    return _bp(
        product_id=pid,
        oem="LG",
        name="LG DLE3400W Electric Dryer",
        category="Laundry",
        brand="LG",
        model_year=2022,
        model_id="mdl-lg-dle3400",
        model_number="DLE3400W",
        model_name="LG 7.4 cu. ft. Ultra Large Capacity Dryer",
        sku_id="SKU-LG-DLE3400-2022",
        components=[
            {"component_id": f"{pid}-c1", "name": "Exhaust Ventilation System", "subsystem": "Airflow"},
            {"component_id": f"{pid}-c2", "name": "Flow Sensor & Ducting", "subsystem": "Sensing"},
            {"component_id": f"{pid}-c3", "name": "Heating Element Circuit", "subsystem": "Thermal"},
        ],
        symptoms=[
            {"symptom_id": f"{pid}-s01", "description": "Clothes still damp after full cycle", "severity": "medium"},
            {"symptom_id": f"{pid}-s02", "description": "d80 error — 80% vent blockage detected", "severity": "high"},
            {
                "symptom_id": f"{pid}-s03",
                "description": "d90 or d95 error — severe vent restriction",
                "severity": "high",
            },
            {"symptom_id": f"{pid}-s04", "description": "Dryer runs but no heat produced", "severity": "high"},
        ],
        failure_modes=[
            {
                "failure_mode_id": f"{pid}-fm01",
                "name": "Restricted Exhaust Duct / d80-d95",
                "description": "Lint buildup in duct or external vent hood blocked.",
                "estimated_repair_time_minutes": 45,
                "safety_notes": "Clean lint filter and full duct run.",
            },
            {
                "failure_mode_id": f"{pid}-fm02",
                "name": "Flow Sensor Fault",
                "description": "Sensor reports false restriction or failed reading.",
                "estimated_repair_time_minutes": 55,
                "safety_notes": "Verify duct is clear before replacing sensor.",
            },
            {
                "failure_mode_id": f"{pid}-fm03",
                "name": "Heating Element or Thermostat Failure",
                "description": "Open heating element or high-limit thermostat tripped.",
                "estimated_repair_time_minutes": 70,
                "safety_notes": "Disconnect power; test element continuity.",
            },
        ],
        diagnostic_steps=[
            {
                "step_id": f"{pid}-d01",
                "description": "Clean lint filter and inspect external vent hood flap opens.",
                "order": 1,
                "expected_outcome": "Strong airflow at vent outlet",
            },
            {
                "step_id": f"{pid}-d02",
                "description": "Run duct blockage test; measure exhaust run length (<60 ft equivalent).",
                "order": 2,
                "expected_outcome": "d80 clears or duct restriction found",
            },
            {
                "step_id": f"{pid}-d03",
                "description": "Inspect flow sensor harness and sensor port for lint packing.",
                "order": 3,
                "expected_outcome": "Sensor reads correctly after cleaning",
            },
            {
                "step_id": f"{pid}-d04",
                "description": "Test heating element and thermostat with multimeter.",
                "order": 4,
                "expected_outcome": "Element continuity OK or open circuit found",
            },
        ],
        parts=[
            {
                "part_id": f"{pid}-p01",
                "name": "Flexible Vent Duct Kit",
                "part_number": "5215EL2002A",
                "estimated_cost_usd": 35.00,
            },
            {
                "part_id": f"{pid}-p02",
                "name": "Flow Sensor Assembly",
                "part_number": "6500EL2001A",
                "estimated_cost_usd": 42.00,
            },
            {
                "part_id": f"{pid}-p03",
                "name": "Heating Element",
                "part_number": "5301EL1001J",
                "estimated_cost_usd": 58.00,
            },
        ],
        symptom_failure_links=[
            {"symptom_id": f"{pid}-s01", "failure_mode_id": f"{pid}-fm01", "confidence": 0.82},
            {"symptom_id": f"{pid}-s02", "failure_mode_id": f"{pid}-fm01", "confidence": 0.93},
            {"symptom_id": f"{pid}-s03", "failure_mode_id": f"{pid}-fm01", "confidence": 0.96},
            {"symptom_id": f"{pid}-s04", "failure_mode_id": f"{pid}-fm03", "confidence": 0.90},
        ],
        failure_mode_part_links=[
            {
                "failure_mode_id": f"{pid}-fm01",
                "part_id": f"{pid}-p01",
                "quantity": 1,
                "probability": 0.75,
                "is_primary": True,
            },
            {
                "failure_mode_id": f"{pid}-fm02",
                "part_id": f"{pid}-p02",
                "quantity": 1,
                "probability": 0.88,
                "is_primary": True,
            },
            {
                "failure_mode_id": f"{pid}-fm03",
                "part_id": f"{pid}-p03",
                "quantity": 1,
                "probability": 0.92,
                "is_primary": True,
            },
        ],
        failure_mode_component_links=[
            {"failure_mode_id": f"{pid}-fm01", "component_id": f"{pid}-c1", "impact_severity": "primary"},
            {"failure_mode_id": f"{pid}-fm02", "component_id": f"{pid}-c2", "impact_severity": "primary"},
            {"failure_mode_id": f"{pid}-fm03", "component_id": f"{pid}-c3", "impact_severity": "primary"},
        ],
        component_part_links=[
            {"component_id": f"{pid}-c1", "part_id": f"{pid}-p01"},
            {"component_id": f"{pid}-c2", "part_id": f"{pid}-p02"},
            {"component_id": f"{pid}-c3", "part_id": f"{pid}-p03"},
        ],
        error_codes=[
            {"error_code_id": f"{pid}-ec-d80", "code": "d80", "description": "80% exhaust blockage"},
            {"error_code_id": f"{pid}-ec-d90", "code": "d90", "description": "90% exhaust blockage"},
            {"error_code_id": f"{pid}-ec-d95", "code": "d95", "description": "95% exhaust blockage"},
        ],
        error_code_failure_links=[
            {"error_code_id": f"{pid}-ec-d80", "failure_mode_id": f"{pid}-fm01", "confidence": 0.90},
            {"error_code_id": f"{pid}-ec-d90", "failure_mode_id": f"{pid}-fm01", "confidence": 0.94},
            {"error_code_id": f"{pid}-ec-d95", "failure_mode_id": f"{pid}-fm01", "confidence": 0.97},
        ],
        diagnostic_step_failure_links=[
            {"step_id": f"{pid}-d01", "failure_mode_id": f"{pid}-fm01", "link_type": "CONFIRMS", "confidence": 0.85},
            {"step_id": f"{pid}-d02", "failure_mode_id": f"{pid}-fm01", "link_type": "CONFIRMS", "confidence": 0.92},
            {"step_id": f"{pid}-d03", "failure_mode_id": f"{pid}-fm02", "link_type": "CONFIRMS", "confidence": 0.88},
            {"step_id": f"{pid}-d04", "failure_mode_id": f"{pid}-fm03", "link_type": "CONFIRMS", "confidence": 0.91},
        ],
        diagnostic_tree_links=[
            {"from_step_id": f"{pid}-d01", "to_step_id": f"{pid}-d02", "condition": "d80_d90_d95"},
            {"from_step_id": f"{pid}-d02", "to_step_id": f"{pid}-d03", "condition": "duct_clear_code_persists"},
            {"from_step_id": f"{pid}-d03", "to_step_id": f"{pid}-d04", "condition": "no_heat"},
        ],
        oem_sources=[
            "https://www.lg.com/us/support/help-library/lg-dryer-error-code-list--20152310891742",
            "https://www.lg.com/us/support/help-library/lg-dryer-understanding-d90-and-d95-error-codes--20150209089448",
        ],
    )


def whirlpool_wfg505m0bs() -> dict:
    pid = "oem-whi-wfg505"
    return _bp(
        product_id=pid,
        oem="Whirlpool",
        name="Whirlpool WFG505M0BS Gas Range",
        category="Cooking",
        brand="Whirlpool",
        model_year=2023,
        model_id="mdl-whi-wfg505",
        model_number="WFG505M0BS",
        model_name="Whirlpool 5.0 cu. ft. Gas Range",
        sku_id="SKU-WHI-WFG505-2023",
        components=[
            {"component_id": f"{pid}-c1", "name": "Bake Igniter System", "subsystem": "Gas Ignition"},
            {"component_id": f"{pid}-c2", "name": "Surface Burner Valves", "subsystem": "Gas Delivery"},
            {"component_id": f"{pid}-c3", "name": "Oven Temperature Sensor", "subsystem": "Sensing"},
        ],
        symptoms=[
            {
                "symptom_id": f"{pid}-s01",
                "description": "Oven ignites but won't stay lit or won't heat",
                "severity": "high",
            },
            {
                "symptom_id": f"{pid}-s02",
                "description": "Gas smell when oven on; weak ignition",
                "severity": "critical",
            },
            {
                "symptom_id": f"{pid}-s03",
                "description": "F9 E0 error — oven temperature sensor fault",
                "severity": "medium",
            },
            {
                "symptom_id": f"{pid}-s04",
                "description": "Surface burner won't light; clicking only",
                "severity": "medium",
            },
        ],
        failure_modes=[
            {
                "failure_mode_id": f"{pid}-fm01",
                "name": "Weak or Failed Bake Igniter",
                "description": "Igniter glows insufficiently to open gas valve.",
                "estimated_repair_time_minutes": 50,
                "safety_notes": "Shut gas supply before service.",
            },
            {
                "failure_mode_id": f"{pid}-fm02",
                "name": "Gas Valve or Safety Valve Fault",
                "description": "Valve does not open after igniter sequence.",
                "estimated_repair_time_minutes": 80,
                "safety_notes": "Licensed gas technician required.",
            },
            {
                "failure_mode_id": f"{pid}-fm03",
                "name": "Oven Temperature Sensor Out of Range",
                "description": "RTD sensor reading triggers F9 E0.",
                "estimated_repair_time_minutes": 40,
                "safety_notes": "Disconnect power before sensor swap.",
            },
            {
                "failure_mode_id": f"{pid}-fm04",
                "name": "Surface Igniter Electrode Fault",
                "description": "Spark electrode worn or misaligned on burner.",
                "estimated_repair_time_minutes": 35,
                "safety_notes": "Ensure burner caps seated correctly.",
            },
        ],
        diagnostic_steps=[
            {
                "step_id": f"{pid}-d01",
                "description": "Observe bake igniter glow amp draw during ignition sequence.",
                "order": 1,
                "expected_outcome": "3.2-3.6A required to open valve",
            },
            {
                "step_id": f"{pid}-d02",
                "description": "Test oven temperature sensor resistance at room temp (~1080 ohms).",
                "order": 2,
                "expected_outcome": "Within spec or F9 E0 confirmed",
            },
            {
                "step_id": f"{pid}-d03",
                "description": "Inspect surface burner caps, ports, and spark electrode gap.",
                "order": 3,
                "expected_outcome": "Blue spark; burner lights",
            },
            {
                "step_id": f"{pid}-d04",
                "description": "If igniter weak, replace igniter before gas valve.",
                "order": 4,
                "expected_outcome": "Oven lights and holds flame",
            },
        ],
        parts=[
            {"part_id": f"{pid}-p01", "name": "Bake Igniter", "part_number": "W10918546", "estimated_cost_usd": 52.00},
            {
                "part_id": f"{pid}-p02",
                "name": "Oven Safety Valve",
                "part_number": "W10861612",
                "estimated_cost_usd": 95.00,
            },
            {
                "part_id": f"{pid}-p03",
                "name": "Temperature Sensor W10181986",
                "part_number": "W10181986",
                "estimated_cost_usd": 28.00,
            },
            {
                "part_id": f"{pid}-p04",
                "name": "Surface Burner Spark Electrode",
                "part_number": "W11176400",
                "estimated_cost_usd": 22.00,
            },
        ],
        symptom_failure_links=[
            {"symptom_id": f"{pid}-s01", "failure_mode_id": f"{pid}-fm01", "confidence": 0.91},
            {"symptom_id": f"{pid}-s02", "failure_mode_id": f"{pid}-fm02", "confidence": 0.75},
            {"symptom_id": f"{pid}-s03", "failure_mode_id": f"{pid}-fm03", "confidence": 0.94},
            {"symptom_id": f"{pid}-s04", "failure_mode_id": f"{pid}-fm04", "confidence": 0.89},
        ],
        failure_mode_part_links=[
            {
                "failure_mode_id": f"{pid}-fm01",
                "part_id": f"{pid}-p01",
                "quantity": 1,
                "probability": 0.93,
                "is_primary": True,
            },
            {
                "failure_mode_id": f"{pid}-fm02",
                "part_id": f"{pid}-p02",
                "quantity": 1,
                "probability": 0.80,
                "is_primary": True,
            },
            {
                "failure_mode_id": f"{pid}-fm03",
                "part_id": f"{pid}-p03",
                "quantity": 1,
                "probability": 0.95,
                "is_primary": True,
            },
            {
                "failure_mode_id": f"{pid}-fm04",
                "part_id": f"{pid}-p04",
                "quantity": 1,
                "probability": 0.88,
                "is_primary": True,
            },
        ],
        failure_mode_component_links=[
            {"failure_mode_id": f"{pid}-fm01", "component_id": f"{pid}-c1", "impact_severity": "primary"},
            {"failure_mode_id": f"{pid}-fm02", "component_id": f"{pid}-c1", "impact_severity": "primary"},
            {"failure_mode_id": f"{pid}-fm03", "component_id": f"{pid}-c3", "impact_severity": "primary"},
            {"failure_mode_id": f"{pid}-fm04", "component_id": f"{pid}-c2", "impact_severity": "primary"},
        ],
        component_part_links=[
            {"component_id": f"{pid}-c1", "part_id": f"{pid}-p01"},
            {"component_id": f"{pid}-c1", "part_id": f"{pid}-p02"},
            {"component_id": f"{pid}-c3", "part_id": f"{pid}-p03"},
            {"component_id": f"{pid}-c2", "part_id": f"{pid}-p04"},
        ],
        error_codes=[
            {"error_code_id": f"{pid}-ec-f9e0", "code": "F9E0", "description": "Oven temperature sensor fault"},
        ],
        error_code_failure_links=[
            {"error_code_id": f"{pid}-ec-f9e0", "failure_mode_id": f"{pid}-fm03", "confidence": 0.96},
        ],
        diagnostic_step_failure_links=[
            {"step_id": f"{pid}-d01", "failure_mode_id": f"{pid}-fm01", "link_type": "CONFIRMS", "confidence": 0.92},
            {"step_id": f"{pid}-d02", "failure_mode_id": f"{pid}-fm03", "link_type": "CONFIRMS", "confidence": 0.94},
            {"step_id": f"{pid}-d03", "failure_mode_id": f"{pid}-fm04", "link_type": "CONFIRMS", "confidence": 0.90},
            {"step_id": f"{pid}-d04", "failure_mode_id": f"{pid}-fm01", "link_type": "CONFIRMS", "confidence": 0.88},
        ],
        diagnostic_tree_links=[
            {"from_step_id": f"{pid}-d01", "to_step_id": f"{pid}-d02", "condition": "f9e0_displayed"},
            {"from_step_id": f"{pid}-d01", "to_step_id": f"{pid}-d04", "condition": "weak_glow"},
            {"from_step_id": f"{pid}-d02", "to_step_id": f"{pid}-d03", "condition": "surface_burner_issue"},
        ],
        oem_sources=["https://producthelp.whirlpool.com/Cooking/Ranges"],
    )


def samsung_dw80b7070us() -> dict:
    pid = "oem-sam-dw80"
    return _bp(
        product_id=pid,
        oem="Samsung",
        name="Samsung DW80B7070US Smart Dishwasher",
        category="Kitchen",
        brand="Samsung",
        model_year=2023,
        model_id="mdl-sam-dw80",
        model_number="DW80B7070US",
        model_name="Samsung Bespoke 24in Dishwasher",
        sku_id="SKU-SAM-DW80-2023",
        components=[
            {"component_id": f"{pid}-c1", "name": "Drain & Sump System", "subsystem": "Plumbing"},
            {"component_id": f"{pid}-c2", "name": "WaterWall Spray System", "subsystem": "Hydraulic"},
            {"component_id": f"{pid}-c3", "name": "Heating & Drying", "subsystem": "Thermal"},
        ],
        symptoms=[
            {"symptom_id": f"{pid}-s01", "description": "LC or LE leak error code displayed", "severity": "critical"},
            {"symptom_id": f"{pid}-s02", "description": "Dishes not clean; low water spray", "severity": "medium"},
            {"symptom_id": f"{pid}-s03", "description": "OC or 0C over-level water error", "severity": "high"},
        ],
        failure_modes=[
            {
                "failure_mode_id": f"{pid}-fm01",
                "name": "Drain Hose / Sump Obstruction",
                "description": "Food debris blocking drain path or check valve.",
                "estimated_repair_time_minutes": 40,
                "safety_notes": "Disconnect power; towel sump area.",
            },
            {
                "failure_mode_id": f"{pid}-fm02",
                "name": "WaterWall Motor or Track Fault",
                "description": "Spray arm not traversing tub length.",
                "estimated_repair_time_minutes": 85,
                "safety_notes": "Check for obstructions on track.",
            },
            {
                "failure_mode_id": f"{pid}-fm03",
                "name": "Inlet Valve Overfill / LC Leak",
                "description": "Inlet valve stuck open or float leak sensor wet.",
                "estimated_repair_time_minutes": 65,
                "safety_notes": "Shut water supply immediately on LC.",
            },
        ],
        diagnostic_steps=[
            {
                "step_id": f"{pid}-d01",
                "description": "Inspect drain hose and remove sump filter debris.",
                "order": 1,
                "expected_outcome": "Drain completes without OC",
            },
            {
                "step_id": f"{pid}-d02",
                "description": "Verify WaterWall arm moves freely full stroke.",
                "order": 2,
                "expected_outcome": "Arm traverses; no grinding",
            },
            {
                "step_id": f"{pid}-d03",
                "description": "Dry leak sensor in pan; test inlet valve shuts off.",
                "order": 3,
                "expected_outcome": "LC clears after dry",
            },
        ],
        parts=[
            {"part_id": f"{pid}-p01", "name": "Drain Pump", "part_number": "DD81-02655A", "estimated_cost_usd": 72.00},
            {
                "part_id": f"{pid}-p02",
                "name": "WaterWall Vane Motor",
                "part_number": "DD82-01315A",
                "estimated_cost_usd": 125.00,
            },
            {
                "part_id": f"{pid}-p03",
                "name": "Water Inlet Valve",
                "part_number": "DD62-00084A",
                "estimated_cost_usd": 48.00,
            },
        ],
        symptom_failure_links=[
            {"symptom_id": f"{pid}-s01", "failure_mode_id": f"{pid}-fm03", "confidence": 0.88},
            {"symptom_id": f"{pid}-s02", "failure_mode_id": f"{pid}-fm02", "confidence": 0.87},
            {"symptom_id": f"{pid}-s03", "failure_mode_id": f"{pid}-fm01", "confidence": 0.91},
        ],
        failure_mode_part_links=[
            {
                "failure_mode_id": f"{pid}-fm01",
                "part_id": f"{pid}-p01",
                "quantity": 1,
                "probability": 0.86,
                "is_primary": True,
            },
            {
                "failure_mode_id": f"{pid}-fm02",
                "part_id": f"{pid}-p02",
                "quantity": 1,
                "probability": 0.90,
                "is_primary": True,
            },
            {
                "failure_mode_id": f"{pid}-fm03",
                "part_id": f"{pid}-p03",
                "quantity": 1,
                "probability": 0.84,
                "is_primary": True,
            },
        ],
        failure_mode_component_links=[
            {"failure_mode_id": f"{pid}-fm01", "component_id": f"{pid}-c1", "impact_severity": "primary"},
            {"failure_mode_id": f"{pid}-fm02", "component_id": f"{pid}-c2", "impact_severity": "primary"},
            {"failure_mode_id": f"{pid}-fm03", "component_id": f"{pid}-c3", "impact_severity": "primary"},
        ],
        component_part_links=[
            {"component_id": f"{pid}-c1", "part_id": f"{pid}-p01"},
            {"component_id": f"{pid}-c2", "part_id": f"{pid}-p02"},
            {"component_id": f"{pid}-c3", "part_id": f"{pid}-p03"},
        ],
        error_codes=[
            {"error_code_id": f"{pid}-ec-lc", "code": "LC", "description": "Leak detected"},
            {"error_code_id": f"{pid}-ec-oc", "code": "OC", "description": "Over-level water check"},
        ],
        error_code_failure_links=[
            {"error_code_id": f"{pid}-ec-lc", "failure_mode_id": f"{pid}-fm03", "confidence": 0.92},
            {"error_code_id": f"{pid}-ec-oc", "failure_mode_id": f"{pid}-fm01", "confidence": 0.90},
        ],
        diagnostic_step_failure_links=[
            {"step_id": f"{pid}-d01", "failure_mode_id": f"{pid}-fm01", "link_type": "CONFIRMS", "confidence": 0.91},
            {"step_id": f"{pid}-d02", "failure_mode_id": f"{pid}-fm02", "link_type": "CONFIRMS", "confidence": 0.89},
            {"step_id": f"{pid}-d03", "failure_mode_id": f"{pid}-fm03", "link_type": "CONFIRMS", "confidence": 0.87},
        ],
        diagnostic_tree_links=[
            {"from_step_id": f"{pid}-d01", "to_step_id": f"{pid}-d02", "condition": "poor_wash"},
            {"from_step_id": f"{pid}-d01", "to_step_id": f"{pid}-d03", "condition": "lc_leak"},
        ],
        oem_sources=["https://www.samsung.com/us/support/home-appliances/dishwashers/"],
    )


def lg_wm4000hwa() -> dict:
    pid = "oem-lg-wm4000"
    return _bp(
        product_id=pid,
        oem="LG",
        name="LG WM4000HWA Front Load Washer",
        category="Laundry",
        brand="LG",
        model_year=2022,
        model_id="mdl-lg-wm4000",
        model_number="WM4000HWA",
        model_name="LG 4.5 cu. ft. Ultra Large Smart Washer",
        sku_id="SKU-LG-WM4000-2022",
        components=[
            {"component_id": f"{pid}-c1", "name": "Direct Drive Motor Stator", "subsystem": "Drive"},
            {"component_id": f"{pid}-c2", "name": "Drain Pump System", "subsystem": "Plumbing"},
            {"component_id": f"{pid}-c3", "name": "Door Lock & Switch", "subsystem": "Safety"},
        ],
        symptoms=[
            {"symptom_id": f"{pid}-s01", "description": "OE error — drain pump fault", "severity": "high"},
            {"symptom_id": f"{pid}-s02", "description": "DE error — door lock fault", "severity": "medium"},
            {"symptom_id": f"{pid}-s03", "description": "UE unbalanced load repeated aborts", "severity": "medium"},
        ],
        failure_modes=[
            {
                "failure_mode_id": f"{pid}-fm01",
                "name": "Drain Pump Blockage or Failure",
                "description": "Pump cannot evacuate water; OE displayed.",
                "estimated_repair_time_minutes": 50,
                "safety_notes": "Drain residual water before pump service.",
            },
            {
                "failure_mode_id": f"{pid}-fm02",
                "name": "Door Lock Mechanism Fault",
                "description": "Door switch or lock assembly fails DE code.",
                "estimated_repair_time_minutes": 45,
                "safety_notes": "Do not force door when locked.",
            },
            {
                "failure_mode_id": f"{pid}-fm03",
                "name": "Motor Stator or Rotor Fault",
                "description": "Direct drive motor fails spin after balance attempts.",
                "estimated_repair_time_minutes": 120,
                "safety_notes": "Professional service for DD motor.",
            },
        ],
        diagnostic_steps=[
            {
                "step_id": f"{pid}-d01",
                "description": "Clean drain pump filter and foreign object trap.",
                "order": 1,
                "expected_outcome": "OE clears after restart",
            },
            {
                "step_id": f"{pid}-d02",
                "description": "Test door lock latch engagement and wiring harness.",
                "order": 2,
                "expected_outcome": "DE clears; door locks at start",
            },
            {
                "step_id": f"{pid}-d03",
                "description": "Run tub clean cycle; redistribute load for UE test.",
                "order": 3,
                "expected_outcome": "Spin completes or motor fault isolated",
            },
        ],
        parts=[
            {
                "part_id": f"{pid}-p01",
                "name": "Drain Pump Assembly",
                "part_number": "ABQ75742503",
                "estimated_cost_usd": 65.00,
            },
            {
                "part_id": f"{pid}-p02",
                "name": "Door Lock Switch",
                "part_number": "EBF49827801",
                "estimated_cost_usd": 55.00,
            },
            {
                "part_id": f"{pid}-p03",
                "name": "Stator Assembly",
                "part_number": "AJS73172601",
                "estimated_cost_usd": 195.00,
            },
        ],
        symptom_failure_links=[
            {"symptom_id": f"{pid}-s01", "failure_mode_id": f"{pid}-fm01", "confidence": 0.94},
            {"symptom_id": f"{pid}-s02", "failure_mode_id": f"{pid}-fm02", "confidence": 0.93},
            {"symptom_id": f"{pid}-s03", "failure_mode_id": f"{pid}-fm03", "confidence": 0.70},
        ],
        failure_mode_part_links=[
            {
                "failure_mode_id": f"{pid}-fm01",
                "part_id": f"{pid}-p01",
                "quantity": 1,
                "probability": 0.90,
                "is_primary": True,
            },
            {
                "failure_mode_id": f"{pid}-fm02",
                "part_id": f"{pid}-p02",
                "quantity": 1,
                "probability": 0.92,
                "is_primary": True,
            },
            {
                "failure_mode_id": f"{pid}-fm03",
                "part_id": f"{pid}-p03",
                "quantity": 1,
                "probability": 0.85,
                "is_primary": True,
            },
        ],
        failure_mode_component_links=[
            {"failure_mode_id": f"{pid}-fm01", "component_id": f"{pid}-c2", "impact_severity": "primary"},
            {"failure_mode_id": f"{pid}-fm02", "component_id": f"{pid}-c3", "impact_severity": "primary"},
            {"failure_mode_id": f"{pid}-fm03", "component_id": f"{pid}-c1", "impact_severity": "primary"},
        ],
        component_part_links=[
            {"component_id": f"{pid}-c2", "part_id": f"{pid}-p01"},
            {"component_id": f"{pid}-c3", "part_id": f"{pid}-p02"},
            {"component_id": f"{pid}-c1", "part_id": f"{pid}-p03"},
        ],
        error_codes=[
            {"error_code_id": f"{pid}-ec-oe", "code": "OE", "description": "Drain error"},
            {"error_code_id": f"{pid}-ec-de", "code": "DE", "description": "Door lock error"},
            {"error_code_id": f"{pid}-ec-ue", "code": "UE", "description": "Unbalanced load"},
        ],
        error_code_failure_links=[
            {"error_code_id": f"{pid}-ec-oe", "failure_mode_id": f"{pid}-fm01", "confidence": 0.95},
            {"error_code_id": f"{pid}-ec-de", "failure_mode_id": f"{pid}-fm02", "confidence": 0.94},
            {"error_code_id": f"{pid}-ec-ue", "failure_mode_id": f"{pid}-fm03", "confidence": 0.65},
        ],
        diagnostic_step_failure_links=[
            {"step_id": f"{pid}-d01", "failure_mode_id": f"{pid}-fm01", "link_type": "CONFIRMS", "confidence": 0.93},
            {"step_id": f"{pid}-d02", "failure_mode_id": f"{pid}-fm02", "link_type": "CONFIRMS", "confidence": 0.92},
            {"step_id": f"{pid}-d03", "failure_mode_id": f"{pid}-fm03", "link_type": "CONFIRMS", "confidence": 0.78},
        ],
        diagnostic_tree_links=[
            {"from_step_id": f"{pid}-d01", "to_step_id": f"{pid}-d02", "condition": "de_error"},
            {"from_step_id": f"{pid}-d02", "to_step_id": f"{pid}-d03", "condition": "ue_spin_abort"},
        ],
        oem_sources=["https://www.lg.com/us/support/help-library/lg-washing-machine-error-code-list"],
    )


OEM_BLUEPRINT_BUILDERS = [
    samsung_wf45t6000aw,
    lg_wm4000hwa,
    lg_ldf5545st,
    samsung_dw80b7070us,
    whirlpool_wtw5000dw,
    lg_dle3400w,
    samsung_rf28r7351sg,
    whirlpool_wfg505m0bs,
    bosch_shpm88z75n,
    ge_jvm3160rfss,
]


def _legacy_products() -> list[dict]:
    return [
        build_washing_machine().model_dump(),
        build_dishwasher().model_dump(),
        build_microwave().model_dump(),
    ]


def build_oem_enterprise_catalog() -> dict:
    """Full enterprise catalog: legacy demo products + OEM blueprints."""
    from graph.warranty_catalog_extensions import (
        ENTERPRISE_ASSETS,
        ENTERPRISE_CLAIMS,
        WARRANTY_POLICIES,
        merge_product_extensions,
    )

    products = [merge_product_extensions(p) for p in _legacy_products()]
    for builder in OEM_BLUEPRINT_BUILDERS:
        products.append(builder())

    # Extended assets for OEM units
    oem_assets = list(ENTERPRISE_ASSETS) + [
        {
            "asset_id": "AST-SAM-WF45-001",
            "customer_id": "CUST-10087",
            "product_id": "oem-sam-wf45",
            "sku_id": "SKU-SAM-WF45-2022",
            "model_number": "WF45T6000AW",
            "serial_number": "SAM-WF45T6000AW-2022-88001",
            "purchase_date": "2022-08-10",
            "warranty_status": "active",
            "warranty_expiry": "2026-08-10",
            "policy_id": "WP-STANDARD-24M",
        },
        {
            "asset_id": "AST-LG-DW-001",
            "customer_id": "CUST-10042",
            "product_id": "oem-lg-ldf5545",
            "sku_id": "SKU-LG-LDF5545-2021",
            "model_number": "LDF5545ST",
            "serial_number": "LG-LDF5545ST-2021-22001",
            "purchase_date": "2021-05-22",
            "warranty_status": "active",
            "warranty_expiry": "2026-05-22",
            "policy_id": "WP-STANDARD-24M",
        },
        {
            "asset_id": "AST-SAM-RF28-001",
            "customer_id": "CUST-10042",
            "product_id": "oem-sam-rf28",
            "sku_id": "SKU-SAM-RF28-2021",
            "model_number": "RF28R7351SG",
            "serial_number": "SAM-RF28R7351SG-2021-55001",
            "purchase_date": "2021-09-01",
            "warranty_status": "active",
            "warranty_expiry": "2026-09-01",
            "policy_id": "WP-STANDARD-24M",
        },
        {
            "asset_id": "AST-LG-DLE-001",
            "customer_id": "CUST-10087",
            "product_id": "oem-lg-dle3400",
            "sku_id": "SKU-LG-DLE3400-2022",
            "model_number": "DLE3400W",
            "serial_number": "LG-DLE3400W-2022-77001",
            "purchase_date": "2022-03-14",
            "warranty_status": "active",
            "warranty_expiry": "2027-03-14",
            "policy_id": "WP-STANDARD-24M",
        },
        {
            "asset_id": "AST-WHI-RNG-001",
            "customer_id": "CUST-10042",
            "product_id": "oem-whi-wfg505",
            "sku_id": "SKU-WHI-WFG505-2023",
            "model_number": "WFG505M0BS",
            "serial_number": "WHI-WFG505M0BS-2023-12001",
            "purchase_date": "2023-11-20",
            "warranty_status": "active",
            "warranty_expiry": "2027-11-20",
            "policy_id": "WP-STANDARD-24M",
        },
    ]
    oem_claims = list(ENTERPRISE_CLAIMS) + [
        {
            "claim_id": "CLM-2026-00812",
            "asset_id": "AST-SAM-WF45-001",
            "product_id": "oem-sam-wf45",
            "symptom_id": "oem-sam-wf45-s01",
            "confirmed_failure_mode_id": "oem-sam-wf45-fm01",
            "used_part_id": "oem-sam-wf45-p01",
            "resolution_summary": "Pump filter cleaned; drain pump replaced under warranty.",
            "closed_date": "2026-01-15",
        },
    ]

    payload = build_enterprise_catalog_payload(products)
    payload["assets"] = oem_assets
    payload["claims"] = oem_claims
    payload["warranty_policies"] = WARRANTY_POLICIES
    payload["catalog_metadata"] = {
        "version": "2.1-enterprise-oem-expanded",
        "product_count": len(products),
        "oem_product_count": len(OEM_BLUEPRINT_BUILDERS),
        "data_policy": "Public OEM support documentation only; verify before production use.",
    }
    return payload
