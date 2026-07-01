"""
Enterprise-grade synthetic diagnosis data generator.

Produces structured, explainable knowledge graph data for three appliance
products with symptoms, failure modes, diagnostic steps, parts, and historical
resolutions — ready for Neo4j population.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

Severity = Literal["low", "medium", "high", "critical"]
OUTPUT_FILE = Path("data/synthetic_diagnosis_data.json")


class Product(BaseModel):
    product_id: str
    name: str
    category: str
    brand: str
    model_year: int


class Symptom(BaseModel):
    symptom_id: str
    description: str
    severity: Severity


class FailureMode(BaseModel):
    failure_mode_id: str
    name: str
    description: str
    estimated_repair_time_minutes: int
    safety_notes: str


class DiagnosticStep(BaseModel):
    step_id: str
    description: str
    order: int
    expected_outcome: str


class Part(BaseModel):
    part_id: str
    name: str
    part_number: str
    estimated_cost_usd: float


class HistoricalResolution(BaseModel):
    resolution_id: str
    description: str
    confirmed_failure_mode_id: str
    resolution_date: str
    technician_notes: str


class SymptomFailureLink(BaseModel):
    symptom_id: str
    failure_mode_id: str
    confidence: float = Field(ge=0.0, le=1.0)


class FailureModePartLink(BaseModel):
    failure_mode_id: str
    part_id: str
    quantity: int = 1
    probability: float = Field(ge=0.0, le=1.0, default=0.9)
    is_primary: bool = True


class ProductKnowledge(BaseModel):
    product: Product
    symptoms: list[Symptom]
    failure_modes: list[FailureMode]
    diagnostic_steps: list[DiagnosticStep]
    parts: list[Part]
    historical_resolutions: list[HistoricalResolution]
    symptom_failure_links: list[SymptomFailureLink]
    failure_mode_part_links: list[FailureModePartLink] = Field(default_factory=list)


class KnowledgeGraphData(BaseModel):
    products: list[ProductKnowledge]


def build_authoritative_catalog() -> dict:
    """
    Single source of truth for the knowledge graph: the OEM enterprise catalog.

    ``generate_knowledge_graph_data()`` produces a Pydantic-validated *core*
    subset (the three base appliances) that is used as a schema self-check. The
    authoritative artifact written to disk is the richer OEM enterprise catalog
    — a superset built from the same base product builders plus enterprise
    blueprint fields (models, SKUs, error codes, components, claim history).
    """
    from graph.oem_product_catalog import build_oem_enterprise_catalog

    return build_oem_enterprise_catalog()


def build_washing_machine() -> ProductKnowledge:
    product = Product(
        product_id="wm-001",
        name="Front Load Washing Machine 8kg",
        category="Laundry",
        brand="AquaHome",
        model_year=2023,
    )
    symptoms = [
        Symptom(symptom_id="wm-s01", description="Machine does not spin during final cycle", severity="high"),
        Symptom(symptom_id="wm-s02", description="Excessive vibration and banging noise", severity="medium"),
        Symptom(symptom_id="wm-s03", description="Water remains in drum after cycle completes", severity="high"),
        Symptom(symptom_id="wm-s04", description="Error code E21 displayed on panel", severity="medium"),
    ]
    failure_modes = [
        FailureMode(
            failure_mode_id="wm-fm01",
            name="Worn Drive Belt",
            description="Drive belt has stretched or snapped, preventing drum rotation.",
            estimated_repair_time_minutes=45,
            safety_notes="Disconnect power before removing rear panel. Belt tension can snap fingers.",
        ),
        FailureMode(
            failure_mode_id="wm-fm02",
            name="Failed Drain Pump",
            description="Pump impeller blocked or motor burned out, preventing water evacuation.",
            estimated_repair_time_minutes=60,
            safety_notes="Residual water may leak when opening filter. Place towels and unplug unit.",
        ),
        FailureMode(
            failure_mode_id="wm-fm03",
            name="Unbalanced Load Sensor Fault",
            description="Suspension rods or shock absorbers degraded, triggering imbalance shutdown.",
            estimated_repair_time_minutes=90,
            safety_notes="Do not bypass safety sensor. Machine may walk across floor if forced to spin.",
        ),
    ]
    diagnostic_steps = [
        DiagnosticStep(
            step_id="wm-d01",
            description="Run empty spin cycle and listen for motor engagement.",
            order=1,
            expected_outcome="Motor hums but drum does not rotate",
        ),
        DiagnosticStep(
            step_id="wm-d02",
            description="Inspect drive belt through rear access panel.",
            order=2,
            expected_outcome="Belt slack, fraying, or missing",
        ),
        DiagnosticStep(
            step_id="wm-d03",
            description="Check drain filter and run pump test mode.",
            order=3,
            expected_outcome="Pump does not activate or makes grinding noise",
        ),
        DiagnosticStep(
            step_id="wm-d04",
            description="Inspect suspension rods for play and oil leakage.",
            order=4,
            expected_outcome="Rods loose or shocks leaking fluid",
        ),
    ]
    parts = [
        Part(part_id="wm-p01", name="Drive Belt Assembly", part_number="AH-DB-8842", estimated_cost_usd=28.50),
        Part(part_id="wm-p02", name="Drain Pump Motor", part_number="AH-DP-3310", estimated_cost_usd=62.00),
        Part(part_id="wm-p03", name="Shock Absorber Kit (x4)", part_number="AH-SA-2201", estimated_cost_usd=84.99),
    ]
    historical_resolutions = [
        HistoricalResolution(
            resolution_id="wm-r01",
            description="Replaced worn drive belt; spin restored.",
            confirmed_failure_mode_id="wm-fm01",
            resolution_date="2025-11-12",
            technician_notes="Customer reported 6 months of intermittent spin failure. Belt showed heat cracking.",
        ),
        HistoricalResolution(
            resolution_id="wm-r02",
            description="Cleared coin blockage and replaced drain pump.",
            confirmed_failure_mode_id="wm-fm02",
            resolution_date="2026-01-08",
            technician_notes="Coin jam caused pump burnout. Recommended pocket-check habit.",
        ),
    ]
    symptom_failure_links = [
        SymptomFailureLink(symptom_id="wm-s01", failure_mode_id="wm-fm01", confidence=0.92),
        SymptomFailureLink(symptom_id="wm-s02", failure_mode_id="wm-fm03", confidence=0.85),
        SymptomFailureLink(symptom_id="wm-s03", failure_mode_id="wm-fm02", confidence=0.88),
        SymptomFailureLink(symptom_id="wm-s04", failure_mode_id="wm-fm02", confidence=0.70),
        SymptomFailureLink(symptom_id="wm-s04", failure_mode_id="wm-fm01", confidence=0.55),
    ]
    failure_mode_part_links = [
        FailureModePartLink(failure_mode_id="wm-fm01", part_id="wm-p01"),
        FailureModePartLink(failure_mode_id="wm-fm02", part_id="wm-p02"),
        FailureModePartLink(failure_mode_id="wm-fm03", part_id="wm-p03"),
    ]
    return ProductKnowledge(
        product=product,
        symptoms=symptoms,
        failure_modes=failure_modes,
        diagnostic_steps=diagnostic_steps,
        parts=parts,
        historical_resolutions=historical_resolutions,
        symptom_failure_links=symptom_failure_links,
        failure_mode_part_links=failure_mode_part_links,
    )


def build_dishwasher() -> ProductKnowledge:
    product = Product(
        product_id="dw-001",
        name="Built-in Dishwasher 12 Place Setting",
        category="Kitchen",
        brand="CleanWave",
        model_year=2022,
    )
    symptoms = [
        Symptom(symptom_id="dw-s01", description="Dishes come out wet and cold", severity="medium"),
        Symptom(symptom_id="dw-s02", description="Standing water at bottom after cycle", severity="high"),
        Symptom(symptom_id="dw-s03", description="Grinding noise during wash phase", severity="medium"),
        Symptom(symptom_id="dw-s04", description="Detergent dispenser does not open", severity="low"),
    ]
    failure_modes = [
        FailureMode(
            failure_mode_id="dw-fm01",
            name="Heating Element Failure",
            description="Heating element open circuit; water does not reach sanitizing temperature.",
            estimated_repair_time_minutes=75,
            safety_notes="Element remains hot briefly after cycle. Allow 30 min cool-down before service.",
        ),
        FailureMode(
            failure_mode_id="dw-fm02",
            name="Clogged Drain Hose",
            description="Kinked or blocked drain hose prevents complete drainage.",
            estimated_repair_time_minutes=35,
            safety_notes="Water in sump may contain food debris. Wear gloves.",
        ),
        FailureMode(
            failure_mode_id="dw-fm03",
            name="Wash Impeller Obstruction",
            description="Glass shard or bone fragment jamming circulation pump impeller.",
            estimated_repair_time_minutes=50,
            safety_notes="Sharp debris risk. Disconnect power and water supply first.",
        ),
    ]
    diagnostic_steps = [
        DiagnosticStep(
            step_id="dw-d01",
            description="Run rinse-only cycle and measure outlet water temperature.",
            order=1,
            expected_outcome="Water stays below 40°C",
        ),
        DiagnosticStep(
            step_id="dw-d02",
            description="Inspect drain hose for kinks behind kick plate.",
            order=2,
            expected_outcome="Hose pinched or filled with grease buildup",
        ),
        DiagnosticStep(
            step_id="dw-d03",
            description="Remove lower spray arm and check impeller chamber.",
            order=3,
            expected_outcome="Foreign object visible or impeller does not spin freely",
        ),
        DiagnosticStep(
            step_id="dw-d04",
            description="Test detergent dispenser solenoid with multimeter.",
            order=4,
            expected_outcome="No continuity on wax motor solenoid",
        ),
    ]
    parts = [
        Part(part_id="dw-p01", name="Heating Element", part_number="CW-HE-4412", estimated_cost_usd=45.00),
        Part(part_id="dw-p02", name="Drain Hose Kit", part_number="CW-DH-1100", estimated_cost_usd=18.75),
        Part(part_id="dw-p03", name="Circulation Pump Assembly", part_number="CW-CP-9920", estimated_cost_usd=110.00),
    ]
    historical_resolutions = [
        HistoricalResolution(
            resolution_id="dw-r01",
            description="Replaced heating element; sanitizing temperature restored.",
            confirmed_failure_mode_id="dw-fm01",
            resolution_date="2025-09-20",
            technician_notes="Hard water scale contributed to element burnout. Advised monthly descale.",
        ),
        HistoricalResolution(
            resolution_id="dw-r02",
            description="Removed glass fragment from impeller; noise eliminated.",
            confirmed_failure_mode_id="dw-fm03",
            resolution_date="2026-02-14",
            technician_notes="Customer loaded chipped glass. Recommended pre-rinse inspection.",
        ),
    ]
    symptom_failure_links = [
        SymptomFailureLink(symptom_id="dw-s01", failure_mode_id="dw-fm01", confidence=0.90),
        SymptomFailureLink(symptom_id="dw-s02", failure_mode_id="dw-fm02", confidence=0.87),
        SymptomFailureLink(symptom_id="dw-s03", failure_mode_id="dw-fm03", confidence=0.91),
        SymptomFailureLink(symptom_id="dw-s04", failure_mode_id="dw-fm01", confidence=0.30),
    ]
    failure_mode_part_links = [
        FailureModePartLink(failure_mode_id="dw-fm01", part_id="dw-p01"),
        FailureModePartLink(failure_mode_id="dw-fm02", part_id="dw-p02"),
        FailureModePartLink(failure_mode_id="dw-fm03", part_id="dw-p03"),
    ]
    return ProductKnowledge(
        product=product,
        symptoms=symptoms,
        failure_modes=failure_modes,
        diagnostic_steps=diagnostic_steps,
        parts=parts,
        historical_resolutions=historical_resolutions,
        symptom_failure_links=symptom_failure_links,
        failure_mode_part_links=failure_mode_part_links,
    )


def build_microwave() -> ProductKnowledge:
    product = Product(
        product_id="mw-001",
        name="Convection Microwave 25L",
        category="Kitchen",
        brand="HeatPro",
        model_year=2024,
    )
    symptoms = [
        Symptom(symptom_id="mw-s01", description="Microwave runs but food stays cold", severity="critical"),
        Symptom(symptom_id="mw-s02", description="Arcing/sparking inside cavity", severity="critical"),
        Symptom(symptom_id="mw-s03", description="Convection fan not running", severity="medium"),
        Symptom(symptom_id="mw-s04", description="Door latch feels loose", severity="high"),
    ]
    failure_modes = [
        FailureMode(
            failure_mode_id="mw-fm01",
            name="Magnetron Failure",
            description="Magnetron filament or high-voltage diode failed; no microwave energy produced.",
            estimated_repair_time_minutes=120,
            safety_notes="HIGH VOLTAGE. Capacitor retains charge. Only certified technicians should service.",
        ),
        FailureMode(
            failure_mode_id="mw-fm02",
            name="Damaged Waveguide Cover",
            description="Grease buildup on mica waveguide cover causing arcing and burn-through.",
            estimated_repair_time_minutes=25,
            safety_notes="Do not operate with damaged cover. Arcing can damage magnetron.",
        ),
        FailureMode(
            failure_mode_id="mw-fm03",
            name="Convection Fan Motor Failure",
            description="Fan motor bearing seized; convection bake mode ineffective.",
            estimated_repair_time_minutes=55,
            safety_notes="Unit may overheat in convection mode. Stop use until repaired.",
        ),
    ]
    diagnostic_steps = [
        DiagnosticStep(
            step_id="mw-d01",
            description="Heat cup of water for 60 seconds on high power.",
            order=1,
            expected_outcome="Water temperature unchanged",
        ),
        DiagnosticStep(
            step_id="mw-d02",
            description="Inspect waveguide cover for burn marks or holes.",
            order=2,
            expected_outcome="Charring or missing mica section",
        ),
        DiagnosticStep(
            step_id="mw-d03",
            description="Run convection bake at 180°C and listen for fan.",
            order=3,
            expected_outcome="No airflow; fan motor silent",
        ),
        DiagnosticStep(
            step_id="mw-d04",
            description="Check door switch continuity with door closed.",
            order=4,
            expected_outcome="Interlock switch fails continuity test",
        ),
    ]
    parts = [
        Part(part_id="mw-p01", name="Magnetron Assembly", part_number="HP-MG-7700", estimated_cost_usd=95.00),
        Part(part_id="mw-p02", name="Waveguide Mica Cover", part_number="HP-WG-0012", estimated_cost_usd=8.50),
        Part(part_id="mw-p03", name="Convection Fan Motor", part_number="HP-CF-3300", estimated_cost_usd=42.00),
    ]
    historical_resolutions = [
        HistoricalResolution(
            resolution_id="mw-r01",
            description="Replaced waveguide cover; arcing stopped.",
            confirmed_failure_mode_id="mw-fm02",
            resolution_date="2025-12-03",
            technician_notes="Grease splatter from uncovered dish caused cover damage.",
        ),
        HistoricalResolution(
            resolution_id="mw-r02",
            description="Replaced magnetron after confirmed HV diode failure.",
            confirmed_failure_mode_id="mw-fm01",
            resolution_date="2026-03-01",
            technician_notes="Unit out of warranty. Customer opted for repair over replacement.",
        ),
    ]
    symptom_failure_links = [
        SymptomFailureLink(symptom_id="mw-s01", failure_mode_id="mw-fm01", confidence=0.94),
        SymptomFailureLink(symptom_id="mw-s02", failure_mode_id="mw-fm02", confidence=0.89),
        SymptomFailureLink(symptom_id="mw-s03", failure_mode_id="mw-fm03", confidence=0.86),
        SymptomFailureLink(symptom_id="mw-s04", failure_mode_id="mw-fm01", confidence=0.40),
    ]
    failure_mode_part_links = [
        FailureModePartLink(failure_mode_id="mw-fm01", part_id="mw-p01"),
        FailureModePartLink(failure_mode_id="mw-fm02", part_id="mw-p02"),
        FailureModePartLink(failure_mode_id="mw-fm03", part_id="mw-p03"),
    ]
    return ProductKnowledge(
        product=product,
        symptoms=symptoms,
        failure_modes=failure_modes,
        diagnostic_steps=diagnostic_steps,
        parts=parts,
        historical_resolutions=historical_resolutions,
        symptom_failure_links=symptom_failure_links,
        failure_mode_part_links=failure_mode_part_links,
    )


def generate_knowledge_graph_data() -> KnowledgeGraphData:
    return KnowledgeGraphData(
        products=[
            build_washing_machine(),
            build_dishwasher(),
            build_microwave(),
        ]
    )


def main() -> None:
    # Schema self-check: validate the core appliance models before exporting.
    core = generate_knowledge_graph_data()

    # Authoritative export = the OEM enterprise catalog (single source of truth).
    catalog = build_authoritative_catalog()
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(json.dumps(catalog, indent=2), encoding="utf-8")

    from graph.enterprise_pipeline.transformers.pim_blueprint_sync import sync_pim_fixture

    sync_pim_fixture(write_enterprise_catalog=True)

    print(f"✅ Generated authoritative catalog: {OUTPUT_FILE}")
    print(f"   Core schema self-check passed: {len(core.products)} base product(s) validated")
    for item in catalog.get("products", []):
        product = item.get("product", {})
        print(
            f"   • {product.get('name', product.get('product_id', '?'))} "
            f"({len(item.get('symptoms', []))} symptoms, "
            f"{len(item.get('failure_modes', []))} failure modes, "
            f"{len(item.get('parts', []))} parts)"
        )


if __name__ == "__main__":
    main()
