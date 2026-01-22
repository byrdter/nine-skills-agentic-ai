"""
Semantic Quality Metrics for Agentic Systems

Demonstrates how to evaluate and track AI output quality beyond
traditional latency and error metrics.

This example shows:
- LLM-as-judge evaluation patterns
- Multi-dimensional quality scoring (groundedness, relevance, toxicity)
- Quality gates for production deployment
- A/B testing and regression detection

Reference: "When AI Breaks: Observability for Agentic Systems" video - Chapter 3

Key Concept: Traditional metrics (latency, error rate) don't tell you
if the AI is giving GOOD answers. Semantic quality metrics do.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum
import random


class QualityDimension(Enum):
    """
    Dimensions of AI output quality.

    Key Principle: Quality is multi-dimensional. An answer can be
    accurate but irrelevant, or relevant but hallucinated.
    """
    GROUNDEDNESS = "groundedness"   # Is it supported by provided sources?
    RELEVANCE = "relevance"         # Does it answer the question asked?
    COHERENCE = "coherence"         # Is it internally consistent?
    COMPLETENESS = "completeness"   # Does it fully address the question?
    TOXICITY = "toxicity"           # Is it harmful or offensive?
    HELPFULNESS = "helpfulness"     # Is it actually useful?


@dataclass
class QualityScore:
    """
    A quality score for a single dimension.

    Scores are typically 0.0-1.0 where:
    - 0.0-0.3: Poor (failing)
    - 0.3-0.6: Needs improvement
    - 0.6-0.8: Good
    - 0.8-1.0: Excellent
    """
    dimension: QualityDimension
    score: float                    # 0.0 to 1.0
    confidence: float = 1.0         # Evaluator confidence in this score
    explanation: str = ""           # Why this score?
    evidence: List[str] = field(default_factory=list)  # Supporting evidence


@dataclass
class QualityEvaluation:
    """
    Complete quality evaluation for an agent response.

    Key Principle: Evaluate multiple dimensions and aggregate
    appropriately for your use case.
    """
    evaluation_id: str
    request_id: str
    timestamp: datetime = field(default_factory=datetime.now)

    # Input context
    user_query: str = ""
    agent_response: str = ""
    retrieved_context: str = ""

    # Scores by dimension
    scores: Dict[QualityDimension, QualityScore] = field(default_factory=dict)

    # Aggregate score
    overall_score: float = 0.0

    # Evaluator metadata
    evaluator_model: str = ""
    evaluation_latency_ms: float = 0.0

    def calculate_overall(self, weights: Optional[Dict[QualityDimension, float]] = None) -> float:
        """
        Calculate weighted overall score.

        Different use cases may weight dimensions differently:
        - Medical: High weight on groundedness
        - Creative: High weight on helpfulness, lower on groundedness
        - Customer service: Balanced across all
        """
        if not self.scores:
            return 0.0

        if weights is None:
            # Default: equal weights
            weights = {dim: 1.0 for dim in self.scores.keys()}

        total_weight = sum(weights.get(dim, 0) for dim in self.scores.keys())
        if total_weight == 0:
            return 0.0

        weighted_sum = sum(
            score.score * weights.get(score.dimension, 1.0)
            for score in self.scores.values()
        )

        self.overall_score = weighted_sum / total_weight
        return self.overall_score

    def passes_gate(self, thresholds: Dict[QualityDimension, float]) -> tuple[bool, List[str]]:
        """
        Check if this evaluation passes quality gates.

        Returns (passed, list_of_failures)
        """
        failures = []

        for dimension, threshold in thresholds.items():
            if dimension in self.scores:
                if self.scores[dimension].score < threshold:
                    failures.append(
                        f"{dimension.value}: {self.scores[dimension].score:.2f} < {threshold:.2f}"
                    )

        return (len(failures) == 0, failures)


class LLMAsJudge:
    """
    Uses an LLM to evaluate the quality of another LLM's output.

    Key Principle: LLMs are surprisingly good at judging quality
    when given clear rubrics and examples.

    In production, use:
    - Smaller/faster model as judge (cost efficiency)
    - Multiple judges for critical evaluations (consensus)
    - Human calibration to align judge scores with human judgment
    """

    def __init__(self, judge_model: str = "claude-3-5-haiku"):
        self.judge_model = judge_model

    def evaluate(self, query: str, response: str, context: str = "") -> QualityEvaluation:
        """
        Evaluate an agent response across multiple quality dimensions.

        In production, this would call an LLM with evaluation prompts.
        This simplified version simulates the evaluation.
        """
        evaluation = QualityEvaluation(
            evaluation_id=f"eval-{random.randint(1000, 9999)}",
            request_id=f"req-{random.randint(1000, 9999)}",
            user_query=query,
            agent_response=response,
            retrieved_context=context,
            evaluator_model=self.judge_model
        )

        # Evaluate each dimension (simulated - real would use LLM)
        evaluation.scores[QualityDimension.GROUNDEDNESS] = self._evaluate_groundedness(
            response, context
        )
        evaluation.scores[QualityDimension.RELEVANCE] = self._evaluate_relevance(
            query, response
        )
        evaluation.scores[QualityDimension.COHERENCE] = self._evaluate_coherence(
            response
        )
        evaluation.scores[QualityDimension.HELPFULNESS] = self._evaluate_helpfulness(
            query, response
        )

        # Calculate overall score
        evaluation.calculate_overall()

        return evaluation

    def _evaluate_groundedness(self, response: str, context: str) -> QualityScore:
        """
        Evaluate if the response is grounded in provided context.

        Real prompt would be:
        "Given the context below, evaluate if the response makes claims
         that are supported by the context. Score 0-1 where 1 means
         all claims are directly supported."
        """
        # Simulated scoring
        score = 0.85 + random.uniform(-0.15, 0.10)

        return QualityScore(
            dimension=QualityDimension.GROUNDEDNESS,
            score=min(1.0, max(0.0, score)),
            explanation="Most claims are supported by provided context",
            evidence=["Response references specific policy sections"]
        )

    def _evaluate_relevance(self, query: str, response: str) -> QualityScore:
        """
        Evaluate if the response actually answers the question asked.

        Key: A response can be accurate but not answer what was asked.
        """
        score = 0.80 + random.uniform(-0.10, 0.15)

        return QualityScore(
            dimension=QualityDimension.RELEVANCE,
            score=min(1.0, max(0.0, score)),
            explanation="Response directly addresses the user's question"
        )

    def _evaluate_coherence(self, response: str) -> QualityScore:
        """Evaluate internal consistency and logical flow."""
        score = 0.90 + random.uniform(-0.10, 0.08)

        return QualityScore(
            dimension=QualityDimension.COHERENCE,
            score=min(1.0, max(0.0, score)),
            explanation="Response is logically structured and consistent"
        )

    def _evaluate_helpfulness(self, query: str, response: str) -> QualityScore:
        """Evaluate if the response is actually useful to the user."""
        score = 0.75 + random.uniform(-0.10, 0.20)

        return QualityScore(
            dimension=QualityDimension.HELPFULNESS,
            score=min(1.0, max(0.0, score)),
            explanation="Response provides actionable information"
        )


class QualityTracker:
    """
    Tracks quality metrics over time for trend analysis and alerting.

    Key Principle: Track quality continuously, not just during testing.
    Production quality can drift due to:
    - Data distribution shifts
    - Model updates
    - Context/RAG changes
    """

    def __init__(self, alert_threshold: float = 0.6):
        self._evaluations: List[QualityEvaluation] = []
        self.alert_threshold = alert_threshold
        self._historical_scores: List[float] = []

    def record(self, evaluation: QualityEvaluation) -> Optional[Dict[str, Any]]:
        """
        Record an evaluation and check for quality degradation.

        Returns an alert if quality has degraded significantly.
        """
        self._evaluations.append(evaluation)
        self._historical_scores.append(evaluation.overall_score)

        # Check for alerts
        if evaluation.overall_score < self.alert_threshold:
            return {
                "type": "quality_below_threshold",
                "score": evaluation.overall_score,
                "threshold": self.alert_threshold,
                "evaluation_id": evaluation.evaluation_id
            }

        # Check for regression (compare to recent average)
        if len(self._historical_scores) > 10:
            recent_avg = sum(self._historical_scores[-10:]) / 10
            overall_avg = sum(self._historical_scores) / len(self._historical_scores)

            if recent_avg < overall_avg - 0.1:  # 10% drop
                return {
                    "type": "quality_regression",
                    "recent_average": recent_avg,
                    "overall_average": overall_avg,
                    "drop": overall_avg - recent_avg
                }

        return None

    def get_summary(self, last_n: int = 100) -> Dict[str, Any]:
        """Get summary statistics for recent evaluations."""
        recent = self._evaluations[-last_n:]
        if not recent:
            return {}

        scores = [e.overall_score for e in recent]

        # Calculate stats by dimension
        by_dimension = {}
        for dim in QualityDimension:
            dim_scores = [
                e.scores[dim].score for e in recent
                if dim in e.scores
            ]
            if dim_scores:
                by_dimension[dim.value] = {
                    "mean": sum(dim_scores) / len(dim_scores),
                    "min": min(dim_scores),
                    "max": max(dim_scores)
                }

        return {
            "evaluation_count": len(recent),
            "overall_mean": sum(scores) / len(scores),
            "overall_min": min(scores),
            "overall_max": max(scores),
            "by_dimension": by_dimension,
            "below_threshold_count": sum(1 for s in scores if s < self.alert_threshold)
        }


# =============================================================================
# Quality Gates for Production Deployment
# =============================================================================

@dataclass
class QualityGate:
    """
    Quality gates that must pass before deploying to production.

    Key Principle: Don't deploy if quality benchmarks aren't met.
    """
    name: str
    dimension_thresholds: Dict[QualityDimension, float]
    overall_threshold: float
    required_sample_size: int = 100


def run_quality_gate(gate: QualityGate, evaluations: List[QualityEvaluation]) -> Dict[str, Any]:
    """
    Run a quality gate against a set of evaluations.

    Returns gate result with pass/fail status and details.
    """
    if len(evaluations) < gate.required_sample_size:
        return {
            "passed": False,
            "reason": f"Insufficient samples: {len(evaluations)} < {gate.required_sample_size}"
        }

    # Check overall score
    overall_avg = sum(e.overall_score for e in evaluations) / len(evaluations)
    if overall_avg < gate.overall_threshold:
        return {
            "passed": False,
            "reason": f"Overall score {overall_avg:.2f} < {gate.overall_threshold}"
        }

    # Check each dimension
    for dimension, threshold in gate.dimension_thresholds.items():
        dim_scores = [
            e.scores[dimension].score for e in evaluations
            if dimension in e.scores
        ]
        if dim_scores:
            dim_avg = sum(dim_scores) / len(dim_scores)
            if dim_avg < threshold:
                return {
                    "passed": False,
                    "reason": f"{dimension.value} score {dim_avg:.2f} < {threshold}"
                }

    return {
        "passed": True,
        "overall_score": overall_avg,
        "sample_size": len(evaluations)
    }


# =============================================================================
# Demonstration
# =============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("Semantic Quality Metrics Demonstration")
    print("=" * 70)

    # Create evaluator and tracker
    judge = LLMAsJudge(judge_model="claude-3-5-haiku")
    tracker = QualityTracker(alert_threshold=0.6)

    # Simulate evaluating several agent responses
    print("\n[1] Evaluating Agent Responses")
    print("-" * 50)

    test_cases = [
        {
            "query": "What is your return policy?",
            "response": "Items can be returned within 30 days for a full refund. "
                       "Electronics have a 15-day window. Sale items are final sale.",
            "context": "Return Policy v2.3: 30-day returns, electronics 15 days, "
                      "sale items non-returnable."
        },
        {
            "query": "How do I track my order?",
            "response": "You can track your order using the tracking number in "
                       "your confirmation email. Visit our tracking page and enter the number.",
            "context": "Order tracking available at example.com/track with order number."
        },
        {
            "query": "Can I get a refund?",
            "response": "I'd be happy to help with your refund request. What item "
                       "would you like to return and when did you purchase it?",
            "context": "Refunds processed within 5-7 business days after return received."
        },
    ]

    evaluations = []
    for i, case in enumerate(test_cases):
        eval_result = judge.evaluate(
            query=case["query"],
            response=case["response"],
            context=case["context"]
        )
        evaluations.append(eval_result)

        # Record and check for alerts
        alert = tracker.record(eval_result)

        print(f"\n  Case {i+1}: '{case['query'][:40]}...'")
        print(f"  Overall Score: {eval_result.overall_score:.2f}")
        for dim, score in eval_result.scores.items():
            print(f"    {dim.value:15} {score.score:.2f}")

        if alert:
            print(f"  ⚠️  ALERT: {alert}")

    # Quality Gate Check
    print("\n[2] Quality Gate Check")
    print("-" * 50)

    gate = QualityGate(
        name="production-deployment",
        dimension_thresholds={
            QualityDimension.GROUNDEDNESS: 0.7,
            QualityDimension.RELEVANCE: 0.7,
            QualityDimension.HELPFULNESS: 0.6
        },
        overall_threshold=0.7,
        required_sample_size=3
    )

    gate_result = run_quality_gate(gate, evaluations)
    print(f"  Gate: {gate.name}")
    print(f"  Passed: {gate_result['passed']}")
    if gate_result['passed']:
        print(f"  Overall Score: {gate_result['overall_score']:.2f}")
    else:
        print(f"  Reason: {gate_result['reason']}")

    # Summary statistics
    print("\n[3] Quality Summary")
    print("-" * 50)
    summary = tracker.get_summary()
    print(f"  Evaluations: {summary.get('evaluation_count', 0)}")
    print(f"  Overall Mean: {summary.get('overall_mean', 0):.2f}")
    print(f"  Below Threshold: {summary.get('below_threshold_count', 0)}")

    print("\n  By Dimension:")
    for dim, stats in summary.get("by_dimension", {}).items():
        print(f"    {dim:15} mean={stats['mean']:.2f} "
              f"(min={stats['min']:.2f}, max={stats['max']:.2f})")

    print("\n" + "=" * 70)
    print("Key Takeaways:")
    print("1. Quality is multi-dimensional: groundedness, relevance, coherence, etc.")
    print("2. LLM-as-judge enables scalable quality evaluation")
    print("3. Quality gates prevent deploying degraded models")
    print("4. Continuous tracking catches regressions before users notice")
    print("=" * 70)
