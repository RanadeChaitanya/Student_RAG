import json

import pytest

from studob.graph.store import ConceptGraphStore


@pytest.fixture
def graph():
    store = ConceptGraphStore()
    store.load_from_json("data/concept_graph.json")
    return store


class TestConceptGraphStore:
    def test_load_json(self, graph):
        nodes = graph.get_all_nodes()
        assert len(nodes) > 0

    def test_get_node_found(self, graph):
        node = graph.get_node("newtons-laws")
        assert node.display_name == "Newton's Laws"
        assert node.subject == "Physics"

    def test_get_node_not_found(self, graph):
        with pytest.raises(KeyError):
            graph.get_node("nonexistent")

    def test_get_prerequisites(self, graph):
        prereqs = graph.get_prerequisites("integration")
        assert len(prereqs) > 0
        assert any(n.id == "differentiation" for n in prereqs)

    def test_traverse_upstream(self, graph):
        upstream = graph.traverse_upstream("integration")
        assert len(upstream) > 0

    def test_get_related_concepts(self, graph):
        related = graph.get_related_concepts("newtons-laws", depth=1)
        assert len(related) > 0

    def test_search_nodes(self, graph):
        matches = graph.search_nodes("Newton")
        assert len(matches) > 0

    def test_get_siblings(self, graph):
        siblings = graph.get_siblings("kinematics-2d")
        assert len(siblings) > 0
        assert all(s.topic == siblings[0].topic for s in siblings)

    def test_find_shortest_path(self, graph):
        path = graph.find_shortest_path("kinematics-1d", "physics-basics")
        assert len(path) > 0
        assert path[0].id == "kinematics-1d"
        assert path[-1].id == "physics-basics"

    def test_empty_graph_warning(self, tmp_path):
        store = ConceptGraphStore(str(tmp_path / "missing.json"))
        assert len(store.get_all_nodes()) == 0

    def test_load_custom_graph(self, tmp_path):
        data = {
            "nodes": [
                {
                    "id": "a",
                    "subject": "X",
                    "topic": "Y",
                    "subtopic": "Z",
                    "display_name": "A",
                    "difficulty": 1,
                    "prerequisites": [],
                }
            ],
            "edges": [],
        }
        f = tmp_path / "custom.json"
        f.write_text(json.dumps(data))
        store = ConceptGraphStore(str(f))
        assert len(store.get_all_nodes()) == 1
