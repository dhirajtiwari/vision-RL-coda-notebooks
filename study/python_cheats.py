"""Python cheat-codes for a non-Python developer — one place, per topic.

Each entry is a :class:`PyNuance`: a memorizable RULE + why it matters + a tiny
runnable example + the beginner GOTCHA it prevents. These attach to the matching
lesson module at serve time (see ``study.store.load_module``), so every topic's
code comes with "why is this Python written this way" explanations.

Sources this distills (all real, worth reading):
  * Fluent Python, 2nd ed. — Luciano Ramalho (idioms, data model)
  * Real Python (realpython.com) — practical tutorials
  * Python docs / PEP 8 (style) / PEP 20 (Zen of Python) / PEP 484 (typing)
  * Effective Python — Brett Slatkin (90 specific ways)
"""

from __future__ import annotations

from study.models import PyNuance

# Fundamentals every beginner needs, shown alongside the simplest topic.
_ESSENTIALS = [
    PyNuance(
        label="Triple = a tuple",
        category="syntax",
        rule="Wrap grouped values in parentheses: (a, b, c) is one tuple.",
        why="rdflib/Neo4j pass a whole record as ONE argument — the extra parens matter.",
        code="g.add((WD.Product, RDF.type, OWL.Class))  # ONE tuple arg, note ((...))",
        gotcha="g.add(WD.Product, RDF.type, OWL.Class) → TypeError: add() takes 1 positional arg.",
    ),
    PyNuance(
        label="f-string",
        category="syntax",
        rule="Put an f before a string to drop variables inside {}.",
        why="Readable interpolation; the go-to way to build text.",
        code='name = "wm-001"\nprint(f"product {name} loaded")  # product wm-001 loaded',
        gotcha="Forgetting the f → literal 'product {name}'. And NEVER f-string SQL/Cypher (injection).",
    ),
    PyNuance(
        label="Import what you use",
        category="syntax",
        rule="from module import Thing  → then use Thing directly.",
        why="Keeps names short; the top of every file declares dependencies.",
        code="from rdflib import Graph, Namespace  # now Graph() works",
        gotcha="import rdflib then Graph() fails — you'd need rdflib.Graph().",
    ),
    PyNuance(
        label="with = auto-cleanup",
        category="idiom",
        rule="with open(...) as f:  closes the file even if the block errors.",
        why="Context managers guarantee cleanup (files, DB sessions, locks).",
        code='with open("data.json") as f:\n    text = f.read()  # f auto-closed here',
        gotcha="Opening without `with` leaks file handles / DB connections.",
    ),
    PyNuance(
        label="Truthiness",
        category="idiom",
        rule="Empty things are falsy: '', [], {}, 0, None all act like False.",
        why="`if items:` reads as 'if there are items' — no len() needed.",
        code='items = []\nif not items:\n    print("nothing yet")',
        gotcha="`if x == None` works but `if x is None` is the correct idiom.",
    ),
]

PYTHON_CHEATS: dict[str, list[PyNuance]] = {
    "01-tbox-abox-simple": _ESSENTIALS
    + [
        PyNuance(
            label="Namespace attribute",
            category="idiom",
            rule="WD.Product builds the IRI wd:Product; WD['wm-001'] for names with dashes.",
            why="Attribute access is sugar; use [] when the name isn't a valid identifier.",
            code='WD = Namespace("https://ex.org/wd#")\nWD.Product        # ok\nWD["wm-001"]      # dash → must use []',
            gotcha="WD.wm-001 is read as (WD.wm) - 001 → error. Use WD['wm-001'].",
        ),
        PyNuance(
            label="Literal vs URIRef",
            category="gotcha",
            rule="Literal('text') = a value; WD.Thing = an identity (node).",
            why="RDF needs to know if the object is data or another resource.",
            code='g.add((WD.Product, RDFS.label, Literal("Product")))  # value\ng.add((s, RDF.type, WD.Product))                     # node',
            gotcha="Passing a plain str where a URIRef is expected changes the meaning.",
        ),
    ],
    "02-cypher-create-read": [
        PyNuance(
            label="Triple-quoted string",
            category="syntax",
            rule='Use """...""" for multi-line text like a Cypher query.',
            why="Keeps the query readable across lines with no \\n noise.",
            code='q = """\nMATCH (p:Product {id:$id})\nRETURN p\n"""',
            gotcha="Single quotes can't span lines — SyntaxError on the newline.",
        ),
        PyNuance(
            label="Parameterize, never f-string queries",
            category="gotcha",
            rule="Pass values as params ($id), not by building the string.",
            why="Prevents injection AND lets the DB cache the query plan.",
            code='session.run(q, id="wm-001")   # SAFE\n# session.run(f"...{user}")   # NEVER',
            gotcha="f-string a user value into Cypher/SQL = classic injection hole.",
        ),
        PyNuance(
            label="Iterate results",
            category="idiom",
            rule="A result is iterable; loop rows or list-comprehend them.",
            why="Pythonic extraction of records.",
            code='names = [r["name"] for r in session.run(q)]',
            gotcha="Results can be consumed once — re-iterating yields nothing.",
        ),
    ],
    "03-etl-pipeline": [
        PyNuance(
            label="Type hints",
            category="typing",
            rule="def f(x: int) -> str:  documents inputs/outputs (not enforced at runtime).",
            why="Editors autocomplete + catch bugs; readers know the shape.",
            code="def build(pim: dict) -> list[dict]:\n    return pim['products']",
            gotcha="Hints don't validate — use pydantic/dataclasses when you need real checks.",
        ),
        PyNuance(
            label="List / dict comprehension",
            category="idiom",
            rule="[f(x) for x in xs if cond]  builds a list in one readable line.",
            why="Replaces manual append loops; faster and clearer.",
            code="ids = [p['id'] for p in products if p.get('active')]",
            gotcha="Deeply nested comprehensions get unreadable — fall back to a loop.",
        ),
        PyNuance(
            label="dict.get with default",
            category="gotcha",
            rule="d.get('k', default) never raises; d['k'] raises KeyError if missing.",
            why="ETL data is messy — .get() survives missing keys.",
            code="qty = row.get('qty', 0)  # 0 if absent",
            gotcha="row['qty'] on absent key → KeyError crashes the pipeline.",
        ),
        PyNuance(
            label="pathlib over os.path",
            category="stdlib",
            rule="Path('a') / 'b' / 'c.json' builds paths with the / operator.",
            why="Cross-platform, readable, has .exists()/.read_text().",
            code='from pathlib import Path\np = Path("data") / "catalog.json"\ntext = p.read_text()',
            gotcha='"data" + "/" + name breaks on Windows and double-slashes.',
        ),
        PyNuance(
            label="try / except / finally",
            category="idiom",
            rule="Catch the specific error; use finally (or with) for cleanup.",
            why="One bad record shouldn't kill the whole batch.",
            code="try:\n    load(row)\nexcept ValueError as e:\n    log.warning('skip %s', e)",
            gotcha="Bare `except:` hides real bugs — catch the narrowest type you expect.",
        ),
    ],
    "04-caching": [
        PyNuance(
            label="Decorator = wrapper",
            category="idiom",
            rule="@lru_cache above a function remembers results per arguments.",
            why="Free memoization for pure, repeat-called functions.",
            code="from functools import lru_cache\n@lru_cache(maxsize=512)\ndef fib(n): return n if n<2 else fib(n-1)+fib(n-2)",
            gotcha="Only cache PURE functions; caching one with side effects hides them.",
        ),
        PyNuance(
            label="dict as a cache",
            category="idiom",
            rule="get→miss→compute→store is the whole cache pattern.",
            why="Understand the manual version before reaching for a library.",
            code="cache = {}\ndef get(k):\n    if k not in cache:\n        cache[k] = compute(k)\n    return cache[k]",
            gotcha="Unbounded dict caches leak memory — add TTL/size limits in real code.",
        ),
        PyNuance(
            label="Keyword vs positional args",
            category="syntax",
            rule="f(ttl=90) is clearer than f(90) and order-independent.",
            why="Cache keys/config read better with names.",
            code="cache.set(key, value, ttl=90)",
            gotcha="Mixing up positional args silently swaps values.",
        ),
    ],
    "05-multithreading": [
        PyNuance(
            label="ThreadPoolExecutor + with",
            category="idiom",
            rule="with ThreadPoolExecutor() as ex: ex.map(fn, items) runs I/O in parallel.",
            why="Simplest safe concurrency for network/file work.",
            code="from concurrent.futures import ThreadPoolExecutor\nwith ThreadPoolExecutor(max_workers=4) as ex:\n    results = list(ex.map(fetch, urls))",
            gotcha="Forgetting `with` leaks threads; not list()-ing ex.map defers exceptions.",
        ),
        PyNuance(
            label="The GIL rule",
            category="gotcha",
            rule="Threads help I/O-bound work, NOT CPU-bound (use processes for CPU).",
            why="Python's GIL lets one thread run Python bytecode at a time.",
            code="# I/O (waiting on network) → threads ✅\n# heavy math loops → ProcessPoolExecutor ✅",
            gotcha="Threading a CPU loop gives ~zero speedup and adds complexity.",
        ),
        PyNuance(
            label="Always release in finally",
            category="idiom",
            rule="Acquire a lock/slot, do work, release in finally (or use `with lock`).",
            why="A lock never released deadlocks everything after it.",
            code="with lock:\n    counter += 1   # released automatically",
            gotcha="lock.acquire() without a guaranteed release → hung program.",
        ),
    ],
    "06-partitioning": [
        PyNuance(
            label="Modulo for buckets",
            category="idiom",
            rule="hash(key) % N picks one of N shards deterministically.",
            why="Same key always lands in the same partition.",
            code="shard = hash(product_id) % num_shards",
            gotcha="Python's str hash is randomized per run — use hashlib for stable shards.",
        ),
        PyNuance(
            label="defaultdict groups",
            category="stdlib",
            rule="defaultdict(list) auto-creates an empty list per new key.",
            why="Group items without checking 'if key in d' every time.",
            code="from collections import defaultdict\nby_family = defaultdict(list)\nfor p in products:\n    by_family[p['family']].append(p)",
            gotcha="Plain dict[key].append on a missing key → KeyError.",
        ),
    ],
    "07-retrieval-bayes": [
        PyNuance(
            label="sum() + comprehension",
            category="idiom",
            rule="sum(x for x in xs) adds without building a temp list.",
            why="Clean math over collections; the () makes a lazy generator.",
            code="total = sum(w for w in weights)",
            gotcha="Integer division: 3/2 == 1.5 (float) but 3//2 == 1 (floor).",
        ),
        PyNuance(
            label="Normalize to probabilities",
            category="idiom",
            rule="Divide each score by the total so they sum to 1.",
            why="Turns raw scores into a comparable posterior.",
            code="tot = sum(scores.values()) or 1\nprob = {k: v/tot for k, v in scores.items()}",
            gotcha="Dividing by zero when tot==0 → guard with `or 1`.",
        ),
        PyNuance(
            label="max with key=",
            category="idiom",
            rule="max(items, key=lambda x: x.score) picks the best by a field.",
            why="One line to rank the top candidate.",
            code="best = max(candidates, key=lambda c: c['posterior'])",
            gotcha="max([]) raises ValueError — pass default= or check emptiness.",
        ),
    ],
    "08-langgraph-agent": [
        PyNuance(
            label="TypedDict = typed dict",
            category="typing",
            rule="A dict whose keys/value-types are declared for the editor.",
            why="LangGraph state is a plain dict with known fields.",
            code="from typing import TypedDict\nclass State(TypedDict):\n    messages: list",
            gotcha="It's still a normal dict at runtime — no validation happens.",
        ),
        PyNuance(
            label="Annotated reducer",
            category="typing",
            rule="Annotated[list, operator.add] tells LangGraph to APPEND, not replace.",
            why="Controls how parallel node outputs merge into state.",
            code="from typing import Annotated\nimport operator\nmessages: Annotated[list, operator.add]",
            gotcha="Without the reducer, each node overwrites messages (history lost).",
        ),
        PyNuance(
            label="@tool decorator",
            category="idiom",
            rule="@tool turns a plain function into an LLM-callable tool with a schema.",
            why="The docstring + type hints become the tool's contract.",
            code="@tool\ndef query_graph(q: str) -> str:\n    '''Query the KG.'''\n    return run(q)",
            gotcha="No docstring → the model doesn't know when to call it.",
        ),
        PyNuance(
            label="pydantic BaseModel",
            category="typing",
            rule="Subclass BaseModel to get validation + .model_dump() for free.",
            why="Validated tool args and API bodies.",
            code="from pydantic import BaseModel\nclass In(BaseModel):\n    user_input: str",
            gotcha="Pydantic v2 uses model_dump()/model_validate(), not the v1 dict()/parse_obj().",
        ),
    ],
    "09-shacl-gates": [
        PyNuance(
            label="Return a tuple",
            category="idiom",
            rule="return ok, report  hands back multiple values at once.",
            why="Validation returns pass/fail AND the details.",
            code="def validate(g):\n    return conforms, text\nok, msg = validate(g)  # unpack",
            gotcha="Forgetting to unpack: `res = validate(g)` gives you the tuple, not ok.",
        ),
        PyNuance(
            label="Boolean gate",
            category="idiom",
            rule="if not conforms: raise / block — fail closed on invalid data.",
            why="Bad data must never reach the graph.",
            code="if not conforms:\n    raise ValueError(f'shape violation: {text}')",
            gotcha="Logging a warning but continuing = the bug you were trying to prevent.",
        ),
    ],
}


def cheats_for(module_id: str) -> list[PyNuance]:
    """Python cheat-codes for a module id (empty list if none defined)."""
    return PYTHON_CHEATS.get(module_id, [])
