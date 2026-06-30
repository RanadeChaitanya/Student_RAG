import json
from collections import deque

from studob.graph.schema import ConceptEdge, ConceptNode
from studob.logging_setup import get_logger

logger = get_logger("graph.store")


class ConceptGraphStore:
    def __init__(self, data_path: str | None = None):
        self._nodes: dict[str, ConceptNode] = {}
        self._edges: list[ConceptEdge] = []
        self._adjacency: dict[str, list[ConceptEdge]] = {}
        if data_path is not None:
            self.load_from_json(data_path)

    def load_from_json(self, path: str) -> None:
        import os

        if not os.path.exists(path):
            logger.warning("Concept graph file not found, using empty graph", extra={"path": path})
            return
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        self._nodes.clear()
        self._edges.clear()
        self._adjacency.clear()
        for node_data in data.get("nodes", []):
            node = ConceptNode(
                id=node_data["id"],
                subject=node_data.get("subject", ""),
                topic=node_data.get("topic", ""),
                subtopic=node_data.get("subtopic", ""),
                display_name=node_data.get("display_name", node_data["id"]),
                difficulty=node_data.get("difficulty", 1),
                prerequisites=node_data.get("prerequisites", []),
            )
            self._nodes[node.id] = node
        for edge_data in data.get("edges", []):
            edge = ConceptEdge(
                from_id=edge_data["from_id"],
                to_id=edge_data["to_id"],
                relationship=edge_data.get("relationship", "related"),
            )
            self._edges.append(edge)
            self._adjacency.setdefault(edge.from_id, []).append(edge)
        logger.info(
            "Loaded concept graph", extra={"nodes": len(self._nodes), "edges": len(self._edges)}
        )

    def get_node(self, node_id: str) -> ConceptNode:
        node = self._nodes.get(node_id)
        if node is None:
            raise KeyError(f"ConceptNode not found: {node_id}")
        return node

    def get_all_nodes(self) -> list[ConceptNode]:
        return list(self._nodes.values())

    def get_all_edges(self) -> list[ConceptEdge]:
        return list(self._edges)

    def get_prerequisites(self, node_id: str) -> list[ConceptNode]:
        node = self.get_node(node_id)
        prereq_ids = node.prerequisites
        result = []
        for pid in prereq_ids:
            try:
                result.append(self.get_node(pid))
            except KeyError:
                logger.warning("Prerequisite node not found", extra={"node_id": pid})
        return result

    def get_dependents(self, node_id: str) -> list[ConceptNode]:
        from contextlib import suppress

        dependents = []
        for edge in self._edges:
            if edge.to_id == node_id and edge.relationship == "prerequisite":
                with suppress(KeyError):
                    dependents.append(self.get_node(edge.from_id))
        return dependents

    def get_siblings(self, node_id: str) -> list[ConceptNode]:
        node = self.get_node(node_id)
        siblings = []
        for n in self._nodes.values():
            if n.id != node_id and n.topic == node.topic and n.subject == node.subject:
                siblings.append(n)
        return siblings

    def get_related_concepts(self, node_id: str, depth: int = 1) -> list[ConceptNode]:
        visited: set[str] = set()
        queue: deque[tuple[str, int]] = deque()
        queue.append((node_id, 0))
        visited.add(node_id)
        results: list[ConceptNode] = []
        while queue:
            current_id, d = queue.popleft()
            if d > depth:
                continue
            if d > 0:
                from contextlib import suppress

                with suppress(KeyError):
                    results.append(self.get_node(current_id))
            for edge in self._adjacency.get(current_id, []):
                if edge.to_id not in visited:
                    visited.add(edge.to_id)
                    queue.append((edge.to_id, d + 1))
                if edge.from_id not in visited:
                    visited.add(edge.from_id)
                    queue.append((edge.from_id, d + 1))
        return results

    def find_shortest_path(self, from_id: str, to_id: str) -> list[ConceptNode]:
        if from_id not in self._nodes or to_id not in self._nodes:
            raise KeyError("Source or target node not found")
        visited: set[str] = set()
        parent: dict[str, str | None] = {from_id: None}
        queue: deque[str] = deque([from_id])
        visited.add(from_id)
        found = False
        while queue:
            current = queue.popleft()
            if current == to_id:
                found = True
                break
            for edge in self._adjacency.get(current, []):
                neighbor = edge.to_id
                if neighbor not in visited:
                    visited.add(neighbor)
                    parent[neighbor] = current
                    queue.append(neighbor)
        if not found:
            return []
        path_ids = []
        cur: str | None = to_id
        while cur is not None:
            path_ids.append(cur)
            cur = parent.get(cur)
        path_ids.reverse()
        return [self._nodes[pid] for pid in path_ids]

    def traverse_upstream(self, node_id: str) -> list[ConceptNode]:
        visited: set[str] = set()
        queue: deque[str] = deque([node_id])
        visited.add(node_id)
        upstream: list[ConceptNode] = []
        while queue:
            current = queue.popleft()
            if current != node_id:
                upstream.append(self._nodes[current])
            node = self._nodes[current]
            for pid in node.prerequisites:
                if pid in self._nodes and pid not in visited:
                    visited.add(pid)
                    queue.append(pid)
        return upstream

    def search_nodes(self, query: str) -> list[ConceptNode]:
        q = query.lower()
        matches = []
        for node in self._nodes.values():
            if (
                q in node.display_name.lower()
                or q in node.subject.lower()
                or q in node.topic.lower()
                or q in node.subtopic.lower()
            ):
                matches.append(node)
        return matches
