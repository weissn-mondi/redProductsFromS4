"""Unit tests for the Product Classification MCP tool (API_CLFN_PRODUCT_SRV)."""
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


class TestProductClassificationToolMock:
    """Tests that mcp-mock.json has correct mock data for classification tools."""

    def test_clfn_server_present(self):
        mock = _load_mock()
        assert "sap-s4-api-clfn-product-srv-mcp-server" in mock["servers"]

    def test_list_clfnproduct_tool_present(self):
        server = _get_server("sap-s4-api-clfn-product-srv-mcp-server")
        assert "list_a_clfnproduct_for_api_clfn_product_srv" in server["tools"]

    def test_get_clfnproduct_tool_present(self):
        server = _get_server("sap-s4-api-clfn-product-srv-mcp-server")
        assert "get_a_clfnproduct_for_api_clfn_product_srv" in server["tools"]

    def test_list_productclasscharc_tool_present(self):
        server = _get_server("sap-s4-api-clfn-product-srv-mcp-server")
        assert "list_a_productclasscharc_for_api_clfn_product_srv" in server["tools"]

    def test_get_productclasscharc_tool_present(self):
        server = _get_server("sap-s4-api-clfn-product-srv-mcp-server")
        assert "get_a_productclasscharc_for_api_clfn_product_srv" in server["tools"]

    def test_clfnproduct_mock_has_class_fields(self):
        server = _get_server("sap-s4-api-clfn-product-srv-mcp-server")
        tool = server["tools"]["list_a_clfnproduct_for_api_clfn_product_srv"]
        results = tool["mock_response"]["results"]
        assert len(results) >= 1
        first = results[0]
        assert "Product" in first
        assert "Class" in first
        assert "ClassType" in first

    def test_productclasscharc_mock_has_characteristic_fields(self):
        server = _get_server("sap-s4-api-clfn-product-srv-mcp-server")
        tool = server["tools"]["list_a_productclasscharc_for_api_clfn_product_srv"]
        results = tool["mock_response"]["results"]
        assert len(results) >= 1
        first = results[0]
        assert "Characteristic" in first
        assert "CharacteristicValue" in first
        assert "CharacteristicDescription" in first

    def test_mock_has_realistic_class_name(self):
        server = _get_server("sap-s4-api-clfn-product-srv-mcp-server")
        tool = server["tools"]["list_a_clfnproduct_for_api_clfn_product_srv"]
        class_name = tool["mock_response"]["results"][0]["Class"]
        assert isinstance(class_name, str)
        assert len(class_name) > 0

    def test_mock_has_two_characteristics(self):
        server = _get_server("sap-s4-api-clfn-product-srv-mcp-server")
        tool = server["tools"]["list_a_productclasscharc_for_api_clfn_product_srv"]
        results = tool["mock_response"]["results"]
        assert len(results) >= 2, "Should have at least 2 characteristic values"

    def test_metadata_tool_present(self):
        server = _get_server("sap-s4-api-clfn-product-srv-mcp-server")
        assert "get_metadata_api_clfn_product_srv" in server["tools"]


class TestClassificationToolIntegration:
    """Integration tests for classification tool handling."""

    @pytest.fixture(autouse=True)
    def add_app_path(self, add_agent_to_path):
        pass

    def test_skill_file_exists(self):
        """Product-query skill file must exist."""
        skill_path = AGENT_ROOT / "app" / "skills" / "product-query" / "SKILL.md"
        assert skill_path.exists(), f"Skill file not found: {skill_path}"

    def test_skill_has_classification_section(self):
        """Product-query skill must mention classification."""
        skill_path = AGENT_ROOT / "app" / "skills" / "product-query" / "SKILL.md"
        content = skill_path.read_text()
        assert "classification" in content.lower()

    def test_skill_has_out_of_scope_handling(self):
        """Product-query skill must have out-of-scope handling instructions."""
        skill_path = AGENT_ROOT / "app" / "skills" / "product-query" / "SKILL.md"
        content = skill_path.read_text()
        assert "pricing" in content.lower() or "out-of-scope" in content.lower()

    def test_skill_has_frontmatter(self):
        """Product-query skill must have YAML frontmatter."""
        skill_path = AGENT_ROOT / "app" / "skills" / "product-query" / "SKILL.md"
        content = skill_path.read_text()
        assert content.startswith("---")
        assert "name:" in content
        assert "description:" in content

    @pytest.mark.asyncio
    async def test_agent_invoke_classification_query(self):
        """Agent should handle classification queries and return completed status."""
        from agent import SampleAgent

        mock_tool = MagicMock()
        mock_tool.name = "list_a_clfnproduct_for_api_clfn_product_srv"
        mock_tool.description = "List product classifications"
        mock_tool.args_schema = None

        with patch("agent.create_agent") as mock_create_agent:
            mock_graph = MagicMock()
            mock_graph.ainvoke = AsyncMock(
                return_value={
                    "messages": [
                        MagicMock(
                            content="Product TG-1050 belongs to class PRESSURE_INSTRUMENTS. "
                            "Characteristics: Pressure Range=0-100 bar, Material=Stainless Steel."
                        )
                    ]
                }
            )
            mock_create_agent.return_value = mock_graph

            agent = SampleAgent()
            result = await agent.invoke(
                query="What classification does product TG-1050 belong to?",
                context_id="test-cls-001",
                tools=[mock_tool],
            )

        assert result.status == "completed"
        assert result.message is not None
