"""
Prefix Caching for Context Optimization

Demonstrates how to structure prompts for maximum cache hits.
Prefix caching stores computed KV (Key-Value) states for repeated
prompt beginnings, dramatically reducing latency and cost.

This example shows:
- Cache-friendly prompt structure (static -> dynamic)
- Platform-specific caching strategies (Anthropic, OpenAI, Gemini)
- Workflow-aware cache management

Reference: "The $10,000 Prompt" video - Chapter 2

Key Concept: If two requests share the same prefix (beginning),
the expensive KV computation is cached and reused.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from enum import Enum


class CacheStatus(Enum):
    """Status of a cache entry."""
    HIT = "hit"           # Cached state was reused
    MISS = "miss"         # No cached state, full computation
    PARTIAL = "partial"   # Some prefix cached, some computed
    EXPIRED = "expired"   # Cache existed but TTL expired


@dataclass
class CachedPrefix:
    """
    Represents a cached prefix and its computed KV state.

    In production, the actual KV cache is managed by the LLM provider.
    This simulates the concept for educational purposes.
    """
    prefix_hash: str
    token_count: int
    created_at: datetime
    last_accessed: datetime
    access_count: int = 0

    # Platform-specific TTL
    ttl_seconds: int = 300  # Anthropic: 5 minutes, can be extended


@dataclass
class PromptStructure:
    """
    A cache-optimized prompt structure.

    Key Principle: Place STATIC content at the BEGINNING.
    Place DYNAMIC content at the END.

    This maximizes prefix reuse across requests.
    """
    # Layer 1: System prompt (rarely changes) - ALWAYS CACHED
    system_prompt: str

    # Layer 2: RAG context (changes per topic, not per query) - OFTEN CACHED
    rag_context: str = ""

    # Layer 3: Conversation history (grows over session) - SOMETIMES CACHED
    conversation_history: List[Dict[str, str]] = field(default_factory=list)

    # Layer 4: Current user query (unique every time) - NEVER CACHED
    current_query: str = ""

    def to_full_prompt(self) -> str:
        """Assemble the full prompt in cache-friendly order."""
        parts = [self.system_prompt]

        if self.rag_context:
            parts.append(f"\n\n## Context\n{self.rag_context}")

        if self.conversation_history:
            history_str = "\n".join(
                f"{msg['role']}: {msg['content']}"
                for msg in self.conversation_history
            )
            parts.append(f"\n\n## Conversation History\n{history_str}")

        if self.current_query:
            parts.append(f"\n\n## Current Query\n{self.current_query}")

        return "\n".join(parts)

    def estimate_cache_boundary(self) -> int:
        """
        Estimate where the cacheable prefix ends.

        Everything before this point can potentially be cached.
        Everything after is unique per request.
        """
        cached_parts = [self.system_prompt]

        if self.rag_context:
            cached_parts.append(f"\n\n## Context\n{self.rag_context}")

        # Note: conversation history is NOT included in cache estimate
        # because it changes with each turn

        cached_text = "\n".join(cached_parts)
        return len(cached_text.split())  # Rough token estimate


class PrefixCacheSimulator:
    """
    Simulates prefix caching behavior for educational purposes.

    In production, this is handled by the LLM provider:
    - Anthropic: beta.prompt_caching API
    - OpenAI: Automatic caching
    - Gemini: Context caching API

    Key Principle: Understand caching to structure prompts optimally.
    """

    def __init__(self, ttl_seconds: int = 300, min_prefix_tokens: int = 1024):
        self._cache: Dict[str, CachedPrefix] = {}
        self.ttl_seconds = ttl_seconds
        self.min_prefix_tokens = min_prefix_tokens  # Anthropic minimum

        # Statistics
        self.total_requests = 0
        self.cache_hits = 0
        self.tokens_saved = 0

    def _hash_prefix(self, prefix: str) -> str:
        """Generate a hash for the prefix."""
        import hashlib
        return hashlib.sha256(prefix.encode()).hexdigest()[:16]

    def _estimate_tokens(self, text: str) -> int:
        """Rough token estimation (real would use tokenizer)."""
        return len(text.split()) * 1.3  # Approximation

    def check_cache(self, prompt: PromptStructure) -> tuple[CacheStatus, int]:
        """
        Check if the prompt's prefix is cached.

        Returns:
            (status, tokens_saved)
        """
        self.total_requests += 1

        # Calculate cacheable prefix (system prompt + RAG context)
        cacheable = prompt.system_prompt
        if prompt.rag_context:
            cacheable += f"\n\n## Context\n{prompt.rag_context}"

        prefix_hash = self._hash_prefix(cacheable)
        prefix_tokens = int(self._estimate_tokens(cacheable))

        # Check minimum token requirement
        if prefix_tokens < self.min_prefix_tokens:
            return (CacheStatus.MISS, 0)

        # Check if cached
        if prefix_hash in self._cache:
            cached = self._cache[prefix_hash]
            now = datetime.now()

            # Check TTL
            if (now - cached.created_at).seconds > self.ttl_seconds:
                del self._cache[prefix_hash]
                return (CacheStatus.EXPIRED, 0)

            # Cache hit!
            cached.last_accessed = now
            cached.access_count += 1
            self.cache_hits += 1
            self.tokens_saved += prefix_tokens

            return (CacheStatus.HIT, prefix_tokens)

        # Cache miss - store for future
        self._cache[prefix_hash] = CachedPrefix(
            prefix_hash=prefix_hash,
            token_count=prefix_tokens,
            created_at=datetime.now(),
            last_accessed=datetime.now()
        )

        return (CacheStatus.MISS, 0)

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        hit_rate = self.cache_hits / max(1, self.total_requests)
        return {
            "total_requests": self.total_requests,
            "cache_hits": self.cache_hits,
            "hit_rate": f"{hit_rate:.1%}",
            "tokens_saved": self.tokens_saved,
            "cached_prefixes": len(self._cache)
        }


# =============================================================================
# Platform-Specific Caching Patterns
# =============================================================================

@dataclass
class PlatformCachingConfig:
    """
    Platform-specific caching configurations.

    Different providers have different caching characteristics.
    Optimize your strategy for your chosen platform.
    """
    name: str
    min_prefix_tokens: int
    default_ttl_minutes: int
    cost_reduction: str
    explicit_api: bool
    notes: str


PLATFORM_CONFIGS = {
    "anthropic": PlatformCachingConfig(
        name="Anthropic",
        min_prefix_tokens=1024,
        default_ttl_minutes=5,
        cost_reduction="90%",
        explicit_api=True,
        notes="Use beta.prompt_caching, cache_control breakpoints"
    ),
    "openai": PlatformCachingConfig(
        name="OpenAI",
        min_prefix_tokens=0,  # Automatic
        default_ttl_minutes=60,  # Automatic management
        cost_reduction="50%",
        explicit_api=False,
        notes="Automatic caching, no API changes needed"
    ),
    "gemini": PlatformCachingConfig(
        name="Google Gemini",
        min_prefix_tokens=32000,  # Up to 32K tokens
        default_ttl_minutes=60,
        cost_reduction="Variable (hourly storage cost)",
        explicit_api=True,
        notes="Explicit cache creation API, hourly storage fees"
    )
}


def demonstrate_bad_vs_good_structure():
    """
    Demonstrate BAD vs GOOD prompt structure for caching.

    Key Insight: The ORDER of content matters for cache efficiency.
    """
    print("\n" + "=" * 60)
    print("BAD vs GOOD Prompt Structure")
    print("=" * 60)

    print("\n[BAD] Dynamic content FIRST (no caching possible):")
    print("-" * 40)
    bad_structure = """
User Query: {query}           <-- Changes every request!

System: You are a helpful assistant...

Context: {rag_context}        <-- Often same topic
"""
    print(bad_structure)
    print("  Problem: Dynamic query at the START destroys caching.")
    print("           Every request computes from scratch.")

    print("\n[GOOD] Static content FIRST (maximum caching):")
    print("-" * 40)
    good_structure = """
System: You are a helpful assistant...  <-- Static, ALWAYS cached

Context: {rag_context}                  <-- Semi-static, OFTEN cached

Conversation: {history}                 <-- Dynamic, SOMETIMES cached

User Query: {query}                     <-- Unique, NEVER cached
"""
    print(good_structure)
    print("  Benefit: Static prefix cached, only unique part computed.")
    print("           50-90% cost reduction possible.")


# =============================================================================
# Demonstration
# =============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("Prefix Caching Demonstration")
    print("=" * 70)

    # Create cache simulator
    cache = PrefixCacheSimulator(ttl_seconds=300, min_prefix_tokens=100)

    # Create a cache-friendly prompt structure
    system_prompt = """You are a helpful customer service assistant for ExampleCorp.

Guidelines:
- Always be polite and professional
- Cite specific policy sections when relevant
- If unsure, escalate to human support
- Never share customer data externally

Available tools: search_orders, get_policy, create_ticket
"""

    rag_context = """## Return Policy (v2.3, Updated Jan 2026)

Section 4.1: Standard Returns
- Items may be returned within 30 days of purchase
- Original packaging required
- Receipt or order confirmation needed

Section 4.2: Exceptions
- Electronics: 15-day return window
- Sale items: Final sale, no returns
- Custom orders: Non-returnable
"""

    # Simulate multiple requests
    print("\n[1] Simulating Multiple Requests")
    print("-" * 50)

    queries = [
        "What's your return policy?",
        "Can I return headphones I bought last week?",
        "The product arrived damaged, what do I do?",
        "How long do I have to return something?",
    ]

    for query in queries:
        prompt = PromptStructure(
            system_prompt=system_prompt,
            rag_context=rag_context,
            current_query=query
        )

        status, tokens_saved = cache.check_cache(prompt)
        print(f"\n  Query: '{query[:40]}...'")
        print(f"  Cache Status: {status.value}")
        if tokens_saved > 0:
            print(f"  Tokens Saved: ~{tokens_saved}")

    # Show cache statistics
    print("\n[2] Cache Statistics")
    print("-" * 50)
    stats = cache.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")

    # Show prompt structure
    print("\n[3] Cache-Friendly Prompt Structure")
    print("-" * 50)
    prompt = PromptStructure(
        system_prompt=system_prompt,
        rag_context=rag_context,
        current_query="Example query"
    )
    print(f"  Cacheable prefix: ~{prompt.estimate_cache_boundary()} tokens")
    print("  Structure layers:")
    print("    1. System Prompt (static)     -> ALWAYS CACHED")
    print("    2. RAG Context (semi-static)  -> OFTEN CACHED")
    print("    3. Conversation (dynamic)     -> SOMETIMES CACHED")
    print("    4. Current Query (unique)     -> NEVER CACHED")

    # Platform comparison
    print("\n[4] Platform-Specific Caching")
    print("-" * 50)
    for platform, config in PLATFORM_CONFIGS.items():
        print(f"\n  {config.name}:")
        print(f"    Cost reduction: {config.cost_reduction}")
        print(f"    Min prefix: {config.min_prefix_tokens} tokens")
        print(f"    TTL: {config.default_ttl_minutes} minutes")
        print(f"    Notes: {config.notes}")

    # Bad vs Good structure
    demonstrate_bad_vs_good_structure()

    print("\n" + "=" * 70)
    print("Key Takeaways:")
    print("1. Static content FIRST, dynamic content LAST")
    print("2. System prompt + RAG context = highly cacheable prefix")
    print("3. Different platforms have different caching characteristics")
    print("4. 50-90% cost reduction possible with proper structure")
    print("=" * 70)
