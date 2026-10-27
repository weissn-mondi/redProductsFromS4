# Specification: product-master-agent

> **Guidelines**: Read all applicable guidelines before executing ANY tasks below:
> - [guidelines.md](../guidelines.md) — Universal execution rules
> - [guidelines-agent.md](../guidelines-agent.md) — Universal agent patterns
> - [guidelines-agent-python.md](../guidelines-agent-python.md) — Python implementation details
> - [guidelines-agent-skills.md](../guidelines-agent-skills.md) — Runtime skills patterns
> - [guidelines-agent-mcp.md](../guidelines-agent-mcp.md) — MCP integration patterns

---

## Data Dependencies

No Data Product ORD IDs. All data is accessed via S/4HANA OData APIs through custom MCP tools (Path A).

---

## API Integrations

Three S/4HANA Cloud Public Edition OData APIs are used. API spec files are downloaded and ready at:

- `specification/product-master-agent/api-specs/API_PRODUCT_SRV.edmx` — Product Master (A2X), ORD ID: `sap.s4:apiResource:API_PRODUCT_SRV:v1`
- `specification/product-master-agent/api-specs/API_CLFN_PRODUCT_SRV.edmx` — Product Master Data Including Classification, ORD ID: `sap.s4:apiResource:API_CLFN_PRODUCT_SRV:v1`
- `specification/product-master-agent/api-specs/API_PRODUCT_AVAILY_INFO_BASIC.edmx` — Basic Product Availability Info, ORD ID: `sap.s4:apiResource:API_PRODUCT_AVAILY_INFO_BASIC:v1`

### MCP Tool Scope

```
MCP API: sap.s4:apiResource:API_PRODUCT_SRV:v1
MCP tool scope: read-only
Resources in scope: A_Product, A_ProductDescription, A_ProductPlant
```

```
MCP API: sap.s4:apiResource:API_CLFN_PRODUCT_SRV:v1
MCP tool scope: read-only
Resources in scope: A_ClfnProduct, A_ClfnProductClassCharc
```

```
MCP API: sap.s4:apiResource:API_PRODUCT_AVAILY_INFO_BASIC:v1
MCP tool scope: read-only
Resources in scope: all
```

---

## Basic Setup

- [x] Read `product-requirements-document.md` and `intent.md` before starting
- [x] Bootstrap agent code in `assets/product-master-agent/` using the `sap-agent-bootstrap` instructions from the agent skill. Run bootstrap from inside `assets/product-master-agent/` using copy commands — do NOT create files manually
- [x] Install dependencies and validate the agent starts and responds at `/.well-known/agent.json`

---

## Runtime Skills

- [x] Review whether runtime skills are needed (see [guidelines-agent-skills.md](../guidelines-agent-skills.md))
- [x] **Decision**: A runtime skill is recommended for the product query domain:
  - Create `assets/product-master-agent/app/skills/product-query/SKILL.md` with:
    - YAML frontmatter: `name: product-query`, `description: Instructions for answering Sales Rep product master data questions`
    - Body: step-by-step instructions for resolving product queries — identify whether the user provides a product ID or name, call the appropriate MCP tool, format the response in plain language, handle missing products gracefully

---

## Project-Specific Tasks

### System Prompt

- [x] Open `assets/product-master-agent/app/agent.py` and configure the system prompt (`@prompt_section` / `get_system_prompt`) with:
  - Agent identity: "You are a product master data assistant for Sales Representatives. You answer natural language questions about SAP S/4HANA product master data."
  - Scope statement: "You can answer questions about product descriptions, categories, units of measure, product classifications, characteristics, and basic product availability. You cannot answer questions about pricing, sales orders, or any other topic outside product master data."
  - Tool usage instruction: "You MUST use tools to retrieve all product data. Never fabricate, guess, or invent product attributes, descriptions, or availability status."
  - Guardrail: "If a user asks about pricing or a topic outside your scope, politely explain that you are scoped to product master data only and suggest they consult the appropriate system."
  - Page size instruction: "When calling tools that support pagination, always set the page size parameter (`top`, `limit`, etc.) to a maximum of 100 to prevent context overflow."
  - Error handling: "If a tool returns an error, report it exactly as received. Do not suggest workarounds unless asked."
  - Read-only declaration: "You must NEVER create, update, or delete any data in S/4HANA."
  - Clarification behaviour: "If a product query is ambiguous (e.g. partial name, multiple matches), ask the user to clarify before calling a tool."
  - Multi-turn context: "Maintain context across conversation turns. If a product was identified in a previous turn, reuse it for follow-up questions without asking the user to repeat it."

### REQ-001 — Natural Language Product Query

- [x] Verify the agent's reasoning loop correctly routes natural language questions to the appropriate MCP tool based on the query type (details / classification / availability)
- [x] Implement clarification logic: if the user provides an ambiguous reference (partial name, no ID), the agent asks a targeted clarifying question before calling any tool
- [x] Verify the agent returns a human-readable, structured answer (not raw JSON) for all successful tool responses

### REQ-002 — Retrieve Product Details

- [x] Wire MCP tool for `API_PRODUCT_SRV` (generated via `mcp-translation-file` skill in MCP Tool Integration section below) to retrieve:
  - Product description (`A_ProductDescription`)
  - Product category / product group (`A_Product`)
  - Base unit of measure (`A_Product`)
- [x] Verify the agent can look up a product by both product ID and by partial product description (using search/filter capabilities of the tool)
- [x] Confirm the response includes at minimum: product ID, description, category, base unit of measure

### REQ-003 — Retrieve Product Classification and Attributes

- [x] Wire MCP tool for `API_CLFN_PRODUCT_SRV` (generated via `mcp-translation-file` skill) to retrieve:
  - Classification class assignment (`A_ClfnProduct`)
  - Characteristic values for the product (`A_ClfnProductClassCharc`)
- [x] Verify the agent formats classification results in readable form (class name + characteristic name/value pairs)
- [x] Confirm graceful handling when a product has no classification data (inform user, do not error)

### REQ-004 — Retrieve Basic Product Availability

- [x] Wire MCP tool for `API_PRODUCT_AVAILY_INFO_BASIC` (generated via `mcp-translation-file` skill) to retrieve availability status for a given product
- [x] Confirm the agent presents availability in plain language (e.g. "Product TG-1050 is available" / "Product TG-1050 is currently unavailable")
- [x] Implement fallback: if the availability API returns no data or an error, the agent informs the user clearly without fabricating an answer

### REQ-005 — Graceful Handling of Out-of-Scope Queries

- [x] Implement out-of-scope detection in the system prompt and verify the agent correctly declines:
  - Pricing questions (e.g. "What is the price of product X?")
  - Write/update requests (e.g. "Update the description of product X")
  - Sales order questions
  - Any non-product-master topic
- [x] Verify that decline responses are friendly, explain the limitation briefly, and do not suggest forbidden workarounds

### REQ-006 — Multi-turn Conversation Support (High-Want)

- [x] Verify the agent retains product context across turns — if the user asked about product TG-1050 in turn 1, follow-up questions ("What is its classification?") in turn 2 should reuse the same product without asking again
- [x] Write an integration test covering a two-turn conversation: (1) ask for product details, (2) follow up on classification

### REQ-007 — Search by Product Description (High-Want)

- [x] Verify that when a user provides a partial product name instead of an ID, the `API_PRODUCT_SRV` tool is called with a filter/search parameter on the description field
- [x] Implement response logic: if multiple products match, list them and ask the user to select one before proceeding

---

## Business Instrumentation

- [x] Implement structured logging and OpenTelemetry spans for all four milestones from the PRD. See [guidelines-agent-python.md](../guidelines-agent-python.md) for the Python-specific pattern (extract business logic from `stream()` into a plain async helper to avoid `GeneratorExit` context errors):

  - **M1 — API Connected**
    - Log on achievement: `M1.achieved: S/4HANA Product Master API connected and returning valid data`
    - Log on miss: `M1.missed: S/4HANA Product Master API connection could not be established`

  - **M2 — Natural Language Resolution**
    - Log on achievement: `M2.achieved: Natural language to product data mapping validated successfully`
    - Log on miss: `M2.missed: Natural language resolution did not meet accuracy threshold`

  - **M3 — Scenario Validation**
    - Log on achievement: `M3.achieved: Agent scenario validation completed — all acceptance criteria met`
    - Log on miss: `M3.missed: Agent scenario validation failed — acceptance criteria not met`

  - **M4 — Live Deployment**
    - Log on achievement: `M4.achieved: Agent deployed and live on SAP Joule — first successful Sales Rep query completed`
    - Log on miss: `M4.missed: Agent deployment to SAP Joule did not complete within target timeline`

- [x] Verify `bootstrap(app)` is called after `app = server.build()` in `main.py`

---

## MCP Tool Integration

> Read [guidelines-agent-mcp.md](../guidelines-agent-mcp.md) for complete MCP integration patterns.
> This asset uses **Path A** — API spec files exist; no pre-built MCP servers available.

- [x] Invoke `mcp-translation-file` skill for each of the three downloaded API spec files:
  - `specification/product-master-agent/api-specs/API_PRODUCT_SRV.edmx` → ORD ID: `sap.s4:apiResource:API_PRODUCT_SRV:v1`
  - `specification/product-master-agent/api-specs/API_CLFN_PRODUCT_SRV.edmx` → ORD ID: `sap.s4:apiResource:API_CLFN_PRODUCT_SRV:v1`
  - `specification/product-master-agent/api-specs/API_PRODUCT_AVAILY_INFO_BASIC.edmx` → ORD ID: `sap.s4:apiResource:API_PRODUCT_AVAILY_INFO_BASIC:v1`
  - Apply scope hints from the **MCP Tool Scope** section above to prune unnecessary endpoints
  - Outputs land in `specification/product-master-agent/mcps/<api-spec-stem>/`

- [x] Invoke `setup-solution` skill to create MCP server assets for each generated translation card
- [x] Read each generated `asset.yaml` and copy the exact `ordId` value into the agent's `asset.yaml` `requires` section — **do NOT invent or guess ORD IDs**:
  ```bash
  grep '^ordId:' assets/<mcp-server-asset-name>/asset.yaml
  ```
- [x] Wire MCP tool loading in `assets/product-master-agent/app/agent.py` using `get_mcp_tools()` from the `mcp_tools` module — never import directly from `sap_cloud_sdk.agentgateway`, never create direct HTTP clients
- [x] Add all three MCP server dependencies to `assets/product-master-agent/asset.yaml` under `requires` using exact ORD IDs from the generated assets
- [x] Generate `mcp-mock.json` using the `mcp-mock-config` skill after all three translation files are complete

---

## Testing

> See [guidelines-agent-python.md](../guidelines-agent-python.md) for Python testing setup and patterns.

- [x] `conftest.py` must only set `IBD_TESTING=true`
- [x] Write unit tests in `assets/product-master-agent/tests/` — one per MCP tool:
  - `test_product_details_tool.py` — mock `API_PRODUCT_SRV` tool, verify correct fields returned
  - `test_product_classification_tool.py` — mock `API_CLFN_PRODUCT_SRV` tool, verify class/characteristic output
  - `test_product_availability_tool.py` — mock `API_PRODUCT_AVAILY_INFO_BASIC` tool, verify availability response
  - Run each test immediately after writing it
- [x] Write one integration test `test_agent_integration.py` covering the end-to-end agent flow:
  - Turn 1: ask for product details by ID → agent calls product details tool → readable response returned
  - Turn 2 (multi-turn): ask follow-up classification question → agent reuses product context → classification tool called
  - Out-of-scope scenario: ask a pricing question → agent declines gracefully without calling any tool
  - Tests must run fully offline (mock LLM responses + mock MCP tool calls)
- [x] Run `pytest` from `assets/product-master-agent/` (no args) — fix failures immediately
- [x] If coverage < 70%, add tests until threshold is met
- [x] Run `pytest` again (no args) to generate final `test_report.json`
- [x] Verify `test_report.json` exists in `assets/product-master-agent/`
