"""
Data Validation and Quality Assurance

Demonstrates validation patterns to ensure agents work with accurate,
complete, and timely data.

This example shows:
- Schema validation for incoming data
- Freshness tracking and staleness detection
- Entity resolution and deduplication
- Data quality dimensions (accuracy, completeness, consistency, timeliness)

Reference: "Garbage In, Hallucinations Out" video - Chapter 2

Key Concept: An agent with perfect reasoning will fail if grounded
in inaccurate, outdated, or biased data.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Set
from datetime import datetime, timedelta
from enum import Enum
import re


class QualityDimension(Enum):
    """
    Data quality dimensions that must all be satisfied.

    A document can be accurate but outdated, or complete but inconsistent.
    Quality assurance must address ALL dimensions.
    """
    ACCURACY = "accuracy"           # Is the data correct?
    COMPLETENESS = "completeness"   # Is anything missing?
    CONSISTENCY = "consistency"     # Do different sources agree?
    TIMELINESS = "timeliness"       # Is the data current?


class FreshnessLevel(Enum):
    """Freshness classification for documents."""
    FRESH = "fresh"         # Within acceptable age
    AGING = "aging"         # Approaching staleness
    STALE = "stale"         # Too old, may be unreliable
    EXPIRED = "expired"     # Must not be used


@dataclass
class ValidationResult:
    """Result of a data validation check."""
    passed: bool
    dimension: QualityDimension
    message: str
    severity: str = "error"     # error, warning, info
    field_path: str = ""        # Which field failed


@dataclass
class Document:
    """A document with validation metadata."""
    doc_id: str
    content: str
    doc_type: str
    source: str

    # Temporal metadata
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    valid_until: Optional[datetime] = None  # Explicit expiration

    # Quality metadata
    validation_results: List[ValidationResult] = field(default_factory=list)
    freshness: FreshnessLevel = FreshnessLevel.FRESH

    # Lineage
    parent_doc_id: Optional[str] = None
    transformations: List[str] = field(default_factory=list)


class SchemaValidator:
    """
    Validates documents against defined schemas.

    Key Principle: All incoming data must conform to defined schemas
    and quality standards BEFORE entering your system.
    """

    def __init__(self):
        self._schemas: Dict[str, Dict[str, Any]] = {}

    def register_schema(self, doc_type: str, schema: Dict[str, Any]) -> None:
        """Register a schema for a document type."""
        self._schemas[doc_type] = schema

    def validate(self, doc: Document) -> List[ValidationResult]:
        """
        Validate a document against its schema.

        Returns list of validation failures (empty = valid).
        """
        results = []

        schema = self._schemas.get(doc.doc_type)
        if not schema:
            results.append(ValidationResult(
                passed=False,
                dimension=QualityDimension.ACCURACY,
                message=f"No schema registered for type: {doc.doc_type}",
                severity="error"
            ))
            return results

        # Check required fields
        required = schema.get("required_fields", [])
        for field_name in required:
            if field_name not in doc.content:
                results.append(ValidationResult(
                    passed=False,
                    dimension=QualityDimension.COMPLETENESS,
                    message=f"Missing required field: {field_name}",
                    field_path=field_name
                ))

        # Check field patterns
        patterns = schema.get("patterns", {})
        for field_name, pattern in patterns.items():
            if field_name in doc.content:
                if not re.match(pattern, str(doc.content)):
                    results.append(ValidationResult(
                        passed=False,
                        dimension=QualityDimension.ACCURACY,
                        message=f"Field {field_name} doesn't match pattern",
                        field_path=field_name
                    ))

        return results


class FreshnessTracker:
    """
    Tracks document freshness and enforces staleness policies.

    Key Principle: A COVID policy from 2020 is not relevant in 2026.
    A stock price from yesterday is stale for day trading.
    """

    def __init__(self):
        # Default TTLs by document type (in hours)
        self._ttl_config: Dict[str, int] = {
            "policy": 24 * 30,      # 30 days
            "faq": 24 * 7,          # 7 days
            "pricing": 24,          # 1 day
            "news": 1,              # 1 hour
            "stock_quote": 0.017,   # 1 minute
        }

    def check_freshness(self, doc: Document) -> FreshnessLevel:
        """
        Check the freshness level of a document.

        Returns freshness classification based on document age and type.
        """
        # Check explicit expiration first
        if doc.valid_until and datetime.now() > doc.valid_until:
            return FreshnessLevel.EXPIRED

        # Get TTL for document type
        ttl_hours = self._ttl_config.get(doc.doc_type, 24 * 7)  # Default 7 days
        age_hours = (datetime.now() - doc.updated_at).total_seconds() / 3600

        # Calculate freshness level
        if age_hours < ttl_hours * 0.5:
            return FreshnessLevel.FRESH
        elif age_hours < ttl_hours * 0.9:
            return FreshnessLevel.AGING
        elif age_hours < ttl_hours:
            return FreshnessLevel.STALE
        else:
            return FreshnessLevel.EXPIRED

    def should_refresh(self, doc: Document) -> bool:
        """Check if document should be refreshed from source."""
        freshness = self.check_freshness(doc)
        return freshness in [FreshnessLevel.STALE, FreshnessLevel.EXPIRED]


class EntityResolver:
    """
    Resolves entity duplicates and variations.

    Key Principle: Enterprise data contains duplicates and variant representations:
    IBM, International Business Machines, IBM Corp., I.B.M.
    Entity resolution identifies these as the same entity.
    """

    def __init__(self):
        self._canonical_forms: Dict[str, str] = {}
        self._aliases: Dict[str, Set[str]] = {}

    def register_entity(self, canonical: str, aliases: List[str]) -> None:
        """Register a canonical entity with its aliases."""
        self._canonical_forms[canonical.lower()] = canonical
        self._aliases[canonical.lower()] = set(a.lower() for a in aliases)

        # Also map aliases to canonical
        for alias in aliases:
            self._canonical_forms[alias.lower()] = canonical

    def resolve(self, entity: str) -> str:
        """
        Resolve an entity to its canonical form.

        Returns the canonical form if known, original otherwise.
        """
        return self._canonical_forms.get(entity.lower(), entity)

    def are_same_entity(self, entity1: str, entity2: str) -> bool:
        """Check if two strings refer to the same entity."""
        return self.resolve(entity1) == self.resolve(entity2)


# =============================================================================
# Demonstration
# =============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("Data Validation Demonstration")
    print("=" * 70)

    # Schema Validation
    print("\n[1] Schema Validation")
    print("-" * 50)

    validator = SchemaValidator()
    validator.register_schema("policy", {
        "required_fields": ["title", "effective_date", "version"],
        "patterns": {"version": r"^\d+\.\d+$"}
    })

    doc = Document(
        doc_id="doc-001",
        content="This is a return policy document",
        doc_type="policy",
        source="internal"
    )

    results = validator.validate(doc)
    print(f"  Document: {doc.doc_id}")
    print(f"  Validation results: {len(results)} issues")
    for r in results:
        print(f"    [{r.severity}] {r.dimension.value}: {r.message}")

    # Freshness Tracking
    print("\n[2] Freshness Tracking")
    print("-" * 50)

    tracker = FreshnessTracker()

    test_docs = [
        Document(
            doc_id="fresh-doc",
            content="Recent content",
            doc_type="faq",
            source="internal",
            updated_at=datetime.now() - timedelta(hours=12)
        ),
        Document(
            doc_id="stale-doc",
            content="Old content",
            doc_type="faq",
            source="internal",
            updated_at=datetime.now() - timedelta(days=10)
        ),
    ]

    for doc in test_docs:
        freshness = tracker.check_freshness(doc)
        age = (datetime.now() - doc.updated_at).total_seconds() / 3600
        print(f"  {doc.doc_id}: {freshness.value} (age: {age:.1f}h)")
        print(f"    Should refresh: {tracker.should_refresh(doc)}")

    # Entity Resolution
    print("\n[3] Entity Resolution")
    print("-" * 50)

    resolver = EntityResolver()
    resolver.register_entity("IBM", [
        "International Business Machines",
        "IBM Corp.",
        "IBM Corporation",
        "I.B.M."
    ])

    test_entities = ["IBM", "international business machines", "I.B.M.", "Apple"]
    for entity in test_entities:
        resolved = resolver.resolve(entity)
        print(f"  '{entity}' -> '{resolved}'")

    print("\n  Same entity check:")
    print(f"    'IBM' == 'I.B.M.': {resolver.are_same_entity('IBM', 'I.B.M.')}")
    print(f"    'IBM' == 'Apple': {resolver.are_same_entity('IBM', 'Apple')}")

    print("\n" + "=" * 70)
    print("Key Takeaways:")
    print("1. Validate ALL data before it enters your system")
    print("2. Track freshness - stale data leads to wrong answers")
    print("3. Resolve entity variations to canonical forms")
    print("4. Data quality is multi-dimensional (accuracy, completeness, etc.)")
    print("=" * 70)
