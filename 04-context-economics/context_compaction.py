"""
Context Compaction and Hierarchical Summarization

Demonstrates techniques for managing unbounded conversation history
and keeping context within token limits while preserving critical information.

This example shows:
- Hierarchical summarization (per-turn, per-session, per-user)
- Sliding window with summarization pattern
- Semantic compression (entity extraction, coreference resolution)

Reference: "The $10,000 Prompt" video - Chapter 3

Key Concept: As agents run for extended periods, conversation histories
grow without bound. Compaction keeps context manageable.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum


class SummaryLevel(Enum):
    """
    Levels of summarization granularity.

    Key Principle: Different situations need different levels of detail.
    Recent = detailed, older = compressed.
    """
    TURN = "turn"           # Individual turn summary (1-2 sentences)
    SESSION = "session"     # Session summary (1 paragraph)
    USER = "user"           # Long-term user summary (key patterns/preferences)


@dataclass
class ConversationTurn:
    """A single turn in a conversation."""
    turn_id: int
    role: str               # "user" or "assistant"
    content: str
    timestamp: datetime
    token_count: int = 0
    summary: str = ""       # Compressed version


@dataclass
class SessionSummary:
    """Summary of an entire conversation session."""
    session_id: str
    user_id: str
    start_time: datetime
    end_time: datetime
    turn_count: int
    summary: str
    key_entities: List[str] = field(default_factory=list)
    outcome: str = ""


class SlidingWindowManager:
    """
    Implements the sliding window with summarization pattern.

    Key Principle: Keep detailed history for recent interactions,
    summarize everything older. Total token usage stays bounded.

    Example structure:
    - Summarized history (turns 1-50): compressed to ~500 tokens
    - Detailed history (turns 51-60): full content, ~2000 tokens
    - Current turn (turn 61): full content
    """

    def __init__(self, window_size: int = 10, max_summary_tokens: int = 500):
        self.window_size = window_size
        self.max_summary_tokens = max_summary_tokens

        self._all_turns: List[ConversationTurn] = []
        self._summarized_history: str = ""

    def add_turn(self, role: str, content: str) -> None:
        """Add a new turn to the conversation."""
        turn = ConversationTurn(
            turn_id=len(self._all_turns) + 1,
            role=role,
            content=content,
            timestamp=datetime.now(),
            token_count=len(content.split())  # Rough estimate
        )
        self._all_turns.append(turn)

        # Compact if window exceeded
        if len(self._all_turns) > self.window_size:
            self._compact_oldest()

    def _compact_oldest(self) -> None:
        """
        Summarize the oldest turn and move to summary buffer.

        In production, this would use an LLM to generate the summary.
        """
        oldest = self._all_turns[0]

        # Generate summary (simplified - real would use LLM)
        summary = self._generate_turn_summary(oldest)

        # Add to summarized history
        if self._summarized_history:
            self._summarized_history += f" {summary}"
        else:
            self._summarized_history = summary

        # Remove from detailed history
        self._all_turns = self._all_turns[1:]

    def _generate_turn_summary(self, turn: ConversationTurn) -> str:
        """
        Generate a summary of a single turn.

        In production, use an LLM with a prompt like:
        "Summarize this conversation turn in 1-2 sentences,
         preserving key facts and decisions."
        """
        # Simplified: just extract first sentence and key info
        content = turn.content
        if len(content) > 100:
            # Take first 100 chars and indicate truncation
            summary = f"[{turn.role.upper()}] {content[:100]}..."
        else:
            summary = f"[{turn.role.upper()}] {content}"

        return summary

    def get_context(self) -> str:
        """
        Get the full context for the LLM prompt.

        Returns a combination of:
        1. Summarized older history
        2. Detailed recent history
        """
        parts = []

        if self._summarized_history:
            parts.append(f"## Previous Context (Summarized)\n{self._summarized_history}")

        if self._all_turns:
            detailed = "\n".join(
                f"{turn.role}: {turn.content}"
                for turn in self._all_turns
            )
            parts.append(f"## Recent Conversation\n{detailed}")

        return "\n\n".join(parts)

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the context."""
        summary_tokens = len(self._summarized_history.split())
        detailed_tokens = sum(t.token_count for t in self._all_turns)

        return {
            "total_turns": len(self._all_turns),
            "summarized_turns": 0,  # Would track this in production
            "summary_tokens": summary_tokens,
            "detailed_tokens": detailed_tokens,
            "total_tokens": summary_tokens + detailed_tokens
        }


class HierarchicalSummarizer:
    """
    Implements hierarchical summarization at multiple levels.

    Key Principle: Different time horizons need different granularity:
    - Per-turn: Captures essence of each exchange (5:1 compression)
    - Per-session: Distills entire conversation (10:1 compression)
    - Per-user: Long-term patterns and preferences (20:1 compression)
    """

    def __init__(self):
        self._turn_summaries: Dict[int, str] = {}
        self._session_summaries: Dict[str, SessionSummary] = {}
        self._user_profiles: Dict[str, Dict[str, Any]] = {}

    def summarize_turn(self, turn: ConversationTurn) -> str:
        """
        Generate a turn-level summary.

        Target: 1-2 sentences capturing the key exchange.
        Compression ratio: ~5:1
        """
        # In production, use LLM with this prompt:
        # "Summarize this turn in 1-2 sentences. Preserve:
        #  - Key facts mentioned
        #  - Decisions made
        #  - Questions asked/answered"

        # Simplified implementation
        content = turn.content
        if turn.role == "user":
            summary = f"User asked about: {content[:50]}..."
        else:
            summary = f"Assistant provided: {content[:50]}..."

        self._turn_summaries[turn.turn_id] = summary
        return summary

    def summarize_session(self, session_id: str, user_id: str,
                          turns: List[ConversationTurn]) -> SessionSummary:
        """
        Generate a session-level summary.

        Target: 1 paragraph capturing the entire conversation.
        Compression ratio: ~10:1
        """
        # In production, use LLM with this prompt:
        # "Summarize this conversation in one paragraph:
        #  - What was the main topic/issue?
        #  - What information was exchanged?
        #  - What was the outcome/resolution?"

        # Simplified implementation
        topics = set()
        for turn in turns:
            # Extract key words (simplified)
            words = turn.content.lower().split()
            for word in words:
                if len(word) > 6:  # Longer words likely more meaningful
                    topics.add(word)

        summary = SessionSummary(
            session_id=session_id,
            user_id=user_id,
            start_time=turns[0].timestamp if turns else datetime.now(),
            end_time=turns[-1].timestamp if turns else datetime.now(),
            turn_count=len(turns),
            summary=f"Session covered: {', '.join(list(topics)[:5])}",
            key_entities=list(topics)[:10],
            outcome="resolved" if any("thank" in t.content.lower() for t in turns) else "unknown"
        )

        self._session_summaries[session_id] = summary
        return summary

    def update_user_profile(self, user_id: str,
                            session_summary: SessionSummary) -> Dict[str, Any]:
        """
        Update long-term user profile from session summary.

        Target: Key patterns and preferences across all interactions.
        Compression ratio: ~20:1
        """
        if user_id not in self._user_profiles:
            self._user_profiles[user_id] = {
                "common_topics": [],
                "session_count": 0,
                "resolution_rate": 0.0,
                "preferences": {}
            }

        profile = self._user_profiles[user_id]
        profile["session_count"] += 1
        profile["common_topics"].extend(session_summary.key_entities[:3])

        # Keep only top N topics
        from collections import Counter
        topic_counts = Counter(profile["common_topics"])
        profile["common_topics"] = [t for t, _ in topic_counts.most_common(10)]

        return profile


@dataclass
class SemanticCompressor:
    """
    Semantic compression extracts structured information from verbose text.

    Key Principle: Identify and preserve high-information content,
    ruthlessly prune low-information filler.

    Techniques:
    - Entity extraction: Pull out key names, concepts, facts
    - Coreference resolution: "the customer" -> "John" (one reference)
    - Redundancy removal: Deduplicate repeated information
    """

    def compress(self, text: str) -> Dict[str, Any]:
        """
        Extract structured information from verbose text.

        In production, use an LLM with a structured extraction prompt.
        """
        # Simplified implementation
        words = text.split()

        # Extract potential entities (capitalized words)
        entities = [w for w in words if w and w[0].isupper()]

        # Extract numbers (potential facts)
        numbers = [w for w in words if any(c.isdigit() for c in w)]

        # Key phrases (simplified)
        key_phrases = []
        if "return" in text.lower():
            key_phrases.append("return_related")
        if "order" in text.lower():
            key_phrases.append("order_related")

        return {
            "entities": list(set(entities))[:10],
            "numbers": numbers[:5],
            "key_phrases": key_phrases,
            "original_length": len(words),
            "compressed_length": len(entities) + len(numbers) + len(key_phrases)
        }


# =============================================================================
# Demonstration
# =============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("Context Compaction Demonstration")
    print("=" * 70)

    # Example 1: Sliding Window
    print("\n[1] Sliding Window with Summarization")
    print("-" * 50)

    window = SlidingWindowManager(window_size=5)

    # Simulate a conversation
    conversation = [
        ("user", "Hi, I'd like to return a product I bought last week."),
        ("assistant", "Of course! I'd be happy to help with your return. Could you provide your order number?"),
        ("user", "Yes, it's ORD-12345. I bought wireless headphones."),
        ("assistant", "Thank you. I found order ORD-12345 for Wireless Headphones Pro, purchased 5 days ago. What's the reason for the return?"),
        ("user", "They don't fit my ears properly, the sound quality isn't what I expected."),
        ("assistant", "I understand. Comfort is important! Since it's within our 15-day electronics return window, you're eligible for a full refund."),
        ("user", "Great! How do I send them back?"),
        ("assistant", "I'll generate a prepaid shipping label for you. You'll receive it via email within 5 minutes."),
        ("user", "Perfect, thank you so much for your help!"),
        ("assistant", "You're welcome! Is there anything else I can help you with today?"),
    ]

    for role, content in conversation:
        window.add_turn(role, content)
        print(f"  Added turn: {role[:4]}... ({len(content.split())} words)")

    print("\n  Context for LLM:")
    print("  " + "-" * 40)
    context = window.get_context()
    print(f"  {context[:300]}...")

    print("\n  Stats:", window.get_stats())

    # Example 2: Hierarchical Summarization
    print("\n[2] Hierarchical Summarization")
    print("-" * 50)

    summarizer = HierarchicalSummarizer()

    # Create turns for summarization
    turns = [
        ConversationTurn(i+1, role, content, datetime.now())
        for i, (role, content) in enumerate(conversation)
    ]

    # Turn-level summary
    print("\n  Turn Summaries (5:1 compression):")
    for turn in turns[:3]:
        summary = summarizer.summarize_turn(turn)
        print(f"    Turn {turn.turn_id}: {summary}")

    # Session-level summary
    print("\n  Session Summary (10:1 compression):")
    session = summarizer.summarize_session("sess-001", "user-123", turns)
    print(f"    {session.summary}")
    print(f"    Entities: {session.key_entities[:5]}")
    print(f"    Outcome: {session.outcome}")

    # User profile
    print("\n  User Profile Update (20:1 compression):")
    profile = summarizer.update_user_profile("user-123", session)
    print(f"    Sessions: {profile['session_count']}")
    print(f"    Common topics: {profile['common_topics'][:5]}")

    # Example 3: Semantic Compression
    print("\n[3] Semantic Compression")
    print("-" * 50)

    compressor = SemanticCompressor()
    verbose_text = """
    The customer, John Smith, called on January 15th, 2026 regarding
    order number ORD-98765 for a Samsung Galaxy phone priced at $899.
    John mentioned he had spoken with Sarah from our team last week
    about the same issue. The phone's battery drains too quickly.
    John would like either a replacement or a full refund.
    """

    compressed = compressor.compress(verbose_text)
    print(f"\n  Original: {compressed['original_length']} words")
    print(f"  Compressed: {compressed['compressed_length']} items")
    print(f"  Entities: {compressed['entities']}")
    print(f"  Numbers: {compressed['numbers']}")
    print(f"  Key phrases: {compressed['key_phrases']}")

    print("\n" + "=" * 70)
    print("Key Takeaways:")
    print("1. Sliding window: Recent = detailed, older = summarized")
    print("2. Hierarchical: Turn (5:1) -> Session (10:1) -> User (20:1)")
    print("3. Semantic compression extracts structure from verbose text")
    print("4. Total context stays bounded while preserving critical info")
    print("=" * 70)
