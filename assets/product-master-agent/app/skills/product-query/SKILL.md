---
name: product-query
description: Step-by-step instructions for answering Sales Representative product master data questions using SAP S/4HANA OData tools.
allowed-tools:
  - get_product_details
  - get_product_classification
  - get_product_availability
---

# Product Query Skill

Follow these steps to answer a Sales Representative's product master data question.

## Step 1: Identify the product reference

- If the user provides a **product ID** (alphanumeric, typically short, e.g. TG-1050, ABC-200), use it directly as the filter key in tool calls.
- If the user provides a **partial product name or description**, use a search/filter on the product description field to find matching products.
- If neither is provided, ask the user: "Could you provide the product ID or name you are looking for?"

## Step 2: Determine the query type

Based on the user's question, identify what data is needed:

| User asks about...                                  | Tool to call                    |
|-----------------------------------------------------|---------------------------------|
| Description, category, unit of measure, base data   | `get_product_details` tool      |
| Classification, product group, characteristics      | `get_product_classification` tool |
| Availability, stock status                          | `get_product_availability` tool |
| Multiple of the above                               | Call tools in the order listed  |

## Step 3: Call the appropriate tool

- Set page size (`$top`) to a maximum of 100.
- If the tool returns multiple results (search scenario), present the list to the user and ask them to select one before proceeding.
- If the tool returns no results, inform the user: "I could not find a product matching '[reference]' in the system."
- If the tool returns an error, relay the error message exactly as received.

## Step 4: Format the response

Present the data in plain, readable language. Do not return raw JSON.

**Product details example:**
> Product **TG-1050** — Industrial Pressure Gauge
> - Category: Measurement Equipment
> - Base Unit of Measure: EA (Each)

**Classification example:**
> Product **TG-1050** classification:
> - Class: PRESSURE_INSTRUMENTS
> - Pressure Range: 0–100 bar
> - Material: Stainless Steel

**Availability example:**
> Product **TG-1050** is currently **available** / **unavailable** in the system.

## Step 5: Handle follow-up questions

- If the user asks a follow-up about the same product (e.g. "What is its classification?"), reuse the product ID from the previous turn without asking again.
- If the context is ambiguous, confirm: "Are you asking about product TG-1050 from your previous question?"

## Out-of-scope handling

If the user asks about pricing, sales orders, inventory reservations, or anything outside product master data:
> "I'm focused on product master data — descriptions, categories, classifications, and availability. For pricing information, please consult your SAP Sales Cloud or ask your sales operations team."
