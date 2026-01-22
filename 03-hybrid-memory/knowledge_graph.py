"""
Knowledge Graph for Multi-Hop Reasoning

Demonstrates how knowledge graphs enable traversing relationships
that vector search cannot handle. This is essential for questions like:
"How does the delay in Project Apollo impact the Q3 budget that Sarah approved?"

This example shows:
- Entity and relationship modeling
- Graph traversal for multi-hop queries
- Temporal knowledge graphs (time-aware indexing)
- Community detection for global queries

Reference: "Beyond RAG: The Three-Tier Memory Architecture" video - Chapter 4

Key Concept: Graphs store entities AND relationships - enabling reasoning
that requires following explicit connections through your data.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Set, Tuple
from datetime import datetime, timedelta
from enum import Enum
from collections import defaultdict


class RelationType(Enum):
    """
    Types of relationships between entities.

    Explicit relationships enable multi-hop reasoning that
    vector similarity search cannot achieve.
    """
    # Project relationships
    OWNS = "owns"                    # Person owns Project
    DEPENDS_ON = "depends_on"        # Project depends on Project
    DELAYED_BY = "delayed_by"        # Project delayed by Issue

    # Budget relationships
    AFFECTS = "affects"              # Issue affects BudgetItem
    APPROVED_BY = "approved_by"      # BudgetItem approved by Person
    ALLOCATED_TO = "allocated_to"    # Budget allocated to Project

    # Organizational
    REPORTS_TO = "reports_to"        # Person reports to Person
    MEMBER_OF = "member_of"          # Person member of Team
    WORKS_ON = "works_on"            # Person works on Project


@dataclass
class Entity:
    """
    A node in the knowledge graph.

    Entities represent things: people, projects, budgets, issues.
    """
    entity_id: str
    entity_type: str                # e.g., "Person", "Project", "Budget"
    name: str
    properties: Dict[str, Any] = field(default_factory=dict)

    # For temporal graphs
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class Relationship:
    """
    An edge in the knowledge graph.

    Relationships connect entities with explicit, typed connections.
    This is what enables multi-hop reasoning.
    """
    rel_id: str
    source_id: str
    target_id: str
    rel_type: RelationType
    properties: Dict[str, Any] = field(default_factory=dict)

    # For temporal relationships
    valid_from: Optional[datetime] = None
    valid_to: Optional[datetime] = None

    def is_valid_at(self, point_in_time: datetime) -> bool:
        """Check if this relationship was valid at a specific time."""
        if self.valid_from and point_in_time < self.valid_from:
            return False
        if self.valid_to and point_in_time > self.valid_to:
            return False
        return True


class KnowledgeGraph:
    """
    A simple knowledge graph implementation.

    In production, you would use:
    - Neo4j with Cypher queries
    - MemGraph for high-performance needs
    - Amazon Neptune for cloud deployments
    - GraphRAG from Microsoft Research

    Key Principle: Graphs answer questions that require
    TRAVERSING relationships, not just finding similar content.
    """

    def __init__(self):
        self._entities: Dict[str, Entity] = {}
        self._relationships: List[Relationship] = []

        # Indexes for fast lookup
        self._outgoing: Dict[str, List[Relationship]] = defaultdict(list)
        self._incoming: Dict[str, List[Relationship]] = defaultdict(list)
        self._by_type: Dict[str, List[Entity]] = defaultdict(list)

    def add_entity(self, entity: Entity) -> None:
        """Add an entity to the graph."""
        self._entities[entity.entity_id] = entity
        self._by_type[entity.entity_type].append(entity)

    def add_relationship(self, rel: Relationship) -> None:
        """Add a relationship to the graph."""
        self._relationships.append(rel)
        self._outgoing[rel.source_id].append(rel)
        self._incoming[rel.target_id].append(rel)

    def get_entity(self, entity_id: str) -> Optional[Entity]:
        """Get an entity by ID."""
        return self._entities.get(entity_id)

    def get_entities_by_type(self, entity_type: str) -> List[Entity]:
        """Get all entities of a specific type."""
        return self._by_type.get(entity_type, [])

    def get_outgoing(self, entity_id: str,
                     rel_type: Optional[RelationType] = None) -> List[Relationship]:
        """Get outgoing relationships from an entity."""
        rels = self._outgoing.get(entity_id, [])
        if rel_type:
            rels = [r for r in rels if r.rel_type == rel_type]
        return rels

    def get_incoming(self, entity_id: str,
                     rel_type: Optional[RelationType] = None) -> List[Relationship]:
        """Get incoming relationships to an entity."""
        rels = self._incoming.get(entity_id, [])
        if rel_type:
            rels = [r for r in rels if r.rel_type == rel_type]
        return rels

    # =========================================================================
    # Multi-Hop Traversal (The key capability)
    # =========================================================================

    def traverse(self, start_id: str, path_pattern: List[RelationType],
                 max_depth: int = 10) -> List[List[str]]:
        """
        Traverse the graph following a pattern of relationship types.

        Example: traverse("project-apollo", [DELAYED_BY, AFFECTS, APPROVED_BY])
        Returns paths like: [project-apollo] -> [issue-1] -> [budget-q3] -> [sarah]

        This is the multi-hop reasoning that vector search CANNOT do.
        """
        if not path_pattern:
            return [[start_id]]

        current_rel_type = path_pattern[0]
        remaining_pattern = path_pattern[1:]

        paths = []
        for rel in self.get_outgoing(start_id, current_rel_type):
            if remaining_pattern:
                # Continue traversal
                sub_paths = self.traverse(rel.target_id, remaining_pattern, max_depth - 1)
                for sub_path in sub_paths:
                    paths.append([start_id] + sub_path)
            else:
                # End of pattern
                paths.append([start_id, rel.target_id])

        return paths

    def shortest_path(self, source_id: str, target_id: str,
                      max_depth: int = 5) -> Optional[List[str]]:
        """
        Find the shortest path between two entities.

        Uses BFS (Breadth-First Search) to find the minimum-hop path.
        """
        if source_id == target_id:
            return [source_id]

        visited = {source_id}
        queue = [(source_id, [source_id])]

        while queue:
            current_id, path = queue.pop(0)

            if len(path) > max_depth:
                continue

            for rel in self.get_outgoing(current_id):
                if rel.target_id == target_id:
                    return path + [target_id]

                if rel.target_id not in visited:
                    visited.add(rel.target_id)
                    queue.append((rel.target_id, path + [rel.target_id]))

        return None  # No path found

    def find_all_connected(self, start_id: str, max_hops: int = 3) -> Set[str]:
        """
        Find all entities within N hops of the starting entity.

        Useful for understanding the "neighborhood" of an entity.
        """
        visited = {start_id}
        frontier = {start_id}

        for _ in range(max_hops):
            new_frontier = set()
            for entity_id in frontier:
                for rel in self.get_outgoing(entity_id):
                    if rel.target_id not in visited:
                        visited.add(rel.target_id)
                        new_frontier.add(rel.target_id)
                for rel in self.get_incoming(entity_id):
                    if rel.source_id not in visited:
                        visited.add(rel.source_id)
                        new_frontier.add(rel.source_id)
            frontier = new_frontier

        return visited

    # =========================================================================
    # Temporal Queries (Time-aware knowledge graphs)
    # =========================================================================

    def query_at_time(self, entity_id: str, rel_type: RelationType,
                      point_in_time: datetime) -> List[Relationship]:
        """
        Query relationships valid at a specific point in time.

        Key Concept: Temporal knowledge graphs add TIME as a dimension.
        "What was the status of Project X on January 15th?"
        """
        rels = self.get_outgoing(entity_id, rel_type)
        return [r for r in rels if r.is_valid_at(point_in_time)]


# =============================================================================
# Example: Building a Project Knowledge Graph
# =============================================================================

def build_example_graph() -> KnowledgeGraph:
    """
    Build the example knowledge graph from the video.

    This demonstrates the multi-hop question:
    "How does the delay in Project Apollo impact the Q3 budget that Sarah approved?"

    The traversal path: Project Apollo -> Supply Chain Issue -> Q3 Budget -> Sarah
    """
    graph = KnowledgeGraph()

    # Add entities
    entities = [
        Entity("project-apollo", "Project", "Project Apollo",
               {"status": "delayed", "priority": "high"}),
        Entity("supply-issue-1", "Issue", "Supply Chain Disruption",
               {"severity": "critical", "region": "Asia"}),
        Entity("budget-q3", "Budget", "Q3 Operating Budget",
               {"amount": 500000, "quarter": "Q3"}),
        Entity("sarah", "Person", "Sarah",
               {"role": "Finance Director", "department": "Finance"}),
        Entity("project-mercury", "Project", "Project Mercury",
               {"status": "active", "priority": "medium"}),
        Entity("bob", "Person", "Bob",
               {"role": "Project Manager", "department": "Engineering"}),
    ]

    for entity in entities:
        graph.add_entity(entity)

    # Add relationships
    relationships = [
        # Project Apollo is delayed by Supply Chain Issue
        Relationship("rel-1", "project-apollo", "supply-issue-1",
                     RelationType.DELAYED_BY,
                     {"delay_days": 30}),

        # Supply Chain Issue affects Q3 Budget
        Relationship("rel-2", "supply-issue-1", "budget-q3",
                     RelationType.AFFECTS,
                     {"impact_amount": 50000}),

        # Q3 Budget was approved by Sarah
        Relationship("rel-3", "budget-q3", "sarah",
                     RelationType.APPROVED_BY,
                     {"approved_date": "2026-01-15"}),

        # Bob owns Project Apollo
        Relationship("rel-4", "bob", "project-apollo",
                     RelationType.OWNS),

        # Bob reports to Sarah
        Relationship("rel-5", "bob", "sarah",
                     RelationType.REPORTS_TO),

        # Project Mercury depends on Project Apollo
        Relationship("rel-6", "project-mercury", "project-apollo",
                     RelationType.DEPENDS_ON),
    ]

    for rel in relationships:
        graph.add_relationship(rel)

    return graph


# =============================================================================
# Demonstration
# =============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("Knowledge Graph Demonstration (Multi-Hop Reasoning)")
    print("=" * 70)

    graph = build_example_graph()

    # The multi-hop question from the video
    print("\n[1] Multi-Hop Query (Vector Search CANNOT Do This)")
    print("-" * 50)
    print("Question: How does the delay in Project Apollo impact")
    print("          the Q3 budget that Sarah approved?")

    # Traverse: Project Apollo -> [delayed by] -> Issue -> [affects] -> Budget -> [approved by] -> Person
    path_pattern = [RelationType.DELAYED_BY, RelationType.AFFECTS, RelationType.APPROVED_BY]
    paths = graph.traverse("project-apollo", path_pattern)

    print("\nTraversal Path:")
    for path in paths:
        entities = [graph.get_entity(eid) for eid in path]
        print("  " + " -> ".join(e.name for e in entities if e))

        # Show the relationships along the path
        print("\n  Relationship chain:")
        for i in range(len(path) - 1):
            rels = graph.get_outgoing(path[i])
            for rel in rels:
                if rel.target_id == path[i+1]:
                    print(f"    {path[i]} --[{rel.rel_type.value}]--> {path[i+1]}")
                    if rel.properties:
                        print(f"      Properties: {rel.properties}")

    # Shortest path
    print("\n[2] Shortest Path Query")
    print("-" * 50)
    print("Question: What's the shortest connection between Project Mercury and Sarah?")

    path = graph.shortest_path("project-mercury", "sarah")
    if path:
        entities = [graph.get_entity(eid) for eid in path]
        print(f"Path ({len(path)-1} hops): " + " -> ".join(e.name for e in entities if e))
    else:
        print("No path found")

    # All connected entities
    print("\n[3] Entity Neighborhood (Impact Analysis)")
    print("-" * 50)
    print("Question: What entities are within 2 hops of the Supply Chain Issue?")

    connected = graph.find_all_connected("supply-issue-1", max_hops=2)
    print("Connected entities:")
    for entity_id in connected:
        entity = graph.get_entity(entity_id)
        if entity:
            print(f"  - {entity.name} ({entity.entity_type})")

    # Compare with vector search limitations
    print("\n[4] Why Vector Search Can't Do This")
    print("-" * 50)
    print("""
Vector search would find:
  - Documents about "Project Apollo"
  - Documents about "budgets"
  - Documents about "Sarah"

But it CANNOT:
  - Trace the RELATIONSHIP chain from Apollo -> Issue -> Budget -> Sarah
  - Answer "Who approved the budget affected by the supply issue?"
  - Perform impact analysis across connected entities

Key Insight: Graphs provide DEPTH (relationships), vectors provide BREADTH (similarity)
    """)

    print("\n" + "=" * 70)
    print("Key Takeaways:")
    print("1. Knowledge graphs store ENTITIES and RELATIONSHIPS")
    print("2. Multi-hop traversal answers questions requiring relationship chains")
    print("3. Temporal graphs add TIME as a dimension")
    print("4. Combine with vectors for the best of both worlds (see hybrid_retrieval.py)")
    print("=" * 70)
