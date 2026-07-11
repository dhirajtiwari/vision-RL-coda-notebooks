"""
GraphRAG layer: query the Neo4j knowledge graph for diagnosis evidence.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any

from config.settings import settings
from graph import reliability
from graph.diagnostic_engine import (
    get_diagnostic_steps,
    get_diagnostic_tree,
    resolve_dynamic_steps,
)
from graph.neo4j_client import get_driver
from graph.provenance import enrich_entity_props, provenance_evidence_line
from graph.symptom_retrieval import hybrid_symptom_score
from utils.diagnosis_display import format_traceability_lines


@dataclass
class DiagnosisResult:
    product_id: str
    product_name: str
    matched_symptoms: list[dict[str, Any]] = field(default_factory=list)
    ranked_failure_modes: list[dict[str, Any]] = field(default_factory=list)
    diagnostic_steps: list[dict[str, Any]] = field(default_factory=list)
    parts: list[dict[str, Any]] = field(default_factory=list)
    historical_resolutions: list[dict[str, Any]] = field(default_factory=list)
    confidence: float = 0.0
    graph_confidence: float = 0.0
    language_confidence: float = 0.0
    should_escalate: bool = False
    escalation_reason: str = ""
    evidence: list[str] = field(default_factory=list)
    provenance_trail: list[dict[str, Any]] = field(default_factory=list)
    asset_id: str = ""
    model_number: str = ""
    sku_id: str = ""
    serial_number: str = ""
    matched_error_codes: list[dict[str, Any]] = field(default_factory=list)
    impacted_components: list[dict[str, Any]] = field(default_factory=list)
    predicted_parts: list[dict[str, Any]] = field(default_factory=list)
    claim_precedents: list[dict[str, Any]] = field(default_factory=list)
    diagnostic_tree: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    # Scoring transparency fields (separated for UI display)
    recommendation_strength: str = ""  # 'Strong' | 'Moderate' | 'Weak' | 'Insufficient data'
    posterior_dominance_ratio: float = 0.0  # top_posterior / second_posterior
    # Exact traversal path: the specific Symptom→FM edges that were weighted in this diagnosis.
    # Enables the UI to highlight ONLY the edges that were actually used,
    # separately from the full "relevant context" subgraph.
    traversed_symptom_ids: list[str] = field(default_factory=list)
    traversed_fm_id: str = ""
    # Hard fail-closed when product / asset / message context is inconsistent.
    # When True, ranked_failure_modes is empty and no graph diagnosis is claimed.
    context_blocked: bool = False
    context_block_code: str = ""  # e.g. soft_appliance_mismatch | product_asset_conflict
    resolution_meta: dict[str, Any] = field(default_factory=dict)


SYNONYMS = {
    "spin": {"spin", "spins", "spinning", "rotate", "rotation"},
    "water": {"water", "drain", "drainage", "flooded"},
    "drum": {"drum", "tub"},
    "machine": {"machine", "washer", "laundry", "appliance"},
    "remain": {"remain", "remains", "stays", "stayed", "left", "standing"},
    "noise": {"noise", "vibration", "banging", "grinding", "loud"},
    "cold": {"cold", "chill", "cool"},
    "wet": {"wet", "damp", "moist"},
    "arcing": {"arcing", "spark", "sparking", "sparks"},
    "heat": {"heat", "heating", "hot", "warm", "temperature"},
}

_CONTRACTION_REPLACEMENTS = (
    ("won't", "not"),
    ("wont", "not"),
    ("doesn't", "not"),
    ("doesnt", "not"),
    ("does not", "not"),
    ("will not", "not"),
    ("can't", "not"),
    ("cannot", "not"),
    ("stays in", "remains in"),
    ("water stays", "water remains"),
    ("washing machine", "machine"),
    ("in the drum", "in drum"),
)


def _normalize_message(text: str) -> str:
    """Normalize customer phrasing so catalog symptoms match more reliably."""
    normalized = text.lower().strip()
    for old, new in _CONTRACTION_REPLACEMENTS:
        normalized = normalized.replace(old, new)
    return normalized


def _tokenize(text: str) -> set[str]:
    return {t for t in re.findall(r"[a-z0-9]+", _normalize_message(text)) if len(t) > 2}


def _canonical_tokens(text: str) -> set[str]:
    """Map synonym variants to a single canonical key to avoid inflated overlap."""
    raw = _tokenize(text)
    canonical: set[str] = set()
    for token in raw:
        mapped = token
        for key, group in SYNONYMS.items():
            if token in group:
                mapped = key
                break
        canonical.add(mapped)
    return canonical


def _text_similarity(a: str, b: str) -> float:
    a_norm, b_norm = _normalize_message(a), _normalize_message(b)
    if a_norm in b_norm or b_norm in a_norm:
        return 0.85
    a_tokens, b_tokens = _canonical_tokens(a), _canonical_tokens(b)
    if not a_tokens or not b_tokens:
        return 0.0
    overlap = a_tokens & b_tokens
    base = len(overlap) / max(len(b_tokens), 1)
    # Boost when a key symptom theme is clearly present in both phrases.
    theme_pairs = (
        ({"spin"}, {"spin"}),
        ({"water", "remain"}, {"water", "remain", "drum"}),
        ({"drum"}, {"drum"}),
        ({"start", "starting", "power"}, {"start", "power", "turn"}),
        ({"ice"}, {"ice"}),
        ({"drain"}, {"drain"}),
    )
    for a_themes, b_themes in theme_pairs:
        if (a_tokens & a_themes) and (b_tokens & b_themes):
            base = max(base, 0.45 + 0.15 * len(overlap))
    return min(base, 1.0)


def _load_json_catalog() -> dict[str, Any]:
    with open(settings.data_file, encoding="utf-8") as f:
        return json.load(f)


def _static_product_list() -> list[dict[str, Any]]:
    """Neo4j-free product catalog derived from the OEM blueprints.

    Used as a graceful fallback when Neo4j is unreachable (CI runners and
    local dev machines without Docker). Keeps the app functional for product
    detection and UI listing without a live graph.
    """
    from graph.oem_product_catalog import build_oem_enterprise_catalog

    catalog = build_oem_enterprise_catalog()
    rows: list[dict[str, Any]] = []
    for entry in catalog.get("products", []):
        prod = entry.get("product", entry)
        rows.append(
            {
                "product_id": prod.get("product_id"),
                "name": prod.get("name"),
                "category": prod.get("category"),
                "brand": prod.get("brand"),
            }
        )
    rows.sort(key=lambda r: r.get("name") or "")
    return rows


def list_products() -> list[dict[str, Any]]:
    """List products from Neo4j, falling back to the static OEM catalog.

    Falls back gracefully when Neo4j is unreachable so the application and its
    test suite work without a running graph database (CI, Docker-less dev).
    """
    try:
        driver = get_driver()
        with driver.session() as session:
            result = session.run("""
                MATCH (p:Product)
                RETURN p.product_id AS product_id, p.name AS name,
                       p.category AS category, p.brand AS brand
                ORDER BY p.name
            """)
            rows = [dict(r) for r in result]
        if rows:
            return rows
        # Empty graph (not yet populated) — use static catalog.
        return _static_product_list()
    except Exception:
        # Neo4j unreachable — degrade gracefully to the static catalog.
        return _static_product_list()


PRODUCT_KEYWORDS: dict[str, list[str]] = {
    "wm-001": ["washing machine", "washing", "washer", "laundry", "spin", "drum", "aquahome"],
    "dw-001": ["dishwasher", "dishes", "rinse", "cleanwave"],
    "mw-001": ["microwave", "convection", "magnetron", "arcing", "spark", "heatpro"],
    "ice-001": ["ice maker", "icemaker", "ice machine", "frostbite", "cubes", "bin full"],
    # 2026 multi-source onboard pack
    "vac-001": ["vacuum", "stick vacuum", "brush roll", "roboclean", "suction"],
    "ac-001": ["portable ac", "air conditioner", "coolair", "btu", "condenser"],
    "oven-001": ["wall oven", "bakepro", "preheat", "oven sensor"],
    "dry-001": ["heat pump dryer", "airflow dryer", "dryer damp", "clothes remain damp"],
    "ref-001": ["compact fridge", "chillvault", "refrigerator warm", "defrost"],
    "grill-001": ["outdoor grill", "flamemaster", "burner", "igniter", "grill"],
    "hob-001": ["induction hob", "sparkline", "induction", "cooktop zone"],
    "fan-001": ["bladeless fan", "breezetower", "oscillat", "airflow fan"],
    "pur-001": [
        "purifier",
        "air purifier",
        "hepa",
        "pure room",
        "pureroom",
        "air quality light",
        "filter change",
    ],
    # 2026 multi-source NEW product (PIM + semi + unstructured + FSM/claims/CRM)
    "hmd-001": [
        "dehumidifier",
        "dryzone",
        "hmd30",
        "dz-hmd30",
        "water tank never fills",
        "tank full",
        "frost sensor",
        "humidity",
        "h3",
    ],
    # 2026 multi-source NEW pack (sources distributed: PIM/FSM/Claims/CRM + pipeline)
    "esp-001": [
        "espresso",
        "brewbar",
        "esp15",
        "bb-esp15",
        "boiler",
        "e05",
        "crema",
        "portafilter",
        "group head",
        "group gasket",
    ],
    "oem-sam-wf45": ["samsung", "wf45", "wf45t6000"],
    "oem-lg-ldf5545": ["lg dishwasher", "ldf5545", "ldf5545st"],
    "oem-whi-wtw5000": ["whirlpool", "wtw5000", "f9 e1", "f9e1"],
    "oem-bos-shpm88": ["bosch", "shpm88"],
    "oem-ge-jvm3160": ["ge microwave", "jvm3160", "over-the-range", "otr microwave"],
    "oem-sam-rf28": ["samsung refrigerator", "rf28", "rf28r7351", "not cooling"],
    "oem-lg-dle3400": ["lg dryer", "dle3400", "vent"],
    "oem-whi-wfg505": ["whirlpool range", "wfg505", "igniter", "f9 e0", "f9e0"],
    "oem-sam-dw80": ["samsung dishwasher", "dw80", "dw80b7070"],
    # Avoid bare "oe"/"de" — they match inside "does"/"device" as substrings
    "oem-lg-wm4000": ["lg washer", "wm4000", "wm4000hwa", " front load washer"],
}


def _keyword_hit(message: str, term: str) -> bool:
    """
    Match product keywords without false positives from short substrings.

    - Multi-word / long terms: substring OK (e.g. "air purifier")
    - Short codes (≤3 chars): whole-word / token boundary only
    """
    term = (term or "").lower().strip()
    if not term or not message:
        return False
    msg = message.lower()
    if len(term) <= 3:
        # Word boundary so "oe" does not match "does"
        return re.search(rf"(?<![a-z0-9]){re.escape(term)}(?![a-z0-9])", msg) is not None
    return term in msg


def score_products_from_message(user_message: str) -> dict[str, int]:
    message = (user_message or "").lower()
    scores = {
        product_id: sum(1 for term in terms if _keyword_hit(message, term))
        for product_id, terms in PRODUCT_KEYWORDS.items()
    }
    # Boost from live product name/brand tokens (covers newly onboarded products)
    try:
        for p in list_products():
            pid = p.get("product_id")
            if not pid:
                continue
            boost = 0
            for field in ("name", "brand", "category"):
                val = (p.get(field) or "").lower()
                if not val:
                    continue
                # Significant tokens from product title
                for tok in re.findall(r"[a-z0-9]{4,}", val):
                    if tok in message:
                        boost += 1
            if boost:
                scores[pid] = scores.get(pid, 0) + boost
    except Exception:
        pass
    return scores


def detect_product(user_message: str) -> dict[str, Any] | None:
    scores = score_products_from_message(user_message)
    if not scores:
        return None
    best_id = max(scores, key=scores.get)
    if scores[best_id] < settings.product_message_signal_min_hits:
        return None
    products = {p["product_id"]: p for p in list_products()}
    return products.get(best_id)


def message_product_signal(user_message: str) -> tuple[str | None, dict[str, int]]:
    """Return best product_id implied by message keywords (or None) and full scores."""
    scores = score_products_from_message(user_message)
    if not scores:
        return None, scores
    best_id = max(scores, key=scores.get)
    if scores[best_id] < settings.product_message_signal_min_hits:
        return None, scores
    return best_id, scores


def _blocked_resolution(
    code: str,
    detail: str,
    *,
    product: dict[str, Any] | None = None,
    asset_ctx: dict[str, Any] | None = None,
    effective_asset_id: str | None = None,
    extra: dict[str, Any] | None = None,
) -> tuple[dict[str, Any] | None, dict[str, Any] | None, str | None, list[str], str, dict[str, Any]]:
    """Resolution tuple: product, asset_ctx, asset_id, warnings, block_code, meta."""
    meta = dict(extra or {})
    meta["soft"] = code.startswith("soft_")
    return product, asset_ctx, effective_asset_id, [detail], code, meta


def _message_implies_other_product(
    bound_id: str,
    msg_product_id: str | None,
    scores: dict[str, int],
) -> bool:
    """
    Soft mismatch only when message clearly points at a *different* product.

    Requires a decisive gap so weak/false hits (historical short codes) cannot
    override a bound asset when the utterance is about that asset (e.g. purifier).
    """
    if not msg_product_id or msg_product_id == bound_id:
        return False
    bound_hits = int(scores.get(bound_id, 0) or 0)
    msg_hits = int(scores.get(msg_product_id, 0) or 0)
    min_hits = max(1, int(settings.product_message_signal_min_hits))
    if msg_hits < min_hits:
        return False
    # Bound product also mentioned → trust the asset (user is on the right unit)
    if bound_hits >= min_hits and bound_hits >= msg_hits:
        return False
    # Need a clear lead for the *other* product (not a 1-hit false positive)
    if msg_hits <= bound_hits:
        return False
    if msg_hits == 1 and bound_hits == 0:
        # Single weak hit is not enough to challenge a bound appliance
        return False
    return msg_hits >= bound_hits + 1 and msg_hits >= 2


def _asset_ctx_from_crm(crm: dict[str, Any] | None, products: dict[str, dict]) -> dict[str, Any] | None:
    """Build asset context from CRM when Neo4j INSTANCE_OF is missing (demo realism)."""
    if not crm or not crm.get("enriched") or not crm.get("asset_id"):
        return None
    pid = crm.get("product_id")
    return {
        "asset_id": crm.get("asset_id"),
        "product_id": pid,
        "product_name": (products.get(pid) or {}).get("name", pid),
        "serial_number": crm.get("serial_number") or "",
        "model_number": crm.get("model_number") or "",
        "sku_id": crm.get("sku_id") or "",
        "customer_id": crm.get("customer_id") or "",
        "source": "CRM",
    }


def resolve_product_for_diagnosis(
    user_message: str,
    product_id: str | None = None,
    asset_id: str | None = None,
    crm_product_id: str | None = None,
    *,
    force_keep_context: bool = False,
    crm_context: dict[str, Any] | None = None,
) -> tuple[dict[str, Any] | None, dict[str, Any] | None, str | None, list[str], str, dict[str, Any]]:
    """
    Asset-first product resolution for production-shaped diagnosis.

    **Identified session (asset / CRM bound):**
      - Product comes from the registered asset — never from free-text override.
      - Client ``product_id`` that disagrees with asset is an API invariant failure.
      - Text that strongly names another appliance family → soft prompt
        (``soft_appliance_mismatch``) unless ``force_keep_context``.

    **Anonymous session (no asset):**
      - Product from explicit pick, else message detection.
      - Same soft mismatch if pick and text disagree.

    Returns:
        (product, asset_ctx, effective_asset_id, warnings, block_code, meta)
    """
    warnings: list[str] = []
    meta: dict[str, Any] = {"session": "anonymous", "force_keep_context": force_keep_context}
    msg_product_id, scores = message_product_signal(user_message)
    products = {p["product_id"]: p for p in list_products()}
    detected = products.get(msg_product_id) if msg_product_id else None

    # Prefer graph asset context; fall back to CRM enrichment (realistic path).
    asset_ctx = resolve_asset_context(asset_id) if asset_id else None
    if not asset_ctx and crm_context:
        asset_ctx = _asset_ctx_from_crm(crm_context, products)
    # If CRM has richer product_id, use CRM as source of truth for bound product
    crm_pid = crm_product_id or (crm_context or {}).get("product_id")
    if asset_ctx and crm_pid and not asset_ctx.get("product_id"):
        asset_ctx["product_id"] = crm_pid
    if asset_ctx and crm_context:
        for k in ("sku_id", "model_number", "serial_number", "customer_id"):
            if crm_context.get(k) and not asset_ctx.get(k):
                asset_ctx[k] = crm_context[k]

    asset_product_id = asset_ctx.get("product_id") if asset_ctx else (crm_pid if asset_id else None)
    if not asset_product_id and crm_pid and asset_id:
        asset_product_id = crm_pid
        if not asset_ctx:
            asset_ctx = _asset_ctx_from_crm(
                crm_context or {"enriched": True, "asset_id": asset_id, "product_id": crm_pid}, products
            )

    effective_asset_id = asset_id if asset_ctx or asset_id else None
    client_product = product_id if product_id and product_id in products else None

    # ─── IDENTIFIED: asset-bound session ───────────────────────────────────
    if asset_product_id and asset_product_id in products:
        meta["session"] = "identified"
        bound = products[asset_product_id]
        # API invariant: client must not send a conflicting product_id
        if client_product and client_product != asset_product_id:
            detail = (
                f"API invariant: product_id `{client_product}` does not match registered asset product "
                f"**{bound['name']}** (`{asset_product_id}`). Bind product from the asset; do not override."
            )
            return _blocked_resolution(
                "product_asset_conflict",
                detail,
                product=bound,
                asset_ctx=asset_ctx,
                effective_asset_id=None,
            )

        # Asset is source of truth: soft language mismatch is a warning, not a hard block.
        # (Hard block still applies for anonymous sessions where product_id is inferred.)
        if _message_implies_other_product(asset_product_id, msg_product_id, scores):
            det_name = (products.get(msg_product_id) or {}).get("name", msg_product_id)
            if force_keep_context:
                warnings.append(
                    f"Proceeding on registered appliance **{bound['name']}** despite description "
                    f"mentioning **{det_name}** (operator confirmed)."
                )
            else:
                warnings.append(
                    f"Note: wording resembles **{det_name}**, but diagnosis stays on the bound asset "
                    f"**{bound['name']}** (`{asset_product_id}`). Switch appliance if that is wrong."
                )
            meta["soft"] = True
            meta["message_product_id"] = msg_product_id
            meta["bound_product_id"] = asset_product_id
        return bound, asset_ctx, effective_asset_id, warnings, "", meta

    # ─── ANONYMOUS: no registered asset ────────────────────────────────────
    meta["session"] = "anonymous"
    if client_product:
        bound = products[client_product]
        if _message_implies_other_product(client_product, msg_product_id, scores) and not force_keep_context:
            det_name = (products.get(msg_product_id) or {}).get("name", msg_product_id)
            detail = (
                f"Your description sounds like **{det_name}**, but you selected **{bound['name']}**. "
                "Change the appliance type or confirm to continue."
            )
            return _blocked_resolution(
                "soft_appliance_mismatch",
                detail,
                product=bound,
                extra={
                    "bound_product_id": client_product,
                    "message_product_id": msg_product_id,
                    "suggested_product_id": msg_product_id,
                    "can_force_keep": True,
                },
            )
        return bound, None, None, warnings, "", meta

    if detected:
        return detected, None, None, warnings, "", meta

    return None, None, None, warnings, "", meta


def match_symptoms(product_id: str, user_message: str) -> list[dict[str, Any]]:
    from graph.symptom_retrieval import normalize_query_text

    # Phrase rewrites so "not starting" aligns with catalog "will not start / power up"
    query = normalize_query_text(user_message)
    driver = get_driver()
    with driver.session() as session:
        symptoms = session.run(
            """
            MATCH (p:Product {product_id: $product_id})-[:HAS_SYMPTOM]->(s:Symptom)
            RETURN s.symptom_id AS symptom_id, s.description AS description,
                   s.severity AS severity,
                   s.source_system AS source_system,
                   s.source_record_id AS source_record_id,
                   s.source_document_uri AS source_document_uri,
                   s.approval_status AS approval_status
        """,
            product_id=product_id,
        )
        symptom_list = [dict(r) for r in symptoms]

    corpus = [s["description"] for s in symptom_list]
    scored: list[tuple[dict[str, Any], float]] = []
    for symptom in symptom_list:
        lexical = _text_similarity(query, symptom["description"])
        if settings.use_hybrid_symptom_matching:
            score = hybrid_symptom_score(
                query,
                symptom["description"],
                lexical_score=lexical,
                corpus=corpus,
            )
        else:
            score = lexical
        scored.append((symptom, score))

    min_score = settings.symptom_match_min_score
    rel_floor = float(getattr(settings, "symptom_secondary_relative_floor", 0.75))
    matched: list[dict[str, Any]] = []

    # Sort by score; admit only scores clearing the absolute bar.
    scored.sort(key=lambda x: x[1], reverse=True)
    top_score = scored[0][1] if scored else 0.0
    for symptom, score in scored:
        if score < min_score:
            continue
        # Secondary admissions must stay close to the best match — no floor noise.
        if matched and score < top_score * rel_floor:
            continue
        enriched = enrich_entity_props("Symptom", symptom["symptom_id"], symptom)
        matched.append(
            {
                **enriched,
                "match_score": round(score, 2),
                "evidence_role": "observed",
            }
        )
        if len(matched) >= 4:
            break

    return matched


def _composite_confidence(
    ranked: list[dict[str, Any]],
    matched_symptoms: list[dict[str, Any]],
) -> tuple[float, float, float, str, float]:
    """
    Return (overall, graph-edge, language-match, recommendation_strength, dominance_ratio).

    - overall  = Bayesian posterior of the leading FM, boosted when it is clearly
                 dominant over the second-best candidate (reliability.dominance_boost).
    - graph    = max INDICATES edge likelihood for the top FM.
    - language = retrieval match quality (text-to-symptom).
    - recommendation_strength = 'Strong' | 'Moderate' | 'Weak' | 'Insufficient data'.
    - dominance_ratio = top_posterior / second_posterior (transparency metric).
    """
    if not ranked or not matched_symptoms:
        return 0.0, 0.0, 0.0, "Insufficient data", 0.0

    score_by_id = {s["symptom_id"]: float(s.get("match_score", 0.0)) for s in matched_symptoms}
    language_conf = max(score_by_id.values()) if score_by_id else 0.0

    top = ranked[0]
    posteriors = {fm["failure_mode_id"]: float(fm.get("posterior", 0.0)) for fm in ranked}
    sorted_posts = sorted(posteriors.values(), reverse=True)
    dominance_ratio = round(sorted_posts[0] / max(sorted_posts[1], 0.001), 2) if len(sorted_posts) > 1 else 10.0

    # Dominance boost: clear leader → higher expressed confidence
    overall = reliability.dominance_boost(posteriors)

    graph_conf = 0.0
    for ind in top.get("indications") or []:
        sid = ind.get("symptom_id")
        edge = ind.get("confidence")
        if sid in score_by_id and edge is not None:
            graph_conf = max(graph_conf, float(edge))

    strength = reliability.recommendation_strength(overall, graph_conf, language_conf, dominance_ratio=dominance_ratio)
    return round(overall, 2), round(graph_conf, 2), round(language_conf, 2), strength, dominance_ratio


def list_failure_modes(product_id: str) -> list[dict[str, Any]]:
    driver = get_driver()
    with driver.session() as session:
        result = session.run(
            """
            MATCH (p:Product {product_id: $product_id})-[:CAN_HAVE]->(fm:FailureMode)
            RETURN fm.failure_mode_id AS failure_mode_id,
                   fm.name AS name,
                   fm.description AS description,
                   fm.estimated_repair_time_minutes AS repair_minutes,
                   fm.safety_notes AS safety_notes
            ORDER BY fm.name
        """,
            product_id=product_id,
        )
        return [dict(r) for r in result]


def _apply_fmea_and_posteriors(
    ranked: list[dict[str, Any]],
    symptom_ids: list[str],
) -> list[dict[str, Any]]:
    """
    Enrich ranked failure modes with FMEA ratings (S/O/D, RPN, Action Priority)
    and a normalised naive-Bayes posterior P(fm | observed symptoms).

    Grounded in graph evidence:
      - Severity   <- worst symptom severity for the mode
      - Occurrence <- observed field-confirmation count (claims + resolutions)
      - Detection  <- diagnostic-step coverage that confirms the mode
      - Likelihood <- (Symptom)-[:INDICATES]->(FailureMode).confidence
    See graph/reliability.py for the standards references.
    """
    for row in ranked:
        sev = reliability.severity_rating(row.pop("severities", None) or [])
        occ = reliability.occurrence_rating(row.pop("evidence_count", 0) or 0)
        det = reliability.detection_rating(row.pop("step_count", 0) or 0)
        row["severity_rating"] = sev
        row["occurrence_rating"] = occ
        row["detection_rating"] = det
        row["rpn"] = reliability.rpn(sev, occ, det)
        row["action_priority"] = reliability.action_priority(sev, occ, det)
        row["_prior"] = reliability.occurrence_prior(occ)

    fm_ids = [row["failure_mode_id"] for row in ranked]
    priors = {row["failure_mode_id"]: row["_prior"] for row in ranked}
    likelihoods: dict[tuple[str, str], float] = {}
    for row in ranked:
        for ind in row.get("indications") or []:
            sid = ind.get("symptom_id")
            conf = ind.get("confidence")
            if sid and conf is not None:
                likelihoods[(sid, row["failure_mode_id"])] = float(conf)

    posteriors = reliability.bayesian_posteriors(priors, likelihoods, symptom_ids, fm_ids)
    for row in ranked:
        row["posterior"] = round(posteriors.get(row["failure_mode_id"], 0.0), 4)
        row.pop("_prior", None)

    # Rank by diagnostic posterior, then FMEA risk (RPN), then evidence breadth.
    ranked.sort(
        key=lambda x: (x.get("posterior", 0.0), x.get("rpn", 0), x.get("link_count", 0)),
        reverse=True,
    )
    return ranked


def rank_failure_modes(product_id: str, symptom_ids: list[str]) -> list[dict[str, Any]]:
    if not symptom_ids:
        failures = list_failure_modes(product_id)
        return [
            {
                **fm,
                "indications": [],
                "total_confidence": 0,
                "link_count": 0,
                "aggregate_confidence": 0.0,
                "posterior": 0.0,
            }
            for fm in failures
        ]

    driver = get_driver()
    with driver.session() as session:
        result = session.run(
            """
            MATCH (p:Product {product_id: $product_id})-[:CAN_HAVE]->(fm:FailureMode)
            OPTIONAL MATCH (s:Symptom)-[ind:INDICATES]->(fm)
            WHERE s.symptom_id IN $symptom_ids
            WITH fm, collect(DISTINCT {symptom_id: s.symptom_id, confidence: ind.confidence}) AS indications,
                 sum(CASE WHEN ind.confidence IS NULL THEN 0 ELSE ind.confidence END) AS total_confidence,
                 count(ind) AS link_count
            RETURN fm.failure_mode_id AS failure_mode_id,
                   fm.name AS name,
                   fm.description AS description,
                   fm.estimated_repair_time_minutes AS repair_minutes,
                   fm.safety_notes AS safety_notes,
                   fm.source_system AS source_system,
                   fm.source_record_id AS source_record_id,
                   fm.source_document_uri AS source_document_uri,
                   indications,
                   total_confidence,
                   link_count,
                   [ (sv:Symptom)-[:INDICATES]->(fm) | sv.severity ] AS severities,
                   size([ (fm)<-[:CONFIRMED]-(ev) | ev ]) AS evidence_count,
                   size([ (ds:DiagnosticStep)-[:CONFIRMS]->(fm) | ds ]) AS step_count
            ORDER BY total_confidence DESC, link_count DESC
        """,
            product_id=product_id,
            symptom_ids=symptom_ids,
        )
        ranked = []
        for record in result:
            row = dict(record)
            # Drop null indication stubs from OPTIONAL MATCH
            inds = [
                ind
                for ind in (row.get("indications") or [])
                if ind and ind.get("symptom_id") and ind.get("confidence") is not None
            ]
            row["indications"] = inds
            row["link_count"] = len(inds)
            row["total_confidence"] = sum(float(i["confidence"]) for i in inds)
            row["aggregate_confidence"] = round(row["total_confidence"] / max(len(symptom_ids), 1), 2)
            ranked.append(row)

    # Evidence-only candidates: never give prior mass to FMs with zero INDICATES
    # edges from the *observed* symptoms (prevents impeller-at-10% on wet/cold).
    evidenced = [row for row in ranked if int(row.get("link_count") or 0) > 0]
    if not evidenced:
        return []
    return _apply_fmea_and_posteriors(evidenced, symptom_ids)


def resolve_asset_context(asset_id: str) -> dict[str, Any] | None:
    driver = get_driver()
    with driver.session() as session:
        row = session.run(
            """
            MATCH (a:Asset {asset_id: $asset_id})-[:INSTANCE_OF]->(p:Product)
            OPTIONAL MATCH (a)-[:BOUND_TO_SKU]->(sku:SKU)
            OPTIONAL MATCH (p)-[:HAS_MODEL]->(m:Model)
            RETURN a.asset_id AS asset_id, a.serial_number AS serial_number,
                   a.model_number AS model_number, a.customer_id AS customer_id,
                   p.product_id AS product_id, p.name AS product_name,
                   sku.sku_id AS sku_id, m.model_number AS graph_model_number
            """,
            asset_id=asset_id,
        ).single()
        return dict(row) if row else None


def match_error_codes(product_id: str, user_message: str) -> list[dict[str, Any]]:
    driver = get_driver()
    message = user_message.upper()
    with driver.session() as session:
        codes = session.run(
            """
            MATCH (p:Product {product_id: $product_id})-[:HAS_ERROR_CODE]->(ec:ErrorCode)
            RETURN ec.error_code_id AS error_code_id, ec.code AS code, ec.description AS description
            """,
            product_id=product_id,
        )
        matched = []
        for row in codes:
            code = row["code"]
            if code.upper() in message or f"ERROR CODE {code.upper()}" in message:
                matched.append(dict(row))
        return matched


def rank_failure_modes_with_error_codes(
    product_id: str,
    symptom_ids: list[str],
    error_code_ids: list[str],
) -> list[dict[str, Any]]:
    ranked = rank_failure_modes(product_id, symptom_ids)
    if not error_code_ids:
        return ranked

    driver = get_driver()
    with driver.session() as session:
        boosts = session.run(
            """
            MATCH (ec:ErrorCode)-[r:INDICATES]->(fm:FailureMode)
            WHERE ec.error_code_id IN $error_code_ids
            RETURN fm.failure_mode_id AS failure_mode_id, sum(r.confidence) AS error_boost
            """,
            error_code_ids=error_code_ids,
        )
        boost_map = {row["failure_mode_id"]: row["error_boost"] for row in boosts}

    for row in ranked:
        fid = row["failure_mode_id"]
        if fid in boost_map:
            row["error_code_boost"] = round(boost_map[fid], 2)
            row["total_confidence"] = (row.get("total_confidence") or 0) + boost_map[fid]
            row["aggregate_confidence"] = round(
                row["total_confidence"] / max(len(symptom_ids) + len(error_code_ids), 1), 2
            )

    # Posterior (diagnostic probability) stays the primary ranking signal;
    # a machine-reported error code acts as a corroborating tie-breaker.
    ranked.sort(
        key=lambda x: (
            x.get("posterior", 0.0),
            x.get("total_confidence", 0),
            x.get("link_count", 0),
        ),
        reverse=True,
    )
    return ranked


def get_impacted_components(product_id: str, failure_mode_id: str) -> list[dict[str, Any]]:
    driver = get_driver()
    with driver.session() as session:
        result = session.run(
            """
            MATCH (p:Product {product_id: $product_id})-[:CAN_HAVE]->(fm:FailureMode {failure_mode_id: $fm_id})
                  -[r:IMPACTS_COMPONENT]->(c:Component)
            RETURN c.component_id AS component_id, c.name AS name, c.subsystem AS subsystem,
                   r.impact_severity AS impact_severity
            ORDER BY c.name
            """,
            product_id=product_id,
            fm_id=failure_mode_id,
        )
        return [dict(r) for r in result]


def get_claim_precedents(failure_mode_id: str, asset_id: str | None = None) -> list[dict[str, Any]]:
    driver = get_driver()
    query = """
        MATCH (cl:Claim)-[:CONFIRMED]->(fm:FailureMode {failure_mode_id: $fm_id})
        OPTIONAL MATCH (cl)-[:FOR_ASSET]->(a:Asset)
        OPTIONAL MATCH (cl)-[:USED_PART]->(pt:Part)
        RETURN cl.claim_id AS claim_id, cl.resolution_summary AS resolution_summary,
               cl.closed_date AS closed_date, a.asset_id AS asset_id,
               pt.part_id AS used_part_id, pt.name AS used_part_name
        ORDER BY cl.closed_date DESC LIMIT 5
    """
    with driver.session() as session:
        rows = [dict(r) for r in session.run(query, fm_id=failure_mode_id)]
    if asset_id:
        asset_matches = [r for r in rows if r.get("asset_id") == asset_id]
        if asset_matches:
            return asset_matches
    return rows[:3]


def get_historical_resolutions(product_id: str, failure_mode_id: str | None = None) -> list[dict[str, Any]]:
    driver = get_driver()
    # When a specific failure mode is requested we use a MATCH (not OPTIONAL MATCH +
    # WHERE) so only resolutions that are CONFIRMED for that exact failure mode are
    # returned. The former OPTIONAL MATCH + WHERE kept resolutions whose CONFIRMED edge
    # pointed at a *different* failure mode (returning failure_mode_name=null), which
    # caused wrong resolutions to surface in the response.
    if failure_mode_id:
        query = """
            MATCH (r:HistoricalResolution)-[:FOR_PRODUCT]->(p:Product {product_id: $product_id})
            MATCH (r)-[:CONFIRMED]->(fm:FailureMode {failure_mode_id: $failure_mode_id})
            RETURN r.resolution_id AS resolution_id, r.description AS description,
                   r.resolution_date AS resolution_date, r.technician_notes AS technician_notes,
                   r.source_system AS source_system, r.source_record_id AS source_record_id,
                   fm.name AS failure_mode_name
            ORDER BY r.resolution_date DESC
        """
    else:
        query = """
            MATCH (r:HistoricalResolution)-[:FOR_PRODUCT]->(p:Product {product_id: $product_id})
            OPTIONAL MATCH (r)-[:CONFIRMED]->(fm:FailureMode)
            RETURN r.resolution_id AS resolution_id, r.description AS description,
                   r.resolution_date AS resolution_date, r.technician_notes AS technician_notes,
                   r.source_system AS source_system, r.source_record_id AS source_record_id,
                   fm.name AS failure_mode_name
            ORDER BY r.resolution_date DESC
        """
    params: dict[str, Any] = {"product_id": product_id}
    if failure_mode_id:
        params["failure_mode_id"] = failure_mode_id
    with driver.session() as session:
        result = session.run(query, **params)
        return [dict(r) for r in result]


def get_parts_for_product(
    product_id: str,
    failure_mode_id: str | None = None,
) -> list[dict[str, Any]]:
    driver = get_driver()
    query = """
        MATCH (p:Product {product_id: $product_id})-[:CAN_HAVE]->(fm:FailureMode)
    """
    if failure_mode_id:
        query += " WHERE fm.failure_mode_id = $failure_mode_id"
    query += """
        MATCH (fm)-[:REQUIRES_PART]->(pt:Part)
        RETURN pt.part_id AS part_id, pt.name AS name,
               pt.part_number AS part_number, pt.estimated_cost_usd AS estimated_cost_usd,
               fm.failure_mode_id AS failure_mode_id, fm.name AS failure_mode_name
        ORDER BY pt.name
    """
    params: dict[str, Any] = {"product_id": product_id}
    if failure_mode_id:
        params["failure_mode_id"] = failure_mode_id

    with driver.session() as session:
        result = session.run(query, **params)
        parts = [dict(r) for r in result]

    if parts:
        return parts

    if settings.demo_mode:
        catalog = _load_json_catalog()
        for item in catalog["products"]:
            if item["product"]["product_id"] == product_id:
                return item.get("parts", [])
    return []


def diagnose(
    user_message: str,
    product_id: str | None = None,
    asset_id: str | None = None,
    crm_product_id: str | None = None,
    *,
    force_keep_context: bool = False,
    crm_context: dict[str, Any] | None = None,
) -> DiagnosisResult:
    product, asset_ctx, effective_asset_id, warnings, block_code, res_meta = resolve_product_for_diagnosis(
        user_message,
        product_id=product_id,
        asset_id=asset_id,
        crm_product_id=crm_product_id,
        force_keep_context=force_keep_context,
        crm_context=crm_context,
    )

    if block_code:
        soft = block_code.startswith("soft_")
        bound_name = (product or {}).get("name") or product_id or "selected appliance"
        return DiagnosisResult(
            product_id=(product or {}).get("product_id") or product_id or "",
            product_name=bound_name if isinstance(bound_name, str) else "Unknown",
            should_escalate=not soft,
            escalation_reason=(
                "Confirm appliance or switch registered asset before diagnosing."
                if soft
                else "Context conflict — diagnosis withheld (API / binding invariant)."
            ),
            evidence=["No graph diagnosis executed (context_blocked)"],
            warnings=warnings,
            context_blocked=True,
            context_block_code=block_code,
            recommendation_strength="Insufficient data",
            confidence=0.0,
            graph_confidence=0.0,
            language_confidence=0.0,
            asset_id=(asset_ctx or {}).get("asset_id", "") if asset_ctx else "",
            model_number=(asset_ctx or {}).get("model_number", "") if asset_ctx else "",
            sku_id=(asset_ctx or {}).get("sku_id", "") if asset_ctx else "",
            serial_number=(asset_ctx or {}).get("serial_number", "") if asset_ctx else "",
            resolution_meta=res_meta,
        )

    if not product:
        return DiagnosisResult(
            product_id="",
            product_name="Unknown",
            should_escalate=True,
            escalation_reason="Could not identify appliance type from message.",
            evidence=["No product keyword match"],
            warnings=warnings,
            context_blocked=True,
            context_block_code="product_unresolved",
            recommendation_strength="Insufficient data",
        )

    pid = product["product_id"]
    sku_id = asset_ctx.get("sku_id", "") if asset_ctx else ""
    matched_error_codes = match_error_codes(pid, user_message)
    error_code_ids = [e["error_code_id"] for e in matched_error_codes]

    matched_symptoms = match_symptoms(pid, user_message)
    # Only observed symptoms (above threshold) enter Bayesian evidence.
    symptom_ids = [s["symptom_id"] for s in matched_symptoms]
    ranked = rank_failure_modes_with_error_codes(pid, symptom_ids, error_code_ids) if symptom_ids else []

    top = ranked[0] if ranked else None
    confidence, graph_confidence, language_confidence, rec_strength, dom_ratio = _composite_confidence(
        ranked, matched_symptoms
    )

    if not matched_symptoms:
        warnings.append(
            "No symptoms matched your description strongly enough for this product. "
            "Please add more detail or confirm the appliance type."
        )
        should_escalate = True
        escalation_reason = "No confident symptom match — escalating for human review."
    else:
        critical = any(s.get("severity") == "critical" for s in matched_symptoms)
        weak_language = language_confidence < 0.35
        # Diagnostic ambiguity = no clear leader among candidate failure modes,
        # measured by the gap between the top two posteriors (a principled
        # separation signal, not a raw symptom count).
        posterior_margin = 1.0
        if len(ranked) >= 2:
            posterior_margin = (ranked[0].get("posterior", 0.0) or 0.0) - (ranked[1].get("posterior", 0.0) or 0.0)
        ambiguous = posterior_margin < settings.diagnosis_ambiguity_margin
        strong_graph = graph_confidence >= 0.85 and not ambiguous

        should_escalate = critical or (
            confidence < settings.escalation_confidence_threshold and not strong_graph and (weak_language or ambiguous)
        )
        escalation_reason = ""
        if ambiguous and not strong_graph:
            warnings.append(
                "Your description maps to more than one likely failure mode with "
                "similar probability. A technician may need to confirm which applies."
            )
        if critical:
            escalation_reason = "Critical severity symptom detected — human review required."
        elif should_escalate and weak_language:
            escalation_reason = (
                f"Language match ({language_confidence:.0%}) is weak for the catalog symptom — "
                "escalating for human review."
            )
        elif should_escalate and ambiguous:
            escalation_reason = "Multiple symptom patterns matched — escalating for human confirmation."
        elif should_escalate:
            escalation_reason = f"Overall confidence ({confidence:.0%}) below threshold — escalating to human agent."

    top_fm_id = top["failure_mode_id"] if top else None
    evidence = []
    if asset_ctx:
        evidence.append(
            f"Asset {asset_ctx['asset_id']}: {asset_ctx.get('model_number', 'N/A')} "
            f"(SKU {sku_id or 'unknown'}, serial {asset_ctx.get('serial_number', '')})"
        )
    if top:
        evidence.append(
            f"Top failure mode: {top['name']} (overall {confidence:.0%} · "
            f"graph edge {graph_confidence:.0%} · language {language_confidence:.0%})"
        )
    for ec in matched_error_codes:
        evidence.append(f"Error code match: {ec['code']} — {ec['description']}")
    for s in matched_symptoms[:3]:
        evidence.append(
            f"Symptom match: {s['description']} [{s.get('severity', 'unknown')}] "
            f"(text score {s.get('match_score', 0):.0%})"
        )

    steps = resolve_dynamic_steps(pid, top_fm_id) if top_fm_id else get_diagnostic_steps(pid)
    diagnostic_tree = get_diagnostic_tree(pid)
    resolutions = get_historical_resolutions(pid, top_fm_id)
    impacted_components = get_impacted_components(pid, top_fm_id) if top_fm_id else []
    claim_precedents = get_claim_precedents(top_fm_id, asset_id) if top_fm_id else []

    from graph.parts_predictor import predict_parts

    top_posterior = float(top.get("posterior", 1.0)) if top else 1.0
    predicted_parts = (
        predict_parts(pid, top_fm_id, sku_id=sku_id or None, fm_posterior=top_posterior) if top_fm_id else []
    )
    parts = predicted_parts or get_parts_for_product(pid, top_fm_id)

    provenance_trail: list[dict[str, Any]] = []
    if settings.enable_provenance:
        for s in matched_symptoms[:3]:
            provenance_trail.append(provenance_evidence_line("Symptom", s.get("symptom_id", ""), s))
        if top:
            fm_props = enrich_entity_props("FailureMode", top.get("failure_mode_id", ""), top)
            provenance_trail.append(provenance_evidence_line("FailureMode", top.get("failure_mode_id", ""), fm_props))
        steps_for_prov = [s for s in steps if s.get("targets_top_fm")] or list(steps)
        for step in steps_for_prov[:4]:
            step_props = enrich_entity_props("DiagnosticStep", step.get("step_id", ""), step)
            provenance_trail.append(provenance_evidence_line("DiagnosticStep", step.get("step_id", ""), step_props))
        for part in predicted_parts[:2]:
            part_props = enrich_entity_props("Part", part.get("part_id", ""), part)
            provenance_trail.append(provenance_evidence_line("Part", part.get("part_id", ""), part_props))
        for res in resolutions[:1]:
            res_props = enrich_entity_props("HistoricalResolution", res.get("resolution_id", ""), res)
            provenance_trail.append(
                provenance_evidence_line("HistoricalResolution", res.get("resolution_id", ""), res_props)
            )

    return DiagnosisResult(
        product_id=pid,
        product_name=product["name"],
        matched_symptoms=matched_symptoms,
        ranked_failure_modes=ranked[:3],
        diagnostic_steps=steps,
        parts=parts,
        historical_resolutions=resolutions,
        confidence=confidence,
        graph_confidence=graph_confidence,
        language_confidence=language_confidence,
        recommendation_strength=rec_strength,
        posterior_dominance_ratio=dom_ratio,
        traversed_symptom_ids=symptom_ids,
        traversed_fm_id=top_fm_id or "",
        should_escalate=should_escalate,
        escalation_reason=escalation_reason,
        evidence=evidence,
        provenance_trail=provenance_trail,
        asset_id=asset_ctx.get("asset_id", "") if asset_ctx else "",
        model_number=asset_ctx.get("model_number", "") if asset_ctx else "",
        sku_id=sku_id,
        serial_number=asset_ctx.get("serial_number", "") if asset_ctx else "",
        matched_error_codes=matched_error_codes,
        impacted_components=impacted_components,
        predicted_parts=predicted_parts,
        context_blocked=False,
        context_block_code="",
        resolution_meta=res_meta,
        claim_precedents=claim_precedents,
        diagnostic_tree=diagnostic_tree,
        warnings=warnings,
    )


def format_diagnosis_response(result: DiagnosisResult) -> str:
    if result.context_blocked:
        soft = result.context_block_code.startswith("soft_")
        if soft:
            lines = [
                "**Confirm appliance**",
                "",
                "Your note may describe a different appliance than the one selected on this account.",
                "",
            ]
            if result.warnings:
                lines.extend([f"- {w}" for w in result.warnings])
            lines.extend(
                [
                    "",
                    "**What to do:**",
                    "1. Switch to the correct registered appliance for this customer, or",
                    "2. Confirm “Keep this appliance” if the selected unit is correct.",
                    "",
                    "Diagnosis did not run yet — product scope stays bound to the registered asset.",
                ]
            )
            return "\n".join(lines)
        lines = [
            "**Diagnosis withheld — binding conflict**",
            "",
            "The request mixed inconsistent product and asset identifiers (API invariant).",
            "",
        ]
        if result.warnings:
            lines.extend([f"- {w}" for w in result.warnings])
        return "\n".join(lines)

    if not result.product_id:
        return (
            "I couldn't identify which appliance you're asking about. "
            "Please mention washing machine, dishwasher, or microwave."
        )

    lines = []
    if result.warnings:
        lines.extend(["**⚠️ Context Notes:**"] + [f"- {w}" for w in result.warnings] + [""])

    lines.append(f"**Product:** {result.product_name}")
    if result.model_number or result.asset_id:
        lines.append(
            f"**Asset:** {result.asset_id or 'N/A'} · Model {result.model_number or 'N/A'} "
            f"· SKU {result.sku_id or 'N/A'}"
        )
    lines.extend(["", "**Matched Symptoms:**"])
    for s in result.matched_symptoms[:3]:
        lines.append(f"- {s['description']} (severity: {s['severity']}, text match: {s.get('match_score', 0):.0%})")

    if result.matched_error_codes:
        lines.extend(["", "**Matched Error Codes:**"])
        for ec in result.matched_error_codes:
            lines.append(f"- {ec['code']}: {ec['description']}")

    if result.ranked_failure_modes:
        top = result.ranked_failure_modes[0]
        lines.extend(
            [
                "",
                f"**Most Likely Diagnosis (Failure Mode):** {top['name']}",
                f"- {top['description']}",
                f"- Estimated repair time: {top['repair_minutes']} minutes",
                f"- Safety: {top['safety_notes']}",
                f"- Diagnostic confidence: {result.confidence:.0%} "
                f"(Bayesian posterior P(failure|symptoms) · strongest graph link "
                f"{result.graph_confidence:.0%} · language match {result.language_confidence:.0%})",
            ]
        )
        if top.get("action_priority"):
            lines.append(
                f"- FMEA risk: Action Priority **{top.get('action_priority')}** · "
                f"RPN {top.get('rpn')} (S{top.get('severity_rating')} × "
                f"O{top.get('occurrence_rating')} × D{top.get('detection_rating')})"
            )
        if len(result.ranked_failure_modes) > 1:
            lines.append("- Differential (ranked by posterior):")
            for fm in result.ranked_failure_modes[:3]:
                lines.append(
                    f"  - {fm['name']} — {float(fm.get('posterior', 0)):.0%} (AP {fm.get('action_priority', '?')})"
                )

    if result.impacted_components:
        lines.extend(["", "**Impacted Components (BOM):**"])
        for comp in result.impacted_components:
            lines.append(f"- {comp['name']} ({comp['subsystem']}) — {comp.get('impact_severity', 'impact')}")

    if result.diagnostic_steps:
        lines.extend(["", "**Targeted Troubleshooting Steps:**"])
        # Use sequential display numbering (1, 2, 3…) rather than the graph
        # step_order property, which reflects order across ALL product steps.
        # When only targeted steps for a failure mode are returned, step_order
        # may start at 2+ and confuse the reader.
        for display_num, step in enumerate(result.diagnostic_steps[:4], 1):
            lines.append(f"{display_num}. {step['description']}")

    parts = result.predicted_parts or result.parts
    if parts:
        lines.extend(["", "**Predicted Parts Required:**"])
        for part in parts[:4]:
            score = part.get("prediction_score")
            score_txt = f" · replacement probability {score:.0%}" if score else ""
            qty = part.get("quantity", 1)
            lines.append(
                f"- {part['name']} · `{part.get('part_number', '')}` · "
                f"qty {qty} · ${part.get('estimated_cost_usd', 0):.2f}{score_txt}"
            )
            if part.get("impacted_components"):
                lines.append(f"  - Impacts: {', '.join(part['impacted_components'])}")
            if part.get("claim_precedents"):
                lines.append(f"  - Prior claim: {', '.join(part['claim_precedents'])}")

    if result.claim_precedents:
        lines.extend(["", "**Warranty Claim Precedents:**"])
        for cl in result.claim_precedents[:2]:
            lines.append(f"- {cl.get('claim_id')}: {cl.get('resolution_summary', '')}")

    if result.historical_resolutions:
        lines.extend(["", "**Similar Past Resolutions:**"])
        for res in result.historical_resolutions[:2]:
            lines.append(f"- {res['description']} ({res['resolution_date']})")

    if result.should_escalate:
        lines.extend(
            [
                "",
                f"**Escalation:** {result.escalation_reason}",
                "A human agent will review this case.",
            ]
        )
    else:
        lines.extend(["", "**Status:** Resolved at automated tier (no escalation needed)."])

    lines.extend(["", "**Graph Evidence:**"] + [f"- {e}" for e in result.evidence])
    if result.provenance_trail:
        lines.extend(["", "**Source Traceability:**"])
        lines.extend(format_traceability_lines(result.provenance_trail))
    return "\n".join(lines)
