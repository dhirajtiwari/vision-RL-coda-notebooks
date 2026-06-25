from functools import lru_cache

from neo4j import GraphDatabase, Driver

from config.settings import settings


@lru_cache
def get_driver() -> Driver:
    return GraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_user, settings.neo4j_password),
    )


def verify_connection() -> bool:
    driver = get_driver()
    try:
        driver.verify_connectivity()
        return True
    except Exception:
        return False