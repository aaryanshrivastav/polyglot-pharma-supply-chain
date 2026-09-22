"""
Integration Tests: Neo4j Knowledge Graph.
Validates multi-echelon node labels and 3-hop Cypher path traversals.
"""

import os
import pytest
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://127.0.0.1:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "pharma_graph_pass")


@pytest.fixture(scope="module")
def neo4j_driver():
    try:
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD), connection_timeout=1.5)
        with driver.session() as s:
            s.run("RETURN 1").single()
        yield driver
        driver.close()
    except Exception as e:
        pytest.skip(f"Neo4j not reachable at {NEO4J_URI}: {e}")


@pytest.mark.integration
class TestNeo4jGraphIntegration:
    def test_node_types_when_queried_should_contain_all_five_core_labels(self, neo4j_driver):
        # Arrange & Act
        with neo4j_driver.session() as session:
            res = session.run("MATCH (n) RETURN DISTINCT head(labels(n)) AS label").data()
            labels = {r["label"] for r in res if r["label"]}

            # Assert
            for expected in ["Manufacturer", "Distributor", "Pharmacy", "Drug", "Ingredient"]:
                assert expected in labels, f"Missing node label in graph: {expected}"

    def test_multi_hop_traversal_when_queried_should_resolve_end_to_end_supply_path(self, neo4j_driver):
        # Arrange
        query = """
        MATCH (m:Manufacturer)-[:SUPPLIES]->(d:Distributor)-[:DISTRIBUTES_TO]->(p:Pharmacy)
        RETURN m.name AS mfr, d.name AS dist, p.name AS pharm
        LIMIT 1
        """

        # Act
        with neo4j_driver.session() as session:
            result = session.run(query).data()

            # Assert
            assert len(result) > 0, "Expected at least one valid 3-hop supply path"
            assert result[0]["mfr"] is not None
            assert result[0]["dist"] is not None
            assert result[0]["pharm"] is not None
