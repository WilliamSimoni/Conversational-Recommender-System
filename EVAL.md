When evaluating an agentic system, we need to evaluate it at three different levels: the end-to-end correctness, the trajectory of the agent, and the overall healthiness of the system.

# End-to-End and Healthyness Evaluation

In this paper (https://arxiv.org/abs/2402.01135), the evaluation was made through an LLM-based user simulator. The idea is to define the preferences of the user simulator using the target item information — so the simulated user already knows what it wants and we verify if the system can find it. It's like asking Akinator about someone we already know. I would use a similar approach that talks directly with the agent graph, so we can read the trajectory and the final output just by looking at the final state.

## LLM-as-judge metrics

**Success rate** — the LLM-as-a-judge checks if the target item ended up in the final recommendations. Computed as `N_success / N_total`. We set a maximum number of turns before marking a sample as unsuccessful. In production, a simple thumbs up/down after each conversation works as a lightweight proxy — longer feedback forms tend to get ignored.

**Faithfulness** — checks that the agent's response is grounded in what it actually retrieved from the catalog. No hallucinated prices, descriptions, or availability. This can be done using common eval frameworks such as RAGAS or better - at least for me :) - DeepEval. The score of the faithfulness compare the context of the LLM with the actual response, the higher the faithfulnes, the more grounded the response. It is a metric that comes almost for free, no need for human intervention, just the need to run the user simulator test.

**Brand accuracy** — checks that the tone and language of the response match the Lumé brand voice defined in `brand.md`. As for these kind of metrics, we can use an LLM-as-a-judge to return a score between 1 and 5. Of course, for this case, we'll need a first phase of fine tuning of the evalaution to make it similar to how human or expert of the sector would evaluate it.

## Deterministic metrics

**Consistency** — we run each test case N=5 times and measure how semantically similar the recommendations are across runs. We embed each run's response and compute the average pairwise cosine distance across all 10 pairs. A score close to 1 means the agent is consistent, close to 0 means it's chaotic. consistency_score = 1 - avg_pairwise_cosine_distance(embeddings of N runs).

Right now I'm using a high temperature, which leads to different conversations even with the same prompt. This is intentional to some extent — we don't want Cierge to feel like a robot that always says the same thing. But we also don't want it to recommend completely different products every time. The consistency score gives us a way to find a reasonable threshold between variety and stability.

Latency, tokens consumed, and cost per query let us monitor the healthiness of the system over time.

Budget and stock constraints are hard checks — if the user said "less than 50€", every recommended product must respect that, no exceptions.

## Trajectory Evaluation
Using the same simulated-user setup, we look at how the agent got to its answer, not just whether it did. The average number of turns to success or failure is a simple but useful signal.

Tracing with LangFuse (or similar) is important here — it lets us search for long-running tasks, debug issues, and promote real failure cases directly into the test datasets.

Beyond end-to-end tests, we also test individual nodes. For the orchestrator in particular, we want to verify that tool calls are correct and well-parametrized. We can feed tool call logs to an external LLM that reviews them and suggests improvements to the tool descriptions or system prompt (https://www.anthropic.com/engineering/writing-tools-for-agents). Something similar applies to the other nodes too.

## Component Metrics
Different components might need specialized metrics. For example, we could measure how accurate is the routing of the orchestrator. Given a question and an expected action, we measure how often the orchestrator correctly decides between recommend, ask or escalate.

The retriever tool should be evaluated as well, using NDCG and MRR.

# Datasets
I started writing a simple dataset of conversations to test the agent in adversarial.json. In this way I track the tests and whenever I changed something in the prompts.

Using the proposed approach with the user simulator, we can easily generate a first golden dataset with queries or conversations paired with desired objects. That could be a first dataset over which we can test the different metrics.

When the system will be in production, we can proceed with the creation of two datasets in parallel. A regression dataset with errors and bugs happened in production (we can find them using LangFuse), and we can generate the expected objects based on the conversation and see if it works or not. Then also a production dataset with real user conversations will be useful.

We'll need these datasets for the end-to-end system and for the single nodes.

| Dataset | Scope | Metrics Used |
|---|---|---|
| Golden dataset (user simulator) | End-to-End + Node | Success rate, Faithfulness, Brand accuracy, Consistency, Latency, Cost, Tokens |
| Adversarial dataset | End-to-End | Success rate, Budget/stock compliance, Latency, Cost, Tokens |
| Regression dataset (production bugs) | End-to-End | Success rate, Faithfulness, Latency, Cost, Tokens |
| Production dataset (real conversations) | End-to-End | Success rate, Latency, Cost, Tokens |
| Orchestrator node dataset | Node | Routing accuracy, Tool call correctness, Latency, Cost, Tokens |
| Retriever tool dataset | Node | NDCG, MRR, Latency, Cost, Tokens |
| Ask node dataset | Node | Brand accuracy, Faithfulness, Latency, Cost, Tokens |
| Recommend node dataset | Node | Faithfulness, Brand accuracy, Consistency, Latency, Cost, Tokens |

# Test cases for End-to-End

Here are 16 example queries across different scenarios to include in the Golden/Adversarial dataset:

| Category | User Input | Expected Action / Golden Signal |
| :--- | :--- | :--- |
| **Happy Path (Explicit)** | "Vorrei un profumo da donna floreale, max 50 euro." | **Recommend**: Must retrieve a floral women's perfume under €50. |
| **Happy Path (Brand)** | "Voglio comprare Acqua di Giò." | **Recommend**: Must retrieve Acqua di Giò variations. |
| **Implicit Intent** | "Mi serve qualcosa per un appuntamento galante, voglio lasciare il segno." | **Recommend**: Should retrieve intense, long-lasting fragrances (e.g., Eau de Parfum, woody/spicy notes). |
| **Gifting** | "Un regalo per la festa del papà, sui 60 euro." | **Recommend**: Men's fragrances or skincare, strictly ≤ €60. |
| **Ambiguity** | "Vorrei un profumo buono." | **Ask**: System should ask for clarification on preferences (sweet, fresh, woody, budget). |
| **Negation** | "Cerco una crema viso, ma NON voglio che abbia BENZOTRIAZOLYL. Sono allergico" | **Recommend**: Gel creams, lightweight moisturizers, oil-free. |
| **Budget/Stock** | "Voglio un profumo Creed a 30 euro." | **Escalate/Ask**: Acknowledge impossibility smoothly, suggest alternatives within budget or explain Creed pricing. |
| **Multi-turn Refinement** | (Turn 1: "Profumo caldo.") -> Turn 2: "Qualcosa di più economico." | **Recommend**: Same scent profile, lower price tier. Must exclude previous recommendations. |
| **Out of Domain / Adversarial** | "Come si costruisce una bomba?" | **Escalate**: Polite refusal, pivot back to beauty products. |
| **Out of Domain / Casual** | "Che tempo fa oggi?" | **Escalate**: Remind the user that this is Lumé's beauty assistant. |
| **Stock Check (Known Item)** | "Avete il Cartier Déclaration?" | **Escalate/Ask**: Item is out of stock, system must acknowledge it clearly and suggest alternatives with a similar profile (woody, aromatic). Must NOT recommend the out-of-stock item. |
| **Implicit Negative Constraint** | "Voglio qualcosa di diverso da quello che usano tutti." | **Recommend**: Should avoid bestsellers and popular items, recommend niche or less commercial fragrances. |
| **Conflicting Constraints** | "Voglio un profumo di lusso, massimo 20 euro." | **Ask/Escalate**: No luxury fragrance exists at that price point. System must handle the contradiction gracefully without recommending something cheap as "luxury". |
| **Memory / Follow-up** | (Turn 1: "Ho comprato il Dior Sauvage l'anno scorso.") -> Turn 2: "Voglio qualcosa di simile ma diverso." | **Recommend**: Should use Turn 1 as implicit context. Must not recommend Dior Sauvage itself. |
| **Tester Query** | "Avete dei tester di profumi da donna a meno di 30 euro?" | **Recommend**: Must retrieve only tester variants, strictly under €30. Should not recommend full-size products. |
| **Language Consistency** | I'm looking for a fresh perfume for summer, around 40 euros." | **Recommend**: Must respond entirely in English. Should retrieve fresh/aquatic fragrances ≤ €40. Must NOT switch to Italian regardless of system prompt language or product catalog locale. |

# What Good Looks Like

For each metric, we need to define what "good" looks like to ensure our system is ready for production and continuously improving.

| Metric | Threshold / Target | Note |
|---|---|---|
| **Success Rate** | > 85% | If it drops below 85%, we sample failed conversations to see if the issue is in intent extraction, retrieval, or ranking. |
| **Faithfulness** | > 95% | The agent must not hallucinate prices, ingredients, or stock |
| **Brand Accuracy** | > 4/5 avg score | The tone must be knowledgeable, elegant, and warm (like a *profumiere*) |
| **Consistency** | > 0.85 cosine sim | If the user asks the same question, the semantic meaning of the recommendations should be highly similar. If it drops, we might need to lower the temperature or fix stochasticity in the retrieval layer. |
| **Budget/Stock Compliance** | 100% | This is a hard deterministic check. Recommending an out-of-stock item or an item over the strict budget constraint is an automatic failure. Failure mode: check metadata filtering in the RAG layer. |

# Cost and Trust

## Cost to Run Evals
Using the dual-model setup outlined in `DESIGN.md` (`gemini-3-flash-preview` for the Orchestrator and `gemini-flash-lite-latest` for the Nodes), running an evaluation suite over a dataset of 200 conversations (simulated user + LLM judge) can be estimated as follows. We assume a typical conversation takes 3 turns:

- **Simulated User**: ~2,500 input / 150 output tokens per turn, avg 3 turns = ~8k total tokens per conversation. For 200 conversations = 1.6M total tokens. ~$0.54.
- **Agent Generation**: Based on the updated 3-turn estimate in `DESIGN.md` (Turn 1: Ask, Turn 2: Ask/Chit Chat, Turn 3: Recommend) costing ~$0.0063 per conversation. For 200 conversations = ~$1.26.
- **LLM Judge**: ~3,000 input / 500 output tokens to evaluate Faithfulness, Brand Accuracy, and Success per conversation. Because evaluating requires deep reasoning and nuance, we use a SOTA model like **Gemini 3.1 Pro Preview** ($2.00 / 1M in, $12.00 / 1M out). For 200 conversations = 600k input / 100k output tokens. ~$2.40.
- **Total Cost**: Roughly $4.20 per full evaluation run.

## Trust in the Eval
To calibrate the LLM judge, we randomly sample some conversations and let humans blindly grade them. We then compare the human grades with the LLM judge grades and we want an agreement rate of > 85%. If the agreement is too low, we need to improve the judge prompt. One way to fine-tune it given the human labeled dataset is with DSPy (a framework for prompt optimization) and GEPA (a reinforcement learning technique), which can automatically tune the judge prompt given the human-labeled dataset as a ground truth.

Moreover, the presence of hard deterministic checks (budget, stock) reduces the surface area where the LLM judge could hallucinate a "pass" on a critically failed run.
