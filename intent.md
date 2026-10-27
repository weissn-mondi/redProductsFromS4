# Product Master Data Q&A Agent for Sales Representatives

AI agent enabling Sales Representatives to ask natural language questions about product master data from SAP S/4HANA Public Cloud Edition and receive instant, accurate answers.

## Business challenge

Sales Representatives must log into SAP S/4HANA and navigate complex screens just to look up basic product information (descriptions, categories, units of measure). This friction costs approximately 5 minutes per lookup, slowing down customer conversations and increasing dependency on back-office navigation.

## Business Goals & Success Criteria

| Metric | Baseline | Target | Timeline | Process / Capability | Source |
|--------|----------|--------|----------|----------------------|--------|
| Time to retrieve product information | 5 minutes per lookup | Under 30 seconds | Within 1 month | Product master data lookup | user |

## Key Milestones

1. **API Connected** — Product Master OData API (S/4HANA Public Cloud) is callable by the agent with valid authentication.
2. **Natural Language Resolution** — Agent correctly interprets natural language questions and maps them to the right product data fields.
3. **Scenario Validation** — Agent validated against a representative set of real Sales Rep question scenarios with accurate responses.
4. **Live Deployment** — Agent is deployed and accessible to Sales Representatives via the SAP Joule chat interface.

## Business Architecture (RBA)

### End-to-End Process

Lead to Cash Standard B2B

### Process Hierarchy

```
Lead to Cash Standard B2B (E2E)
└── Plan to Optimize Marketing and Sales (Phase)
    └── Plan prices and promotions (Sub-Process, BPS-359_002)
        └── Plan and define sales prices (Business Activity)
```

### Summary

Sales Representatives querying product master data maps to the Lead to Cash Standard B2B E2E process, specifically the "Plan prices and promotions" sub-process where accurate product information and pricing definitions are foundational to enabling effective sales conversations.

## Fit Gap Analysis

| Requirement (business) | Standard asset(s) found | API ORD ID | MCP Server ORD ID | MCP Server Version | Webhook API ORD ID | Data Product ORD ID | Gap? | Notes / assumptions |
|------------------------|------------------------|------------|-------------------|--------------------|--------------------|---------------------|------|---------------------|
| Retrieve basic product details (description, category, UoM) | SAP S/4HANA Cloud Public Edition – Sales Price Planning and Definition (SC1044) | `sap.s4:apiResource:API_PRODUCT_SRV:v1` | — | — | — | — | No | No pre-built MCP server; custom MCP tooling will wrap this OData API |
| Retrieve product classification and attributes | SAP S/4HANA Cloud Public Edition | `sap.s4:apiResource:API_CLFN_PRODUCT_SRV:v1` | — | — | — | — | No | Covers product master data including classification |
| Product availability information | SAP S/4HANA Cloud Public Edition | `sap.s4:apiResource:API_PRODUCT_AVAILY_INFO_BASIC:v1` | — | — | — | — | Maybe | Basic availability info; extended availability API not in landscape |
| Pricing information | — | — | — | — | — | — | Yes | Pricing Service and Manage Sales Price Specifications APIs not available in this landscape; excluded from scope |
| Natural language query interface for Sales Reps | — | — | — | — | — | — | Yes | No standard SAP product covers NL querying; custom AI agent required |

### Key findings

- SAP S/4HANA Cloud Public Edition is confirmed in the landscape with relevant Product Master OData APIs available.
- No pre-built MCP servers exist for these APIs; custom MCP tool wrappers must be built from the OData specs.
- Pricing APIs (Pricing Service, Manage Sales Price Specifications) are unavailable in the landscape and are excluded from scope.
- The Product Master (A2X) API and Product Master Data Including Classification API together cover the core data need: product descriptions, categories, units of measure, and classifications.
- A custom Python A2A agent is the right fit — it provides the NL query capability not covered by any standard SAP product.

## Recommendations

### AI Agent for Product Master Data Q&A

#### Executive Summary

Python A2A agent with S/4HANA OData MCP tools surfaced via SAP Joule.

#### Recommended Solution

Build a Python-based AI agent (A2A protocol) that wraps the SAP S/4HANA Cloud Public Edition Product Master OData APIs as MCP tools. Sales Representatives interact with the agent in natural language through the SAP Joule chat interface. The agent interprets questions, calls the appropriate S/4HANA API, and returns structured, human-readable answers — eliminating the need to navigate S/4HANA screens directly.

#### Problem Statement

Sales Representatives lose approximately 5 minutes per product lookup navigating SAP S/4HANA screens, disrupting customer conversations and reducing sales efficiency.

#### Affected User Roles

- Sales Representatives

#### Important factors

##### Reduces manual effort through conversational access

Sales Reps can ask plain-language questions ("What is the unit of measure for product X?") and get immediate answers without needing S/4HANA navigation skills.

##### Leverages existing S/4HANA investment

The agent reads data directly from the authoritative source — no data duplication or synchronisation overhead.

##### Fast time-to-value

Using available OData APIs and the standard Python agent framework, the solution can be built and deployed within the 1-month target.

#### Potential risks

##### API authentication and authorisation

The agent must be configured with appropriate S/4HANA service credentials scoped to read-only product data access.

##### Query accuracy

Natural language interpretation may occasionally mismatch product queries — query validation and fallback messaging should be included.

#### Recommended solution category

AI Agent

#### Intent fit
92%
