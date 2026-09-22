"""
Unit Tests: Graph SPOF & Centrality Analytics Module.
Validates multi-echelon graph network construction, betweenness centrality,
and bottleneck node ranking in ml/spof_centrality.py.
"""

import pytest
import networkx as nx
from ml.spof_centrality import build_supply_chain_graph, compute_spof_metrics, SPOFAnalyzer


@pytest.mark.unit
class TestSPOFCentralityAnalytics:
    def test_build_supply_chain_graph_when_edges_provided_should_construct_directed_network(self):
        # Arrange
        edges = [
            {"source_id": "EST-0001", "target_id": "DIST-001", "relationship": "SUPPLIES", "weight": 1.0},
            {"source_id": "DIST-001", "target_id": "PHARM-0001", "relationship": "SHIPS_TO", "weight": 1.0},
            {"source_id": "DIST-001", "target_id": "PHARM-0002", "relationship": "SHIPS_TO", "weight": 1.0},
        ]

        # Act
        G = build_supply_chain_graph(edges)

        # Assert
        assert isinstance(G, nx.DiGraph), "Constructed graph must be a directed graph (nx.DiGraph)"
        assert G.number_of_nodes() == 4
        assert G.number_of_edges() == 3

    def test_compute_spof_metrics_when_hub_bottleneck_topology_should_rank_bridge_node_highest(self):
        # Arrange: Bowtie / Hourglass topology where DIST-HUB is the sole bridge
        edges = [
            {"source_id": "EST-0001", "target_id": "DIST-HUB", "weight": 1.0},
            {"source_id": "EST-0002", "target_id": "DIST-HUB", "weight": 1.0},
            {"source_id": "DIST-HUB", "target_id": "PHARM-0001", "weight": 1.0},
            {"source_id": "DIST-HUB", "target_id": "PHARM-0002", "weight": 1.0},
        ]
        G = build_supply_chain_graph(edges)

        # Act
        rankings = compute_spof_metrics(G)

        # Assert
        assert len(rankings) == 5
        top_node = rankings[0]
        assert top_node["node_id"] == "DIST-HUB", "Sole bridge distributor must be ranked #1 bottleneck"
        assert top_node["betweenness_centrality"] > 0.0
        assert top_node["spof_risk_index"] > 0.5
        assert top_node["classification"] in {"CRITICAL_BOTTLENECK", "HIGH_CONCENTRATION"}

    def test_spof_analyzer_when_dry_run_mode_should_rank_staged_topology_nodes(self):
        # Arrange
        analyzer = SPOFAnalyzer(dry_run=True)

        # Act
        rankings = analyzer.run_analysis(top_k=5)
        analyzer.close()

        # Assert
        assert len(rankings) > 0, "Expected non-empty SPOF rankings list"
        top = rankings[0]
        assert "node_id" in top
        assert "spof_risk_index" in top
        assert "classification" in top
