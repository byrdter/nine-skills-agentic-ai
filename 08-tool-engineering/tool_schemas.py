"""
Tool Schema Design for Agentic Systems

Demonstrates how to design clear, effective tool definitions that
agents can understand and use correctly.

This example shows:
- Tool schema anatomy (name, description, parameters, returns)
- The Four Questions every tool description should answer
- Semantic altitude (too specific vs too general)
- Examples for few-shot learning

Reference: "Golden Tools vs. Dangerous APIs" video - Chapter 2

Key Concept: Tools are the agent's user interface. Poor tool definitions
cause agents to make mistakes - at machine speed, at scale.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum
import json


class RiskLevel(Enum):
    """Tool risk classification."""
    READ_ONLY = "read_only"     # No side effects
    LOW = "low"                 # Minor side effects, reversible
    MEDIUM = "medium"          # Significant side effects
    HIGH = "high"              # Irreversible or dangerous


@dataclass
class ToolExample:
    """
    An example invocation showing input and expected output.

    Examples accelerate learning and reduce trial-and-error.
    """
    description: str
    input: Dict[str, Any]
    output: Dict[str, Any]


@dataclass
class ToolDefinition:
    """
    A complete tool definition following best practices.

    Key Principle: A good tool description answers FOUR questions:
    1. WHAT does this tool do?
    2. WHEN should the agent use it?
    3. WHAT are the inputs and their format?
    4. WHAT will the tool return?
    """
    name: str
    description: str            # Comprehensive description
    parameters: Dict[str, Any]  # JSON Schema
    returns: Dict[str, Any]     # JSON Schema for output

    # Optional metadata
    risk_level: RiskLevel = RiskLevel.READ_ONLY
    requires_approval: bool = False
    examples: List[ToolExample] = field(default_factory=list)
    limitations: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)

    def to_function_schema(self) -> Dict[str, Any]:
        """Convert to function calling schema (OpenAI format)."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters
            }
        }


def create_well_designed_tool() -> ToolDefinition:
    """
    Example of a well-designed tool definition.

    This tool answers all four questions clearly.
    """
    return ToolDefinition(
        name="get_weather",
        description=(
            "Retrieves current weather conditions for a specified location. "
            "\n\n"
            "WHEN TO USE: Use this when the user asks about current weather, "
            "temperature, or conditions for a specific place. Do NOT use for "
            "weather forecasts or historical weather data."
            "\n\n"
            "INPUT: Location can be a city name (e.g., 'Paris') or "
            "city with country (e.g., 'Paris, France') for disambiguation. "
            "Unit should be 'celsius' or 'fahrenheit'."
            "\n\n"
            "OUTPUT: Returns a JSON object with temperature (number), "
            "conditions (string like 'Sunny', 'Cloudy', 'Rainy'), "
            "humidity (percentage), and wind_speed (in appropriate unit)."
        ),
        parameters={
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "City name or city,country format (e.g., 'Paris, France')"
                },
                "unit": {
                    "type": "string",
                    "enum": ["celsius", "fahrenheit"],
                    "default": "celsius",
                    "description": "Temperature unit"
                }
            },
            "required": ["location"]
        },
        returns={
            "type": "object",
            "properties": {
                "temperature": {"type": "number"},
                "conditions": {"type": "string"},
                "humidity": {"type": "number"},
                "wind_speed": {"type": "number"}
            }
        },
        risk_level=RiskLevel.READ_ONLY,
        examples=[
            ToolExample(
                description="Get weather in Tokyo in Celsius",
                input={"location": "Tokyo", "unit": "celsius"},
                output={"temperature": 18, "conditions": "Partly cloudy", "humidity": 65, "wind_speed": 12}
            ),
            ToolExample(
                description="Get weather in NYC in Fahrenheit",
                input={"location": "New York, USA", "unit": "fahrenheit"},
                output={"temperature": 72, "conditions": "Sunny", "humidity": 45, "wind_speed": 8}
            )
        ],
        limitations=[
            "Only provides current weather, not forecasts",
            "May have delays of up to 10 minutes from real-time",
            "Some remote locations may not be available"
        ],
        tags=["weather", "location", "external-api"]
    )


def create_poorly_designed_tool() -> ToolDefinition:
    """
    Example of a poorly designed tool definition.

    This tool is ambiguous and will cause agent errors.
    """
    return ToolDefinition(
        name="get_data",
        description="Gets data from the system.",  # Too vague!
        parameters={
            "type": "object",
            "properties": {
                "id": {"type": "string"}  # What kind of ID? What format?
            }
        },
        returns={
            "type": "object"  # What's in the object?
        },
        risk_level=RiskLevel.READ_ONLY
    )


class SemanticAltitudeAnalyzer:
    """
    Analyzes the semantic altitude of tool descriptions.

    Key Concept: Semantic altitude is the level of abstraction:
    - Too LOW (specific): "Get weather in San Francisco in Fahrenheit" - inflexible
    - Too HIGH (general): "Get information about something" - useless
    - OPTIMAL: "Get current weather for any location in specified units"
    """

    def analyze(self, tool: ToolDefinition) -> Dict[str, Any]:
        """
        Analyze the semantic altitude of a tool description.
        """
        desc = tool.description.lower()

        # Check for overly specific indicators
        specific_indicators = [
            "only for", "specifically", "exactly",
            "must be", "san francisco", "new york"  # Hardcoded locations
        ]
        specific_count = sum(1 for ind in specific_indicators if ind in desc)

        # Check for overly general indicators
        general_indicators = [
            "something", "anything", "data", "information",
            "stuff", "things", "various"
        ]
        general_count = sum(1 for ind in general_indicators if ind in desc)

        # Check for good indicators
        good_indicators = [
            "when to use", "returns", "input", "output",
            "format", "example", "unit", "parameter"
        ]
        good_count = sum(1 for ind in good_indicators if ind in desc)

        # Determine altitude
        if specific_count > 2:
            altitude = "TOO_LOW"
            recommendation = "Make the tool more flexible and reusable"
        elif general_count > 2 or len(desc) < 50:
            altitude = "TOO_HIGH"
            recommendation = "Add specific details about when/how to use"
        else:
            altitude = "OPTIMAL"
            recommendation = "Good balance of specificity and flexibility"

        return {
            "altitude": altitude,
            "description_length": len(desc),
            "has_when_to_use": "when to use" in desc or "use this when" in desc,
            "has_input_details": "input" in desc or "parameter" in desc,
            "has_output_details": "output" in desc or "return" in desc,
            "has_examples": len(tool.examples) > 0,
            "recommendation": recommendation
        }


# =============================================================================
# Demonstration
# =============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("Tool Schema Design Demonstration")
    print("=" * 70)

    # Compare good vs bad tool definitions
    print("\n[1] Well-Designed Tool")
    print("-" * 50)

    good_tool = create_well_designed_tool()
    print(f"  Name: {good_tool.name}")
    print(f"  Risk Level: {good_tool.risk_level.value}")
    print(f"  Examples: {len(good_tool.examples)}")
    print(f"  Limitations documented: {len(good_tool.limitations)}")
    print(f"\n  Description (answers 4 questions):")
    print(f"  {good_tool.description[:200]}...")

    print("\n[2] Poorly-Designed Tool")
    print("-" * 50)

    bad_tool = create_poorly_designed_tool()
    print(f"  Name: {bad_tool.name}")
    print(f"  Description: '{bad_tool.description}'")
    print("  Problems:")
    print("    - What data? What system?")
    print("    - When should the agent use this?")
    print("    - What format is the ID?")
    print("    - What's in the output?")

    # Semantic altitude analysis
    print("\n[3] Semantic Altitude Analysis")
    print("-" * 50)

    analyzer = SemanticAltitudeAnalyzer()

    for tool, label in [(good_tool, "Well-designed"), (bad_tool, "Poorly-designed")]:
        analysis = analyzer.analyze(tool)
        print(f"\n  {label} Tool:")
        print(f"    Altitude: {analysis['altitude']}")
        print(f"    Has 'when to use': {analysis['has_when_to_use']}")
        print(f"    Has input details: {analysis['has_input_details']}")
        print(f"    Has output details: {analysis['has_output_details']}")
        print(f"    Recommendation: {analysis['recommendation']}")

    # Show function schema format
    print("\n[4] Function Calling Schema (OpenAI Format)")
    print("-" * 50)
    schema = good_tool.to_function_schema()
    print(json.dumps(schema, indent=2)[:500] + "...")

    print("\n" + "=" * 70)
    print("Key Takeaways:")
    print("1. Answer FOUR questions: What, When, Inputs, Outputs")
    print("2. Include examples for few-shot learning")
    print("3. Document limitations clearly")
    print("4. Optimal semantic altitude: specific enough to be useful,")
    print("   flexible enough to be reusable")
    print("=" * 70)
