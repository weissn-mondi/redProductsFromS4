"""Unit tests for the Product Availability MCP tool (API_PRODUCT_AVAILY_INFO_BASIC)."""
from __future__ import annotations

import json
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


def _load_mock() -> dict:
    return json.loads((AGENT_ROOT / "mcp-mock.json").read_text())


def _get_server(slug: str) -> dict:
    return _load_mock()["servers"][slug]


class TestProductAvailabilityToolMock:
    """Tests that mcp-mock.json has correct mock data for availability tools."""

    def test_availability_server_present(self):
        mock = _load_mock()
        assert "sap-s4-api-product-availy-info-basic-mcp-server" in mock["servers"]

    def test_determine_avail_at_tool_present(self):
        server = _get_server("sap-s4-api-product-availy-info-basic-mcp-server")
        assert "function_determineavailat_for_api_product_availy_info_basic" in server["tools"]

    def test_determine_avail_of_tool_present(self):
        server = _get_server("sap-s4-api-product-availy-info-basic-mcp-server")
        assert "function_determineavailof_for_api_product_availy_info_basic" in server["tools"]

    def test_calc_avail_timeseries_tool_present(self):
        server = _get_server("sap-s4-api-product-availy-info-basic-mcp-server")
        assert "function_calcavailtimeseries_for_api_product_availy_info_basic" in server["tools"]

    def test_determine_avail_at_mock_has_availability_fields(self):
        server = _get_server("sap-s4-api-product-availy-info-basic-mcp-server")
        tool = server["tools"]["function_determineavailat_for_api_product_availy_info_basic"]
        response = tool["mock_response"]
        assert "AvailableQuantityInBaseUnit" in response
        assert "BaseUnit" in response
        assert "PeriodStartUTCDateTime" in response

    def test_determine_avail_of_mock_has_availability_fields(self):
        server = _get_server("sap-s4-api-product-availy-info-basic-mcp-server")
        tool = server["tools"]["function_determineavailof_for_api_product_availy_info_basic"]
        response = tool["mock_response"]
        assert "AvailableQuantityInBaseUnit" in response
        assert "BaseUnit" in response

    def test_avail_quantity_is_positive(self):
        server = _get_server("sap-s4-api-product-availy-info-basic-mcp-server")
        tool = server["tools"]["function_determineavailat_for_api_product_availy_info_basic"]
        qty = float(tool["mock_response"]["AvailableQuantityInBaseUnit"])
        assert qty > 0

    def test_timeseries_mock_has_multiple_periods(self):
        server = _get_server("sap-s4-api-product-availy-info-basic-mcp-server")
        tool = server["tools"]["function_calcavailtimeseries_for_api_product_availy_info_basic"]
        results = tool["mock_response"]["results"]
        assert len(results) >= 2, "Timeseries should have at least 2 periods"

    def test_determine_avail_at_requires_plant_and_material(self):
        server = _get_server("sap-s4-api-product-availy-info-basic-mcp-server")
        tool = server["tools"]["function_determineavailat_for_api_product_availy_info_basic"]
        required = tool["input_schema"].get("required", [])
        assert "SupplyingPlant" in required
        assert "Material" in required

    def test_metadata_tool_present(self):
        server = _get_server("sap-s4-api-product-availy-info-basic-mcp-server")
        assert "get_metadata_api_product_availy_info_basic" in server["tools"]

    def test_base_unit_is_ea_in_mock(self):
        """Mock availability should use EA as base unit (each) for the test product."""
        server = _get_server("sap-s4-api-product-availy-info-basic-mcp-server")
        tool = server["tools"]["function_determineavailat_for_api_product_availy_info_basic"]
        assert tool["mock_response"]["BaseUnit"] == "EA"


class TestAvailabilityToolIntegration:
    """Integration tests for availability tool handling."""

    @pytest.fixture(autouse=True)
    def add_app_path(self, add_agent_to_path):
        pass

    @pytest.mark.asyncio
    async def test_agent_invoke_availability_query(self):
        """Agent should handle availability queries and return completed status."""
        from agent import SampleAgent

        mock_tool = MagicMock()
        mock_tool.name = "function_determineavailat_for_api_product_availy_info_basic"
        mock_tool.description = "Determine product availability at a specific date"
        mock_tool.args_schema = None

        with patch("agent.create_agent") as mock_create_agent:
            mock_graph = MagicMock()
            mock_graph.ainvoke = AsyncMock(
                return_value={
                    "messages": [
                        MagicMock(
                            content="Product TG-1050 is currently available at plant 1000 "
                            "with 250 EA available."
                        )
                    ]
                }
            )
            mock_create_agent.return_value = mock_graph

            agent = SampleAgent()
            result = await agent.invoke(
                query="Is product TG-1050 available at plant 1000?",
                context_id="test-avail-001",
                tools=[mock_tool],
            )

        assert result.status == "completed"
        assert result.message is not None

    @pytest.mark.asyncio
    async def test_agent_handles_api_error_gracefully(self):
        """Agent should return error status gracefully when API call fails."""
        from agent import SampleAgent

        mock_tool = MagicMock()
        mock_tool.name = "function_determineavailat_for_api_product_availy_info_basic"
        mock_tool.description = "Determine product availability"
        mock_tool.args_schema = None

        with patch("agent.create_agent") as mock_create_agent:
            mock_graph = MagicMock()
            mock_graph.ainvoke = AsyncMock(
                return_value={
                    "messages": [
                        MagicMock(
                            content="I was unable to retrieve availability for product TG-1050. "
                            "The API returned an error: 404 Product not found."
                        )
                    ]
                }
            )
            mock_create_agent.return_value = mock_graph

            agent = SampleAgent()
            result = await agent.invoke(
                query="Is product XYZ-999 available?",
                context_id="test-avail-error-001",
                tools=[mock_tool],
            )

        assert result.status == "completed"
        assert result.message is not None
