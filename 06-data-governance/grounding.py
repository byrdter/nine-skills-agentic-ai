"""
Strict Grounding and Hallucination Prevention

Demonstrates techniques to ensure agent outputs are grounded in
verified sources, with proper citation and confidence scoring.

This example shows:
- Strict grounding prompts that constrain to retrieved content
- Citation generation for verifiable claims
- Confidence scoring with appropriate thresholds
- Attribution checking for claim verification

Reference: "Garbage In, Hallucinations Out" video - Chapter 4

Key Concept: LLMs have parametric knowledge that can be outdated or wrong.
Strict grounding ensures agents only assert what's in the documents.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from enum import Enum


class ConfidenceLevel(Enum):
    """
    Confidence levels for agent responses.

    Key Principle: Express uncertainty rather than hallucinate.
    """
    HIGH = "high"           # 90%+ - Answer directly
    MEDIUM = "medium"       # 60-90% - Add caveats
    LOW = "low"             # <60% - Escalate or refuse


@dataclass
class Citation:
    """
    A citation linking a claim to its source.

    Key Principle: Every factual claim should include a citation.
    Users can verify information by checking the source.
    """
    source_id: str
    source_title: str
    section: str = ""
    page_number: Optional[int] = None
    timestamp: Optional[datetime] = None
    quote: str = ""         # Direct quote if applicable


@dataclass
class GroundedClaim:
    """
    A claim with its supporting citations.

    Claims without citations are potential hallucinations.
    """
    claim_text: str
    citations: List[Citation]
    confidence: float           # 0.0 to 1.0
    grounded: bool              # Is this claim supported?


@dataclass
class GroundedResponse:
    """
    An agent response with grounding metadata.

    Includes the response text, all claims with citations,
    and an overall confidence score.
    """
    response_text: str
    claims: List[GroundedClaim]
    overall_confidence: float
    confidence_level: ConfidenceLevel

    ungrounded_claims: List[str] = field(default_factory=list)
    insufficient_info: bool = False


class GroundingChecker:
    """
    Checks if agent claims are grounded in provided sources.

    In production, this would use an LLM to verify that each claim
    in the response is supported by the retrieved documents.
    """

    def __init__(self, strictness: float = 0.7):
        """
        Args:
            strictness: Minimum support required (0-1)
        """
        self.strictness = strictness

    def check_claim(self, claim: str, sources: List[Dict[str, Any]]) -> Tuple[bool, List[Citation], float]:
        """
        Check if a claim is grounded in the provided sources.

        Returns: (is_grounded, citations, confidence)

        In production, use an LLM with this prompt:
        "Does the following claim appear in or is it supported by the sources?
         Claim: {claim}
         Sources: {sources}
         Return: supported (yes/no), supporting quotes, confidence (0-1)"
        """
        # Simplified implementation
        citations = []
        confidence = 0.0

        for source in sources:
            content = source.get("content", "").lower()
            claim_words = claim.lower().split()

            # Check for word overlap (simplified - real would use semantic similarity)
            overlap = sum(1 for word in claim_words if word in content)
            word_confidence = overlap / max(len(claim_words), 1)

            if word_confidence > 0.3:
                citations.append(Citation(
                    source_id=source.get("id", "unknown"),
                    source_title=source.get("title", "Unknown Source"),
                    section=source.get("section", ""),
                    quote=content[:100] + "..." if len(content) > 100 else content
                ))
                confidence = max(confidence, word_confidence)

        is_grounded = confidence >= self.strictness and len(citations) > 0
        return is_grounded, citations, confidence

    def generate_grounded_response(self, response_text: str,
                                   claims: List[str],
                                   sources: List[Dict[str, Any]]) -> GroundedResponse:
        """
        Generate a grounded response with citations for all claims.
        """
        grounded_claims = []
        ungrounded = []

        for claim in claims:
            is_grounded, citations, confidence = self.check_claim(claim, sources)

            grounded_claims.append(GroundedClaim(
                claim_text=claim,
                citations=citations,
                confidence=confidence,
                grounded=is_grounded
            ))

            if not is_grounded:
                ungrounded.append(claim)

        # Calculate overall confidence
        if grounded_claims:
            overall = sum(c.confidence for c in grounded_claims) / len(grounded_claims)
        else:
            overall = 0.0

        # Determine confidence level
        if overall >= 0.9:
            level = ConfidenceLevel.HIGH
        elif overall >= 0.6:
            level = ConfidenceLevel.MEDIUM
        else:
            level = ConfidenceLevel.LOW

        return GroundedResponse(
            response_text=response_text,
            claims=grounded_claims,
            overall_confidence=overall,
            confidence_level=level,
            ungrounded_claims=ungrounded,
            insufficient_info=overall < 0.3
        )


class ConfidenceGate:
    """
    Gates agent responses based on confidence thresholds.

    Key Principle: Don't give confident-sounding nonsense.
    Low confidence should trigger caveats or refusal.
    """

    def __init__(self,
                 high_threshold: float = 0.9,
                 medium_threshold: float = 0.6,
                 refuse_threshold: float = 0.3):
        self.high_threshold = high_threshold
        self.medium_threshold = medium_threshold
        self.refuse_threshold = refuse_threshold

    def apply_gate(self, response: GroundedResponse) -> Dict[str, Any]:
        """
        Apply confidence gate to a grounded response.

        Returns action to take based on confidence level.
        """
        conf = response.overall_confidence

        if conf >= self.high_threshold:
            return {
                "action": "respond",
                "add_caveats": False,
                "response": response.response_text
            }
        elif conf >= self.medium_threshold:
            return {
                "action": "respond",
                "add_caveats": True,
                "response": self._add_caveats(response),
                "caveats": ["Based on available information...",
                           "Please verify with official sources..."]
            }
        elif conf >= self.refuse_threshold:
            return {
                "action": "escalate",
                "reason": "Low confidence - human review needed",
                "response": "I'm not confident enough to answer this accurately. "
                           "Let me connect you with a human expert."
            }
        else:
            return {
                "action": "refuse",
                "reason": "Insufficient information",
                "response": "I don't have enough information to answer this question reliably."
            }

    def _add_caveats(self, response: GroundedResponse) -> str:
        """Add uncertainty language to a medium-confidence response."""
        prefix = "Based on the available information, "
        suffix = " Please note that this information may be subject to change."
        return prefix + response.response_text + suffix


# =============================================================================
# Demonstration
# =============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("Strict Grounding Demonstration")
    print("=" * 70)

    # Example sources
    sources = [
        {
            "id": "policy-001",
            "title": "Return Policy v2.3",
            "section": "Section 4.1",
            "content": "Items may be returned within 30 days of purchase for a full refund. "
                      "Original packaging and receipt are required. Electronics have a "
                      "15-day return window."
        },
        {
            "id": "faq-001",
            "title": "Customer FAQ",
            "section": "Returns",
            "content": "Customers can return most items within 30 days. Sale items are "
                      "final sale and cannot be returned."
        }
    ]

    # Example claims to verify
    claims = [
        "You can return items within 30 days for a full refund.",
        "Electronics have a 15-day return window.",
        "You can return items after 60 days with manager approval.",  # Not supported
        "Sale items are final sale."
    ]

    checker = GroundingChecker(strictness=0.5)

    # Check individual claims
    print("\n[1] Checking Individual Claims")
    print("-" * 50)

    for claim in claims:
        is_grounded, citations, confidence = checker.check_claim(claim, sources)
        status = "✓ GROUNDED" if is_grounded else "✗ UNGROUNDED"
        print(f"\n  {status} ({confidence:.0%})")
        print(f"  Claim: '{claim}'")
        if citations:
            print(f"  Source: {citations[0].source_title}")

    # Generate full grounded response
    print("\n[2] Grounded Response Generation")
    print("-" * 50)

    response = checker.generate_grounded_response(
        response_text="Items can be returned within 30 days for a full refund. "
                     "Electronics have a shorter 15-day window. Sale items are final sale.",
        claims=claims[:3],
        sources=sources
    )

    print(f"\n  Overall Confidence: {response.overall_confidence:.0%}")
    print(f"  Confidence Level: {response.confidence_level.value}")
    print(f"  Ungrounded Claims: {response.ungrounded_claims}")

    # Apply confidence gate
    print("\n[3] Confidence Gate")
    print("-" * 50)

    gate = ConfidenceGate()
    action = gate.apply_gate(response)

    print(f"\n  Action: {action['action']}")
    if action.get('add_caveats'):
        print(f"  Caveats added: Yes")
    print(f"  Response: {action['response'][:80]}...")

    # Low confidence example
    print("\n[4] Low Confidence Example")
    print("-" * 50)

    low_conf_response = GroundedResponse(
        response_text="The warranty lasts for 5 years.",
        claims=[GroundedClaim("The warranty lasts for 5 years", [], 0.2, False)],
        overall_confidence=0.2,
        confidence_level=ConfidenceLevel.LOW
    )

    action = gate.apply_gate(low_conf_response)
    print(f"\n  Action: {action['action']}")
    print(f"  Response: {action['response']}")

    print("\n" + "=" * 70)
    print("Key Takeaways:")
    print("1. Strict grounding: Only assert what's in the documents")
    print("2. Citations enable verification of every claim")
    print("3. Confidence scoring quantifies uncertainty")
    print("4. Low confidence should trigger caveats or refusal, not hallucination")
    print("=" * 70)
