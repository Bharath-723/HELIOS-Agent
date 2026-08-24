"""
HELIOS v2 - Knowledge Manager & Graph Layer
Manages source registries, metadata extraction, freshness tracking, and Knowledge Graph entity relationships.
"""
import logging
from typing import Dict, List, Optional, Any, Tuple
from core.knowledge.knowledge_models import (
    KnowledgeSource,
    VerificationStatus,
    KnowledgeGraphNode,
    KnowledgeGraphEdge,
    KnowledgeGraph
)
from core.knowledge.knowledge_logger import KnowledgeLogger

log = logging.getLogger("helios.knowledge.manager")

class KnowledgeManager:
    def __init__(self):
        # Source registry
        self.sources: Dict[str, KnowledgeSource] = {}
        
        # Knowledge Graph topology
        self.graph = KnowledgeGraph(nodes={}, edges=[])
        self.logger = KnowledgeLogger()

    # ---------------------------------------------------------
    # Knowledge Source Registry
    # ---------------------------------------------------------
    def register_source(
        self,
        source_id: str,
        name: str,
        source_type: str,
        uri: str,
        version: str,
        reliability_score: float = 1.0,
        verification_status: VerificationStatus = VerificationStatus.VERIFIED
    ) -> KnowledgeSource:
        import time
        source = KnowledgeSource(
            source_id=source_id,
            name=name,
            source_type=source_type,
            uri=uri,
            version=version,
            last_modified=time.time(),
            freshness_status="fresh",
            reliability_score=reliability_score,
            verification_status=verification_status
        )
        self.sources[source_id] = source
        self.logger.log_event("source_registered", {"source_id": source_id, "type": source_type})
        return source

    def update_source_freshness(self, source_id: str, current_time: float, max_age_seconds: float):
        source = self.sources.get(source_id)
        if source:
            age = current_time - source.last_modified
            freshness = "fresh"
            if age > max_age_seconds:
                freshness = "expired"
            elif age > max_age_seconds * 0.5:
                freshness = "stale"
                
            updated = KnowledgeSource(
                source_id=source.source_id,
                name=source.name,
                source_type=source.source_type,
                uri=source.uri,
                version=source.version,
                last_modified=source.last_modified,
                freshness_status=freshness,
                reliability_score=source.reliability_score,
                verification_status=source.verification_status
            )
            self.sources[source_id] = updated

    # ---------------------------------------------------------
    # Knowledge Graph Operations
    # ---------------------------------------------------------
    def add_node(self, node_id: str, entity_type: str, properties: Optional[Dict[str, Any if 'Any' in globals() else str]] = None) -> KnowledgeGraphNode:
        props = properties.copy() if properties else {}
        node = KnowledgeGraphNode(node_id=node_id, entity_type=entity_type, properties=props)
        self.graph.nodes[node_id] = node
        self.logger.log_graph_modification("add_node", node_id)
        return node

    def add_edge(
        self,
        source_id: str,
        target_id: str,
        relation_type: str,
        properties: Optional[Dict[str, Any if 'Any' in globals() else str]] = None,
        verification_ref: str = ""
    ) -> KnowledgeGraphEdge:
        if source_id not in self.graph.nodes or target_id not in self.graph.nodes:
            raise ValueError(f"Cannot add edge between missing nodes: {source_id} -> {target_id}")
            
        props = properties.copy() if properties else {}
        edge = KnowledgeGraphEdge(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type,
            properties=props,
            source_verification_ref=verification_ref
        )
        self.graph.edges.append(edge)
        self.logger.log_graph_modification("add_edge", f"{source_id}->{target_id}")
        return edge

    def get_adjacent_nodes(self, node_id: str) -> List[Tuple[KnowledgeGraphNode, str]]:
        """
        Finds adjacent nodes linked to node_id.
        Returns List of Tuples: (target_node, relation_type)
        """
        adjacents = []
        for edge in self.graph.edges:
            if edge.source_id == node_id:
                target_node = self.graph.nodes.get(edge.target_id)
                if target_node:
                    adjacents.append((target_node, edge.relation_type))
        return adjacents
