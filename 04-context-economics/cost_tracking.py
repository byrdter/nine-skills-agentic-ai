"""
Token Cost Tracking and Budget Management

Demonstrates how to monitor, attribute, and control LLM token costs
in production agentic systems.

This example shows:
- Per-request cost calculation
- Budget allocation by team/project/workflow
- Cost anomaly detection
- Optimization recommendations

Reference: "The $10,000 Prompt" video - Chapter 4

Key Concept: If you can't measure it, you can't optimize it.
Cost visibility is the foundation of context economics.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from enum import Enum
from collections import defaultdict
import math


@dataclass
class TokenPricing:
    """
    Token pricing for different models.

    Prices are per 1M tokens as of 2026.
    Input tokens are typically cheaper than output tokens.
    """
    model_name: str
    input_price_per_million: float      # $ per 1M input tokens
    output_price_per_million: float     # $ per 1M output tokens
    cached_input_price_per_million: float = 0.0  # $ per 1M cached tokens


# Common model pricing (fictional, for demonstration)
MODEL_PRICING = {
    "gpt-4o": TokenPricing("gpt-4o", 2.50, 10.00, 1.25),
    "gpt-4o-mini": TokenPricing("gpt-4o-mini", 0.15, 0.60, 0.075),
    "claude-3-5-sonnet": TokenPricing("claude-3-5-sonnet", 3.00, 15.00, 0.30),
    "claude-3-5-haiku": TokenPricing("claude-3-5-haiku", 0.25, 1.25, 0.03),
    "gemini-1.5-pro": TokenPricing("gemini-1.5-pro", 1.25, 5.00, 0.0625),
}


@dataclass
class UsageRecord:
    """Record of a single LLM API call."""
    request_id: str
    timestamp: datetime
    model: str

    # Token counts
    input_tokens: int
    output_tokens: int
    cached_tokens: int = 0

    # Attribution
    team_id: str = ""
    project_id: str = ""
    workflow_id: str = ""
    user_id: str = ""

    # Computed cost
    cost_usd: float = 0.0

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)


class CostTracker:
    """
    Tracks and analyzes LLM token costs.

    Key Principle: Attribution enables accountability.
    Know WHAT is costing money, WHO is spending it, and WHY.
    """

    def __init__(self):
        self._records: List[UsageRecord] = []
        self._budgets: Dict[str, float] = {}  # team_id -> budget_usd

        # Aggregations for fast queries
        self._cost_by_team: Dict[str, float] = defaultdict(float)
        self._cost_by_model: Dict[str, float] = defaultdict(float)
        self._cost_by_workflow: Dict[str, float] = defaultdict(float)

    def record_usage(self, record: UsageRecord) -> UsageRecord:
        """
        Record an LLM API call and calculate cost.

        This should be called after every LLM invocation.
        """
        # Calculate cost
        pricing = MODEL_PRICING.get(record.model)
        if pricing:
            input_cost = (record.input_tokens / 1_000_000) * pricing.input_price_per_million
            output_cost = (record.output_tokens / 1_000_000) * pricing.output_price_per_million
            cached_cost = (record.cached_tokens / 1_000_000) * pricing.cached_input_price_per_million

            record.cost_usd = input_cost + output_cost + cached_cost

        # Store record
        self._records.append(record)

        # Update aggregations
        self._cost_by_team[record.team_id] += record.cost_usd
        self._cost_by_model[record.model] += record.cost_usd
        self._cost_by_workflow[record.workflow_id] += record.cost_usd

        # Check budget alerts
        self._check_budget_alert(record)

        return record

    def set_budget(self, team_id: str, budget_usd: float) -> None:
        """Set a monthly budget for a team."""
        self._budgets[team_id] = budget_usd

    def _check_budget_alert(self, record: UsageRecord) -> None:
        """Check if a team is approaching budget limits."""
        if record.team_id in self._budgets:
            budget = self._budgets[record.team_id]
            spent = self._cost_by_team[record.team_id]

            if spent > budget * 0.9:
                print(f"  ⚠️  BUDGET ALERT: {record.team_id} at {spent/budget:.0%} of budget")
            elif spent > budget * 0.75:
                print(f"  📊 Budget notice: {record.team_id} at {spent/budget:.0%} of budget")

    def get_summary(self, time_window_hours: int = 24) -> Dict[str, Any]:
        """Get a summary of costs within a time window."""
        cutoff = datetime.now() - timedelta(hours=time_window_hours)
        recent = [r for r in self._records if r.timestamp > cutoff]

        total_cost = sum(r.cost_usd for r in recent)
        total_input = sum(r.input_tokens for r in recent)
        total_output = sum(r.output_tokens for r in recent)
        total_cached = sum(r.cached_tokens for r in recent)

        return {
            "time_window_hours": time_window_hours,
            "request_count": len(recent),
            "total_cost_usd": round(total_cost, 4),
            "total_input_tokens": total_input,
            "total_output_tokens": total_output,
            "total_cached_tokens": total_cached,
            "cache_hit_rate": total_cached / max(1, total_input + total_cached),
            "cost_by_team": dict(self._cost_by_team),
            "cost_by_model": dict(self._cost_by_model),
            "cost_by_workflow": dict(self._cost_by_workflow),
        }

    def get_cost_breakdown(self, group_by: str = "model") -> List[Dict[str, Any]]:
        """
        Get cost breakdown by different dimensions.

        Args:
            group_by: "model", "team", "workflow", or "day"
        """
        if group_by == "model":
            aggregation = self._cost_by_model
        elif group_by == "team":
            aggregation = self._cost_by_team
        elif group_by == "workflow":
            aggregation = self._cost_by_workflow
        else:
            # Group by day
            aggregation = defaultdict(float)
            for r in self._records:
                day_key = r.timestamp.strftime("%Y-%m-%d")
                aggregation[day_key] += r.cost_usd

        total = sum(aggregation.values())
        return [
            {
                "key": k,
                "cost_usd": round(v, 4),
                "percentage": round(v / max(total, 0.01) * 100, 1)
            }
            for k, v in sorted(aggregation.items(), key=lambda x: x[1], reverse=True)
        ]


class AnomalyDetector:
    """
    Detects cost anomalies in LLM usage.

    Key Principle: Set alerts for unusual patterns - a runaway loop
    can burn through thousands of dollars before anyone notices.
    """

    def __init__(self, window_size: int = 100):
        self._recent_costs: List[float] = []
        self.window_size = window_size
        self.alert_threshold_std = 3.0  # Alert if > 3 standard deviations

    def check(self, record: UsageRecord) -> Optional[Dict[str, Any]]:
        """
        Check if a request's cost is anomalous.

        Returns alert details if anomalous, None otherwise.
        """
        cost = record.cost_usd

        # Need enough history to detect anomalies
        if len(self._recent_costs) < 10:
            self._recent_costs.append(cost)
            return None

        # Calculate statistics
        mean = sum(self._recent_costs) / len(self._recent_costs)
        variance = sum((x - mean) ** 2 for x in self._recent_costs) / len(self._recent_costs)
        std = math.sqrt(variance) if variance > 0 else 0.01

        # Check for anomaly
        z_score = (cost - mean) / std if std > 0 else 0

        # Update history
        self._recent_costs.append(cost)
        if len(self._recent_costs) > self.window_size:
            self._recent_costs.pop(0)

        if abs(z_score) > self.alert_threshold_std:
            return {
                "type": "cost_spike" if z_score > 0 else "cost_drop",
                "request_id": record.request_id,
                "cost_usd": cost,
                "z_score": round(z_score, 2),
                "expected_cost": round(mean, 4),
                "message": f"Cost {cost:.4f} is {abs(z_score):.1f}x std from mean {mean:.4f}"
            }

        return None


class OptimizationRecommender:
    """
    Analyzes usage patterns and recommends cost optimizations.

    Key Principle: Data-driven optimization beats intuition.
    """

    @staticmethod
    def analyze(tracker: CostTracker) -> List[Dict[str, Any]]:
        """Generate optimization recommendations based on usage patterns."""
        recommendations = []
        summary = tracker.get_summary(time_window_hours=168)  # 1 week

        # Check cache hit rate
        cache_rate = summary.get("cache_hit_rate", 0)
        if cache_rate < 0.3:
            recommendations.append({
                "category": "caching",
                "priority": "high",
                "current": f"{cache_rate:.0%} cache hit rate",
                "recommendation": "Restructure prompts for prefix caching (static content first)",
                "potential_savings": "30-50%"
            })

        # Check model selection
        model_costs = tracker.get_cost_breakdown(group_by="model")
        expensive_model_spend = sum(
            m["cost_usd"] for m in model_costs
            if "gpt-4o" in m["key"] or "sonnet" in m["key"]
        )
        total_spend = sum(m["cost_usd"] for m in model_costs)

        if expensive_model_spend > total_spend * 0.8:
            recommendations.append({
                "category": "model_selection",
                "priority": "medium",
                "current": f"{expensive_model_spend/total_spend:.0%} on large models",
                "recommendation": "Route simple queries to smaller/cheaper models",
                "potential_savings": "40-60%"
            })

        # Check output length
        output_tokens = summary.get("total_output_tokens", 0)
        input_tokens = summary.get("total_input_tokens", 0)
        if output_tokens > input_tokens * 2:
            recommendations.append({
                "category": "output_length",
                "priority": "medium",
                "current": f"Output/input ratio: {output_tokens/max(input_tokens,1):.1f}x",
                "recommendation": "Add 'be concise' instructions, limit max_tokens",
                "potential_savings": "20-30%"
            })

        return recommendations


# =============================================================================
# Demonstration
# =============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("Token Cost Tracking Demonstration")
    print("=" * 70)

    # Create tracker and anomaly detector
    tracker = CostTracker()
    anomaly_detector = AnomalyDetector()

    # Set budgets
    tracker.set_budget("customer-service", 1000.0)  # $1000/month
    tracker.set_budget("data-analysis", 500.0)      # $500/month

    # Simulate usage records
    print("\n[1] Recording Usage")
    print("-" * 50)

    import random
    usage_data = [
        # (model, input_tokens, output_tokens, cached_tokens, team, workflow)
        ("claude-3-5-haiku", 500, 200, 300, "customer-service", "chat"),
        ("claude-3-5-haiku", 600, 150, 400, "customer-service", "chat"),
        ("gpt-4o", 2000, 500, 0, "data-analysis", "report"),
        ("claude-3-5-sonnet", 1500, 800, 1000, "customer-service", "escalation"),
        ("gpt-4o-mini", 300, 100, 200, "customer-service", "chat"),
        ("claude-3-5-haiku", 450, 175, 350, "customer-service", "chat"),
        ("gpt-4o", 3000, 1000, 500, "data-analysis", "analysis"),
        ("claude-3-5-haiku", 500, 200, 400, "customer-service", "chat"),
    ]

    for i, (model, input_t, output_t, cached_t, team, workflow) in enumerate(usage_data):
        record = UsageRecord(
            request_id=f"req-{i+1:03d}",
            timestamp=datetime.now(),
            model=model,
            input_tokens=input_t,
            output_tokens=output_t,
            cached_tokens=cached_t,
            team_id=team,
            workflow_id=workflow
        )

        record = tracker.record_usage(record)
        alert = anomaly_detector.check(record)

        print(f"  {record.request_id}: {model:20} {record.cost_usd:>8.4f} USD")
        if alert:
            print(f"    ⚠️  ANOMALY: {alert['message']}")

    # Show summary
    print("\n[2] Cost Summary (24h)")
    print("-" * 50)
    summary = tracker.get_summary(time_window_hours=24)
    print(f"  Total cost: ${summary['total_cost_usd']:.4f}")
    print(f"  Requests: {summary['request_count']}")
    print(f"  Cache hit rate: {summary['cache_hit_rate']:.1%}")

    # Cost breakdown
    print("\n[3] Cost Breakdown by Model")
    print("-" * 50)
    for item in tracker.get_cost_breakdown(group_by="model"):
        print(f"  {item['key']:25} ${item['cost_usd']:>8.4f} ({item['percentage']}%)")

    print("\n[4] Cost Breakdown by Team")
    print("-" * 50)
    for item in tracker.get_cost_breakdown(group_by="team"):
        budget = tracker._budgets.get(item["key"], 0)
        budget_pct = item["cost_usd"] / budget * 100 if budget > 0 else 0
        print(f"  {item['key']:20} ${item['cost_usd']:>8.4f} ({budget_pct:.1f}% of budget)")

    # Optimization recommendations
    print("\n[5] Optimization Recommendations")
    print("-" * 50)
    recommendations = OptimizationRecommender.analyze(tracker)
    for rec in recommendations:
        print(f"\n  [{rec['priority'].upper()}] {rec['category']}")
        print(f"    Current: {rec['current']}")
        print(f"    Recommendation: {rec['recommendation']}")
        print(f"    Potential savings: {rec['potential_savings']}")

    if not recommendations:
        print("  ✓ No critical optimizations needed")

    print("\n" + "=" * 70)
    print("Key Takeaways:")
    print("1. Track every API call with full attribution (team, workflow, user)")
    print("2. Set budgets and alert thresholds proactively")
    print("3. Anomaly detection catches runaway loops early")
    print("4. Data-driven recommendations beat intuition")
    print("=" * 70)
