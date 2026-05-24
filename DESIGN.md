# Introduction

This document follows the mental flow that led to the different stages of the implementation. Given the two-day constraint, the goal was to build a working end-to-end baseline first, then iterate: run it on real queries, identify what breaks, store failures in an adversarial dataset, and fix them progressively. A more complete version would include a simulated agent–user conversation loop to build a golden dataset automatically.

## Baseline
When working with systems like this, the ETL pipeline matters more than the agent itself. A well-structured index with the right fields makes everything downstream — retrieval, filtering, ranking — significantly easier. For that reason, three to four hours were spent analyzing the catalog structure and building a solid ETL pipeline before touching the agent.The pipeline loads data into Qdrant, one of the leading vector databases. Simpler alternatives like Chroma or FAISS would have been sufficient at this scale, but Qdrant was chosen for familiarity and because it scales easily to millions of data points without architectural changes.
The agent, described in detail below, is intentionally minimal: it can ask clarifying questions or retrieve from the vector database. Some research on multi-agent recommendation systems informed the architecture; improvements inspired by that literature are discussed in a later section.

### ETL
The ETL pipeline works as follows:
1. Load the data from catalog.json.
2. Fix encoding issues (malformed characters present in the raw data) and strip HTML from all fields loaded into Qdrant.
3. Flatten the L4 product category, which the agent can use as a filter.
4. Extract structured fields from custom_fields: tipologia_prodotto (present on 245 of 300 products, 69 unique values), ingredienti (HTML-stripped), and collezione.
5. Store variants as nested objects within each product. This is important: if a product has many variants, a naive semantic search would surface mostly variants of the same product rather than diverse results.
6. Set boolean fields: is_tester (derived from the product title) and is_niche (derived from the collezione field).
7. Compute has_in_stock_variant: a product is considered available if at least one of its variants is in stock. Some products are marked unavailable at the top level even though their variants are available — those are treated as available.
8. Build an enriched text field for embedding, combining: title, category_l4, product type, description, tester flag (if set, the text notes it is a tester and priced lower), ingredients, collections, and variant names. Including variant names means that a query like "profumo da 30ml" can match products that carry a 30ml variant.

Of course there are other possible improvements. To cite some of them:
- Ingredient parsing: A small LLM could read the raw ingredient strings, clean them, and produce a structured list. This would enable proper exclusion filters. Currently, a query like "non voglio il profumo alla banana" causes the agent to search for "profumo senza banana," but the embedding space places that query close to products containing banana — the opposite of what is wanted. The multi-turn agent can partially compensate by observing that all retrieved results share an unwanted ingredient and retrying, but the first retrieval is still wasted. A regex approach was attempted but proved too brittle to ship.
- Collection field enrichment: Additional structured attributes — genre, brand, occasion — could be extracted from the collezione field.
- Occasion filtering: Some occasion tags in the data appear stale or season-mismatched and could be pruned.

In general, RAG without filters does not scale well. Extracting filterable fields from the start — even imperfect ones — pays off as the catalog grows. Scaling to 100 merchants with 5,000–50,000 products each is not a problem: you add a merchant_id field to each Qdrant point and filter by it at query time. The vector database handles that volume without issues, and keeping merchants isolated is simple — every query includes the merchant_id as a hard filter, so there is no risk of a customer seeing another merchant's products. At much larger scale (hundreds of merchants with hundreds of thousands of products each), a separate Qdrant collection per merchant becomes the better choice, because a shared collection still requires a global index scan before filtering kicks in. For the scale described here, the shared collection is simpler and works well.

### Agent Architecture

The agent architecture is the following:

UI client
   │  POST /chat {thread_id, customer_id?, user_message}
   ▼
FastAPI ──► LangGraph (Postgres checkpointer, keyed by thread_id)
            │
            ▼
        prepare_state         (turn count)
            │
            ▼
        central_agent         (create_agent loop, response_format=CentralAgentOutput)
            │   └── tool: search_catalog (Qdrant; re-callable, bounded by ModelCallLimitMiddleware)
            ▼
        terminal action ∈ {3 nodes that can be Ask, Recommend, Escalate}    ◄── Pydantic discriminated union
            │
            ▼
   reply_text, product_ids, needs_human  →  client

Offline:  catalog.json ──► ETL ──► Qdrant collection (one point per product)

Why this structure:
- Each turn runs a tool loop that terminates in exactly one of {Ask, Recommend, Escalate}, keeping the control flow predictable.
- The central agent owns retrieval and decision-making: it can call search_catalog multiple times, reason over the returned products, re-rank them, and decide which action to take (that's why for this version I didn't add other reranking modules)
- The three terminal nodes handle voice and judgment separately from retrieval logic, keeping each component focused.

Each call to the LLM uses Gemini models with fallback towards Mistral models (or vice versa). This allows the system to be resilient when the main provider is down or not available for global rate limit issues.
If the orchestrator fails to produce a valid structured output, the fallback extracts the last text message from the tool loop and routes it directly to escalate_node.

### Retrieval
Retrieval uses dense single-vector search over the enriched text field, embedded with a multilingual model (gemini-embedding-2). A model specialized in Italian could offer marginally better recall on niche fragrance vocabulary, but API-hosted multilingual models trade some latency and cost control for zero infrastructure overhead.

Hybrid search (dense + sparse/BM25) would improve precision on exact-match queries — brand names like "Chanel," specific product codes, or ingredient names — where semantic similarity alone can miss. It was not implemented in this baseline but is an impactful retrieval improvement for a second iteration.

The search_catalog tool exposes filter parameters so the agent can narrow results by category_l4, is_tester, has_in_stock_variant, and similar fields. This keeps retrieval scalable as the catalog grows and prevents the agent from having to reason over irrelevant results.

#### Reranker and Finetuning

Rerankers become useful when the catalog is large enough that returning 20+ results to the orchestrator creates noise and inflates context size. At that point, a reranker upstream keeps the agent's input clean — instead of reasoning over 20 candidates, it receives the top 5 already filtered.

However, in a previous project I ran an analysis on cross-encoder rerankers such as BGE, measuring Mean Reciprocal Rank (MRR) and Normalized Discounted Cumulative Gain (NDCG) on a labeled dataset where for each query we retrieved the top 10 items and manually scored them from 0 to 2. BGE showed no meaningful improvement over baseline retrieval. This is likely because it was trained on generic datasets and does not capture domain-specific similarity signals — fragrance vocabulary in particular (notes, families, ingredients) is specific enough to hurt generic models. A similar evaluation should be run here before committing to any reranker.

For this reason, the more interesting direction is a small language model fine-tuned specifically for this task. The training data can be bootstrapped using a large LLM as a first-pass reranker: given a query and 100 candidate products, the large model produces an ordered list of 10. That process, repeated across a representative set of queries, generates a labeled dataset cheaply. Before using it for training, MRR and NDCG of the large model's output should be verified to be significantly above the BGE baseline — that's the quality bar the fine-tuned model needs to replicate. A secondary benefit of fine-tuning is structured output reliability: small models struggle with constrained formats out of the box, but respond well to task-specific training, which makes this a natural fit.

### Cost per Query

Rough numbers, current public prices. Single-turn recommend with one search_catalog call:


| Component | Tokens (in / out) | Unit price | Cost |
|---|---|---|---|
| Query embedding (gemini-embedding-2) | ~50 / — | $0.2 / 1M | ~$0.00001 |
| `central_agent` LLM call #1 (sees system + transcript, emits tool call) | ~2,500 / 150 | $0.25 / $1.50 per 1M | ~$0.00085 |
| `central_agent` LLM call #2 (sees tool result, emits `Recommend`) | ~3,200 / 400 | same | ~$0.00140 |
| **Total per recommend turn** | | | **≈ $0.0023** |
| Single `Ask` turn (no tool call) | ~2,500 / 150 | | ≈ $0.00085 |
| ETL one-shot embed of 300 products (cached after) | ~150k / — | $0.20 / 1M | ≈ $0.03 |

At 10,000 turns/month: ~$23/mo on LLM calls, dominated by input tokens.  If retrieval quality requires stronger reasoning, switching the central_agent to Gemini 3 Flash Preview doubles the cost to ~$46/mo — still very cheap at this scale.
