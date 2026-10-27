"""Unit tests for the Product Details MCP tool (API_PRODUCT_SRV).

Verifies that when the agent calls the product details tools, the mock
returns the expected fields and the agent correctly handles the results.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Stub out heavy runtime dependencies not available in the test environment.
for _mod in [
    "litellm", "litellm.exceptions",
    "langchain_litellm",
    "opentelemetry", "opentelemetry.trace",
    "sap_cloud_sdk", "sap_cloud_sdk.aicore", "sap_cloud_sdk.agent_decorators",
    "sap_cloud_sdk.agentgateway",
    "sap_cloud_sdk.agentgateway.converters",
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


def _load_mock() -> dict:
    return json.loads((AGENT_ROOT / "mcp-mock.json").read_text())


def _get_server(slug: str) -> dict:
    return _load_mock()["servers"][slug]


class TestProductDetailsToolMock:
    """Tests that the mcp-mock.json contains correct mock data for product detail tools."""

    def test_mock_file_exists(self):
        assert (AGENT_ROOT / "mcp-mock.json").exists(), "mcp-mock.json must exist"

    def test_product_srv_server_present(self):
        mock = _load_mock()
        assert "sap-s4-api-product-srv-mcp-server" in mock["servers"]

    def test_list_a_product_tool_present(self):
        server = _get_server("sap-s4-api-product-srv-mcp-server")
        assert "list_a_product_for_api_product_srv" in server["tools"]

    def test_get_a_product_tool_present(self):
        server = _get_server("sap-s4-api-product-srv-mcp-server")
        assert "get_a_product_for_api_product_srv" in server["tools"]

    def test_list_product_description_tool_present(self):
        server = _get_server("sap-s4-api-product-srv-mcp-server")
        assert "list_a_productdescription_for_api_product_srv" in server["tools"]

    def test_list_product_mock_response_has_required_fields(self):
        server = _get_server("sap-s4-api-product-srv-mcp-server")
        tool = server["tools"]["list_a_product_for_api_product_srv"]
        results = tool["mock_response"]["results"]
        assert len(results) >= 1
        first = results[0]
        assert "Product" in first
        assert "ProductGroup" in first
        assert "BaseUnit" in first

    def test_get_product_mock_response_has_required_fields(self):
        server = _get_server("sap-s4-api-product-srv-mcp-server")
        tool = server["tools"]["get_a_product_for_api_product_srv"]
        product = tool["mock_response"]
        assert product["Product"] == "TG-1050"
        assert product["BaseUnit"] == "EA"
        assert "ProductGroup" in product

    def test_product_description_mock_response_has_description_field(self):
        server = _get_server("sap-s4-api-product-srv-mcp-server")
        tool = server["tools"]["list_a_productdescription_for_api_product_srv"]
        results = tool["mock_response"]["results"]
        assert len(results) >= 1
        assert "ProductDescription" in results[0]
        assert "Language" in results[0]

    def test_metadata_tool_present(self):
        server = _get_server("sap-s4-api-product-srv-mcp-server")
        assert "get_metadata_api_product_srv" in server["tools"]

    def test_input_schema_has_filter_param(self):
        server = _get_server("sap-s4-api-product-srv-mcp-server")
        tool = server["tools"]["list_a_product_for_api_product_srv"]
        props = tool["input_schema"]["properties"]
        assert "$filter" in props
        assert "$top" in props


class TestProductDetailsAgentIntegration:
    """Tests that the agent processes product detail responses correctly."""

    @pytest.fixture(autouse=True)
    def add_app_path(self, add_agent_to_path):
        pass

    def _make_mock_tool(self, tool_name: str, mock_response: dict):
        tool = MagicMock()
        tool.name = tool_name
        tool.description = f"Mock tool {tool_name}"
        tool.args_schema = None
        return tool

    @pytest.mark.asyncio
    async def test_agent_can_be_instantiated(self, add_agent_to_path):
        """Agent should be instantiable without errors."""
        from agent import SampleAgent
        agent = SampleAgent()
        assert agent is not None

    def test_system_prompt_source_contains_product_scope(self, add_agent_to_path):
        """agent.py source should define product master data scope in the prompt string."""
        import inspect
        import agent as agent_module
        source = inspect.getsource(agent_module)
        assert "product master data" in source.lower()
        assert "s/4hana" in source or "S/4HANA" in source

    def test_system_prompt_source_forbids_fabrication(self, add_agent_to_path):
        """agent.py source should instruct the agent never to fabricate data."""
        import inspect
        import agent as agent_module
        source = inspect.getsource(agent_module)
        assert "Never fabricate" in source or "never fabricate" in source.lower() or "MUST use tools" in source

    def test_system_prompt_source_read_only_guardrail(self, add_agent_to_path):
        """agent.py source should declare the read-only guardrail."""
        import inspect
        import agent as agent_module
        source = inspect.getsource(agent_module)
        assert "NEVER create" in source or "never" in source.lower()

    @pytest.mark.asyncio
    async def test_invoke_with_mocked_tools_returns_completed(self, add_agent_to_path):
        """Agent invoke should return a completed response with mocked tools."""
        from agent import SampleAgent

        mock_llm_response = MagicMock()
        mock_llm_response.content = "Product TG-1050 is an Industrial Pressure Gauge with base unit EA."

        mock_tool = MagicMock()
        mock_tool.name = "list_a_product_for_api_product_srv"
        mock_tool.description = "List products"
        mock_tool.args_schema = None

        with patch("agent.ChatLiteLLM") as mock_llm_cls:
            mock_llm_instance = MagicMock()
            mock_llm_cls.return_value = mock_llm_instance

            with patch("agent.create_agent") as mock_create_agent:
                mock_graph = MagicMock()
                mock_graph.ainvoke = AsyncMock(
                    return_value={
                        "messages": [
                            MagicMock(content="Product TG-1050 is an Industrial Pressure Gauge with base unit EA.")
                        ]
                    }
                )
                mock_create_agent.return_value = mock_graph

                agent = SampleAgent()
                result = await agent.invoke(
                    query="What is the description of product TG-1050?",
                    context_id="test-ctx-001",
                    tools=[mock_tool],
                )

        assert result.status == "completed"
        assert result.message is not None
