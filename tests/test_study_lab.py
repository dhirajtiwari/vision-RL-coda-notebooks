"""Study Lab API + generator smoke tests."""

from __future__ import annotations

from fastapi.testclient import TestClient

from api.main import app
from study.generator import generate_module_from_text
from study.store import ensure_seeded, list_modules


def test_seed_modules_exist():
    ensure_seeded()
    mods = list_modules()
    ids = {m["id"] for m in mods}
    assert "01-rdf-owl-tbox-abox" in ids
    assert "03-langgraph-cypher-agent" in ids


def test_generate_from_markdown_has_beats():
    mod = generate_module_from_text(
        """# My Topic

Story paragraph long enough to become the memory anchor for the learner.

```python
def hello():
    return 1
```
""",
        title="My Topic",
    )
    assert mod.beats
    assert mod.beats[0].language == "python"
    assert mod.beats[0].code
    assert isinstance(mod.beats[0].line_quiz, list)


def test_study_api_list_and_detail():
    client = TestClient(app)
    r = client.get("/study/modules")
    assert r.status_code == 200
    mods = r.json()["modules"]
    assert len(mods) >= 5
    mid = mods[0]["id"]
    d = client.get(f"/study/modules/{mid}")
    assert d.status_code == 200
    assert d.json()["title"]


def test_study_grade_fill():
    client = TestClient(app)
    # use known seed beat with fill blanks
    mod = client.get("/study/modules/01-rdf-owl-tbox-abox").json()
    beat = next(b for b in mod["beats"] if b.get("fill_blanks"))
    answers = {bl["id"]: bl["answer"] for bl in beat["fill_blanks"]["blanks"]}
    g = client.post(
        "/study/grade/fill-blanks",
        json={"module_id": "01-rdf-owl-tbox-abox", "beat_id": beat["id"], "answers": answers},
    )
    assert g.status_code == 200
    assert g.json()["score"] == 1.0
