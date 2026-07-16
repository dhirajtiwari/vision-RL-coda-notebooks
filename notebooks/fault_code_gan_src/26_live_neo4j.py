# Optional: live Neo4j query if the dual-graph demo stack is up
# (docker compose from repo — production bolt usually localhost:7687)


def try_live_neo4j(code: str, product_id: str = "wm-001"):
    try:
        from neo4j import GraphDatabase
    except ImportError:
        print("neo4j driver not installed")
        return None
    uri = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
    user = os.environ.get("NEO4J_USER", "neo4j")
    password = os.environ.get("NEO4J_PASSWORD", "password")
    query = (
        "MATCH (p:Product {product_id: $product_id})-[:HAS_ERROR_CODE]->(ec:ErrorCode) "
        "WHERE toUpper(ec.code) = toUpper($code) "
        "OPTIONAL MATCH (ec)-[r:INDICATES]->(fm:FailureMode) "
        "RETURN ec.code AS code, ec.description AS description, "
        "collect({fm: fm.failure_mode_id, conf: r.confidence}) AS failure_modes"
    )
    try:
        driver = GraphDatabase.driver(uri, auth=(user, password))
        with driver.session() as session:
            rec = session.run(query, product_id=product_id, code=code).single()
        driver.close()
        if rec is None:
            print(
                f"No live hit for product={product_id} code={code} "
                "(graph empty or wrong product_id)"
            )
            return None
        data = dict(rec)
        print("Live Neo4j hit:", data)
        return [data]
    except Exception as exc:  # noqa: BLE001 — demo optional path
        print(f"Live Neo4j unavailable ({exc}). Offline Cypher templates above still apply.")
        return None


# Uncomment when Neo4j is running and product ABox is loaded:
# try_live_neo4j("5E", product_id="wm-001")
print("Live Neo4j helper defined as try_live_neo4j(code, product_id).")
