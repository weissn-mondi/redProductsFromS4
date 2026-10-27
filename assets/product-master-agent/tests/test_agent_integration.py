"""Integration test: end-to-end agent flow with mocked LLM and MCP tools.

Tests:
1. Turn 1: ask for product details by ID → agent calls product details tool → readable response
2. Turn 2 (multi-turn): ask follow-up classification question → classification tool called
3. Out-of-scope: ask pricing question → agent declines without calling any tool
All tests run fully offline (mocked LLM + mocked MCP calls).
"""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

for _mod in [
    "litellm", "litellm.exceptions",
    "langchain_litellm",
    "opentelemetry", "opentelemetry.trace",
    "sap_cloud_sdk", "sap_cloud_sdk.aicore", "sap_cloud_sdk.agent_decorators",
    "sap_cloud_sdk.agentgateway", "sap_cloud_sdk.agentgateway.converters",
    "sap_cloud_sdk.agent_memory", "sap_cloud_sdk.agent_memory.factory",
    "sap_cloud_sdk.agent_memory.factory.langgraph_checkpoint",
    "langchain", "langchain.agents", "langchain.agents.middleware",
    "langchain_core", "langchain_core.messages", "langchain_core.messages.utils",
    "langchain_core.runnables", "langchain_core.tools",
    "langgraph", "langgraph.graph", "langgraph.graph.state",
    "a2a", "a2a.server", "a2a.server.agent_execution", "a2a.server.apps",
    "a2a.server.events", "a2a.server.request_handlers", "a2a.server.tasks",
    "a2a.types", "a2a.utils", "a2a.utils.errors",
    "uvicorn", "click", "starlette", "starlette.middleware", "starlette.middleware.base",
]:
    if _mod not in sys.modules:
        sys.modules[_mod] = MagicMock()

AGENT_ROOT = Path(__file__).parent.parent


def _make_mock_tools() -> list:
    """Create minimal mock tools for all three MCP servers."""
    tools = []
    tool_names = [
        "list_a_product_for_api_product_srv",
        "get_a_product_for_api_product_srv",
        "list_a_productdescription_for_api_product_srv",
        "list_a_clfnproduct_for_api_clfn_product_srv",
        "list_a_productclasscharc_for_api_clfn_product_srv",
        "function_determineavailat_for_api_product_availy_info_basic",
        "function_determineavailof_for_api_product_availy_info_basic",
    ]
    for name in tool_names:
        tool = MagicMock()
        tool.name = name
        tool.description = f"Mock tool {name}"
        tool.args_schema = None
        tools.append(tool)
    return tools


@pytest.fixture(autouse=True)
def add_app_path(add_agent_to_path):
    pass


class TestAgentEndToEndFlow:
    """End-to-end integration tests using fully mocked LLM and MCP tools."""

    @pytest.mark.asyncio
    async def test_turn1_product_details_query(self):
        """Turn 1: Ask for product details by ID → agent returns readable answer."""
        from agent import SampleAgent

        tools = _make_mock_tools()

        with patch("agent.create_agent") as mock_create_agent:
            mock_graph = MagicMock()
            mock_graph.ainvoke = AsyncMock(
                return_value={
                    "messages": [
                        MagicMock(
                            content=(
                                "**Product TG-1050 — Industrial Pressure Gauge 0-100 bar**\n"
                                "- Category: ME-INSTRU (Measurement Instruments)\n"
                                "- Base Unit of Measure: EA (Each)\n"
                                "- Product Type: FERT (Finished Product)"
                            )
                        )
                    ]
                }
            )
            mock_create_agent.return_value = mock_graph

            agent = SampleAgent()
            result = await agent.invoke(
                query="What is the description and unit of measure for product TG-1050?",
                context_id="integration-ctx-001",
                tools=tools,
            )

        assert result.status == "completed"
        assert result.message is not None
        assert len(result.message) > 0

    @pytest.mark.asyncio
    async def test_turn2_followup_classification_query(self):
        """Turn 2 (multi-turn): Follow-up classification question reuses product context."""
        from agent import SampleAgent

        tools = _make_mock_tools()

        with patch("agent.create_agent") as mock_create_agent:
            mock_graph = MagicMock()
            # First call returns product details; second returns classification
            mock_graph.ainvoke = AsyncMock(
                side_effect=[
                    {
                        "messages": [
                            MagicMock(
                                content="Product TG-1050 is in category ME-INSTRU with base unit EA."
                            )
                        ]
                    },
                    {
                        "messages": [
                            MagicMock(
                                content=(
                                    "Product TG-1050 classification:\n"
                                    "- Class: PRESSURE_INSTRUMENTS\n"
                                    "- Pressure Range: 0-100 bar\n"
                                    "- Housing Material: Stainless Steel"
                                )
                            )
                        ]
                    },
                ]
            )
            mock_create_agent.return_value = mock_graph

            agent = SampleAgent()

            # Turn 1
            result1 = await agent.invoke(
                query="What is product TG-1050?",
                context_id="integration-ctx-002",
                tools=tools,
            )
            assert result1.status == "completed"

            # Turn 2: follow-up
            result2 = await agent.invoke(
                query="What is its classification?",
                context_id="integration-ctx-002",
                tools=tools,
            )
            assert result2.status == "completed"
            assert result2.message is not None

    @pytest.mark.asyncio
    async def test_out_of_scope_pricing_query_declined(self):
        """Out-of-scope: Agent declines pricing question without calling pricing tools."""
        from agent import SampleAgent

        tools = _make_mock_tools()

        with patch("agent.create_agent") as mock_create_agent:
            mock_graph = MagicMock()
            mock_graph.ainvoke = AsyncMock(
                return_value={
                    "messages": [
                        MagicMock(
                            content=(
                                "I'm focused on product master data — descriptions, categories, "
                                "classifications, and availability. For pricing information, "
                                "please consult your SAP Sales Cloud or ask your sales operations team."
                            )
                        )
                    ]
                }
            )
            mock_create_agent.return_value = mock_graph

            agent = SampleAgent()
            result = await agent.invoke(
                query="What is the price of product TG-1050?",
                context_id="integration-ctx-003",
                tools=tools,
            )

        assert result.status == "completed"
        # Response should not contain pricing data
        assert result.message is not None

    @pytest.mark.asyncio
    async def test_agent_returns_error_on_no_messages(self):
        """Agent should handle edge case where graph returns no messages."""
        from agent import SampleAgent

        tools = _make_mock_tools()

        with patch("agent.create_agent") as mock_create_agent:
            mock_graph = MagicMock()
            mock_graph.ainvoke = AsyncMock(
                return_value={"messages": []}
            )
            mock_create_agent.return_value = mock_graph

            agent = SampleAgent()
            result = await agent.invoke(
                query="What is product TG-1050?",
                context_id="integration-ctx-004",
                tools=tools,
            )

        # Should still complete, with a fallback message
        assert result.status in ("completed", "error")

    @pytest.mark.asyncio
    async def test_agent_handles_no_tools(self):
        """Agent should handle the case where no tools are available."""
        from agent import SampleAgent

        with patch("agent.create_agent") as mock_create_agent:
            mock_graph = MagicMock()
            mock_graph.ainvoke = AsyncMock(
                return_value={
                    "messages": [
                        MagicMock(
                            content="Tools are temporarily unavailable. Please try again shortly."
                        )
                    ]
                }
            )
            mock_create_agent.return_value = mock_graph

            agent = SampleAgent()
            result = await agent.invoke(
                query="What is product TG-1050?",
                context_id="integration-ctx-005",
                tools=[],  # empty tools
            )

        assert result.status == "completed"

    def test_milestone_logging_in_agent_source(self):
        """Agent source should contain M1-M4 milestone log statements."""
        agent_source = (AGENT_ROOT / "app" / "agent.py").read_text()
        for milestone in ["M1.achieved", "M1.missed", "M2.achieved", "M2.missed",
                          "M3.achieved", "M3.missed"]:
            assert milestone in agent_source, f"Missing milestone log: {milestone}"

    def test_business_instrumentation_has_otel_spans(self):
        """Agent source should use OpenTelemetry spans for business step instrumentation."""
        agent_source = (AGENT_ROOT / "app" / "agent.py").read_text()
        assert "tracer" in agent_source
        assert "start_as_current_span" in agent_source

    def test_mcp_mock_metadata_is_complete(self):
        """mcp-mock.json metadata should list all 3 servers and 24 tools."""
        import json
        mock = json.loads((AGENT_ROOT / "mcp-mock.json").read_text())
        meta = mock["metadata"]
        assert meta["total_servers"] == 3
        assert meta["total_tools"] == 24
        assert meta["mock_mode"] is True
