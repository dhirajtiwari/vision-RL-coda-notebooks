"""Study Lab — grounded curriculum + API smoke tests."""

from __future__ import annotations

from fastapi.testclient import TestClient

from api.main import app
from study.generator import generate_module_from_text
from study.seed_curriculum import write_all_seeds
from study.store import list_modules, load_module


def test_grounded_seeds_exist():
    write_all_seeds(wipe_old=True)
    mods = list_modules()
    ids = {m["id"] for m in mods}
    assert "01-tbox-abox-simple" in ids
    assert "03-etl-pipeline" in ids
    assert "04-caching" in ids
    assert "05-multithreading" in ids
    assert "06-partitioning" in ids
    # platform expansion
    assert "10-llmops-disciplines" in ids
    assert "13-cicd-github-actions" in ids
    assert "15-k8s-helm-rollouts" in ids
    assert "17-finops-cost" in ids
    assert "20-synthetic-mlops-images" in ids
    # no auto notebook module in grounded set
    assert "08-notebook-auto" not in ids
    m = load_module("03-etl-pipeline")
    assert m.say_aloud
    assert m.cheat_sheet
    assert m.grounded is True
    assert len(m.beats) >= 2


def test_generate_from_markdown_marked_ungrounded():
    mod = generate_module_from_text(
        """# My Topic

Enough story text to act as a memory anchor for the learner path.

```python
def hello():
    return 1
```
""",
        title="My Topic",
    )
    assert mod.beats
    assert mod.grounded is False


def test_study_api_list_and_etl_module():
    write_all_seeds(wipe_old=True)
    client = TestClient(app)
    r = client.get("/study/modules")
    assert r.status_code == 200
    mods = r.json()["modules"]
    assert any(m["id"] == "03-etl-pipeline" for m in mods)
    d = client.get("/study/modules/04-caching")
    assert d.status_code == 200
    body = d.json()
    assert "TTL" in body["story"] or any("TTL" in (c.get("term") or "") for c in body.get("cheat_sheet") or [])


def test_study_grade_fill_on_grounded():
    write_all_seeds(wipe_old=True)
    client = TestClient(app)
    mod = client.get("/study/modules/01-tbox-abox-simple").json()
    beat = next(b for b in mod["beats"] if b.get("fill_blanks"))
    answers = {bl["id"]: bl["answer"] for bl in beat["fill_blanks"]["blanks"]}
    g = client.post(
        "/study/grade/fill-blanks",
        json={"module_id": "01-tbox-abox-simple", "beat_id": beat["id"], "answers": answers},
    )
    assert g.status_code == 200
    assert g.json()["score"] == 1.0


def test_flashcards_deck_has_5wh_and_sources():
    from study.flashcards_deck import load_deck, write_deck

    write_deck()
    deck = load_deck()
    assert len(deck) >= 60
    sample = next(c for c in deck if c.id == "fc-tbox")
    assert sample.what and sample.how and sample.why
    assert sample.sources
    assert any("w3.org" in (s.url or "") for s in sample.sources)
    assert any(c.id == "fc-llmops-map" for c in deck)
    assert any(c.track == "finops" for c in deck)
    assert any(c.track == "cicd" for c in deck)
    # indexing + delta scale cards
    assert any(c.id == "fc-unique-constraint-index" for c in deck)
    assert any(c.id == "fc-entity-delta" for c in deck)
    idx = next(c for c in deck if c.id == "fc-unique-constraint-index")
    assert idx.what and idx.how and idx.where and idx.code
    assert idx.sources

    client = TestClient(app)
    r = client.get("/study/flashcards?track=foundations")
    assert r.status_code == 200
    body = r.json()
    assert body["count"] >= 1
    assert body["cards"][0]["what"]


def test_masterclasses_include_turtle_and_graph_ops():
    """Turtle guide must stay registered; graph ops is a sibling masterclass."""
    client = TestClient(app)
    r = client.get("/study/masterclasses")
    assert r.status_code == 200
    ids = {m["id"] for m in r.json()["masterclasses"]}
    assert "mc-01-rdf-owl-ontology-turtle" in ids
    assert "mc-02-smart-cypher-agent" in ids
    assert "mc-03-graph-ops-index-delta-scale" in ids

    turtle = client.get("/study/masterclasses/mc-01-rdf-owl-ontology-turtle")
    assert turtle.status_code == 200
    body = turtle.json()["body"]
    assert "Car Diagnostics RDF/OWL Ontology" in body
    assert "Prefixes" in body or "prefixes" in body.lower() or "TBox" in body

    ops = client.get("/study/masterclasses/mc-03-graph-ops-index-delta-scale")
    assert ops.status_code == 200
    assert "create_constraints" in ops.json()["body"]
    assert "Seek" in ops.json()["body"]

    cards = client.get("/study/masterclasses/mc-03-graph-ops-index-delta-scale/cards")
    assert cards.status_code == 200
    payload = cards.json()
    assert payload["counts"]["total"] >= 10
    assert payload["counts"]["blanks"] >= 1
    sample = payload["cards"][0]
    assert sample["front"]
    assert sample.get("what")  # 5W+H on graph ops cards
    # Turtle cards still load; enrichment must not wipe fronts
    t_cards = client.get("/study/masterclasses/mc-01-rdf-owl-ontology-turtle/cards")
    assert t_cards.status_code == 200
    fronts = [c["front"] for c in t_cards.json()["cards"]]
    assert any("7-beat" in f or "TBox" in f for f in fronts)
    enriched = [c for c in t_cards.json()["cards"] if c.get("what")]
    assert len(enriched) >= 5
