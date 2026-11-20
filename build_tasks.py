#!/usr/bin/env python3
"""Builds tasks3.jsonl: 25 tasks with an explicit easy/hard split.

Tags: C=closed O=open E=easy(dispositive) H=hard(underdetermined)
      D=document-excerpt R=research W=benefits-from-web M=misleading-signal
Option labels kept to <=30 chars so models can return them verbatim.
"""
import json

T = []


def add(tid, use_case, prompt, options, tags):
    T.append({"task_id": tid, "use_case": use_case, "prompt": prompt.strip(),
              "options": options, "tags": tags})


# ============================ ARCHITECTURE: EASY (3) ==========================

add("arch-e1", "architecture", """
A team must classify 8M support tickets per month into 12 categories. Latency is
irrelevant, 400,000 historically labeled tickets are available, and the accuracy
requirement is 94%. Cost per month must stay under $2,000. Choose the best
primary approach.
""", ["frontier-model-api", "finetuned-small-model", "embedding-classifier",
      "prompted-open-model-batch", "rules-plus-llm-fallback"], ["C", "E"])

add("arch-e2", "architecture", """
A legal team processes 20M document pages once per quarter. A run may take up to
48 hours, data must remain inside a private VPC, workloads can be queued, and the
team has two platform engineers with no ML operations experience. Choose the best
architecture.
""", ["private-managed-batch", "self-hosted-k8s-batch", "private-realtime-endpoint",
      "temporary-gpu-cluster", "on-premises-cluster"], ["C", "E"])

add("arch-e3", "architecture", """
A coding assistant sends prompts containing a shared 60,000-token repository
prefix followed by a short user-specific request. Traffic is steady, 80% of
requests hit the same repository revision within a five-minute window, output
length averages 200 tokens, and time to first token is the sole performance
complaint. Choose the highest-impact primary optimization.
""", ["prefix-caching", "prompt-compression", "smaller-long-context-model",
      "speculative-decoding", "repository-rag"], ["C", "E"])

# ============================ ARCHITECTURE: HARD (5) ==========================

add("arch-h1", "architecture", """
A 14-person team serves a 70B model. Peak traffic is 40 req/s for roughly 6 hours
a day and near zero for the other 18. Arrival of the daily peak is not
predictable in advance and shifts by up to 3 hours. p95 latency must stay under
2 seconds; the infrastructure budget is $9,000 per month. Measured on this
provider: fixed dedicated capacity sufficient for peak costs $8,400 per month;
autoscaled dedicated averages $5,100 per month but takes 90 seconds to add a
replica; serverless cold start for this model size is 45 seconds. Choose the best
deployment strategy.
""", ["fixed-dedicated", "autoscaled-dedicated", "serverless",
      "scheduled-dedicated", "hybrid-baseline-plus-burst"], ["C", "H"])

add("arch-h2", "architecture", """
A customer-facing chatbot on a 13B model receives unpredictable bursts between 5
and 120 req/s. Bursts last 10 to 20 minutes and begin without warning. p95
latency must remain under 1.5 seconds. Serverless with provisioned capacity
carries a 30% price premium over on-demand serverless and eliminates cold starts.
Autoscaled dedicated adds replicas in about 3 minutes, which is longer than the
burst onset but shorter than the burst. Idle GPU spend is the team's stated top
concern; a director has separately said latency breaches are unacceptable.
Choose the best deployment strategy.
""", ["fixed-dedicated", "on-demand-serverless", "autoscaled-dedicated",
      "provisioned-serverless", "dedicated-plus-serverless-overflow"], ["C", "H"])

add("arch-h3", "architecture", """
A translation API has steady traffic of about 75 req/s. The model needs four
GPUs, p95 must stay under 800ms, and demand varies by less than 10%. The provider
offers dedicated capacity at list price monthly, or a 40% discount on a 12-month
commitment. The company has 9 months of funding runway and is in the middle of a
fundraise. A multi-tenant dedicated endpoint is 25% cheaper than monthly list but
carries no latency SLA. Choose the best deployment strategy.
""", ["monthly-dedicated-list-price", "committed-12-month-dedicated",
      "multi-tenant-dedicated", "autoscaled-dedicated",
      "serverless-with-min-replicas"], ["C", "H"])

add("arch-h4", "architecture", """
A mobile app must summarize private notes with no network access. Notes cannot
leave the device. Target devices have 8 GB unified memory, of which the app may
use at most 3 GB. Summaries may take up to 10 seconds. The smallest acceptable
quantized generative model measures 4.2 GB. A platform-native on-device model API
exists but is present on only 60% of the target install base. An extractive
summarizer plus a 600 MB generator fits comfortably but scored measurably lower
in internal quality review. Choose the best implementation strategy.
""", ["on-device-quantized-model", "extractive-plus-small-generator",
      "platform-native-model-api", "native-api-with-fallback",
      "defer-feature-pending-hardware"], ["C", "H"])

add("arch-h5", "architecture", """
A team is choosing between two inference providers for a latency-sensitive agent
product. Provider A: TTFT p50 180ms, p99 620ms; throughput 42 tokens/s per
stream; $0.55 per million input tokens; no prefix caching. Provider B: TTFT p50
310ms, p99 480ms; throughput 61 tokens/s per stream; $0.90 per million input
tokens; prefix caching that the team estimates would apply to 55% of their input
volume. The workload is 6-turn agent conversations with a large shared system
prompt. No independent benchmark covers this workload. Choose the better
provider on the evidence given.
""", ["provider-a", "provider-b", "either-difference-immaterial",
      "insufficient-evidence-to-choose", "split-traffic-and-measure"], ["C", "H", "M"])

# ============================== POLICY: EASY (2) ==============================

add("policy-e1", "policy", """
Read the retention clauses and choose the date by which deletion from active
systems must ordinarily be completed. Excerpt: 'Upon termination, Customer may
retrieve Customer Content for 30 days. Provider will delete Customer Content from
active systems within 45 days after the retrieval period ends. Residual copies in
encrypted backups will expire in the ordinary course within 90 additional days.'
The agreement terminates on March 1 and the customer does not request earlier
deletion.
""", ["March-31", "April-15", "May-15", "June-29", "August-13"], ["C", "E", "D"])

add("policy-e2", "policy", """
Read the two clauses and choose the architecture that most clearly satisfies
both. Clause A: 'Restricted Data may be processed only in the United States and
may not be stored in request logs.' Clause B: 'Zero-retention mode disables
storage of prompts and outputs after the response is returned, but operational
metadata may be retained for 30 days. Zero-retention mode is available only on
regional dedicated endpoints.'
""", ["us-dedicated-zero-retention", "global-serverless-no-logging",
      "us-serverless-7-day-retention", "us-dedicated-with-debug-logs",
      "eu-dedicated-zero-retention"], ["C", "E", "D"])

# ============================== POLICY: HARD (3) ==============================

add("policy-h1", "policy", """
Read both clauses and choose the most supportable conclusion. Clause 4.2: 'To
detect and prevent abuse, Provider retains prompt and output content for 30 days.
This retention applies to all Services.' Clause 9.1: 'Where Customer enables
Zero-Retention Mode, Provider does not store prompt or output content after the
response is returned.' The agreement contains no order-of-precedence provision
and does not cross-reference either clause. The customer has enabled
Zero-Retention Mode and asks whether abuse-monitoring copies still exist.
""", ["no-content-retained", "30-day-abuse-copies-persist",
      "retention-only-on-flagged-content", "clauses-conflict-unresolvable",
      "depends-on-undefined-abuse-scope"], ["C", "H", "D"])

add("policy-h2", "policy", """
Read the licence excerpt and choose the most supportable conclusion. Excerpt:
'You may not make the Model, modified versions, weights, or substantially
equivalent functionality available to third parties as a hosted or managed
service.' 'Substantially equivalent functionality' is not defined anywhere in the
licence. Scenario: the licensee generates 2 million synthetic training examples
using the Model, trains a separate 3B model on those outputs, and offers that 3B
model as a paid hosted API. The distilled model scores 71% of the original's
benchmark performance.
""", ["clearly-prohibited", "clearly-permitted", "prohibited-only-above-parity",
      "turns-on-undefined-term", "permitted-but-outputs-restricted"],
    ["C", "H", "D"])

add("policy-h3", "policy", """
Read the excerpt and choose the most supportable classification. Excerpt:
'Customer determines the purposes and essential means of processing Customer
Content. Provider processes Customer Content only on Customer's documented
instructions. Provider may independently process service telemetry to secure,
maintain and improve the Service, provided telemetry is aggregated or
de-identified before use for product analytics.' The excerpt does not define
aggregation thresholds or de-identification standards. Scenario: the provider
stores prompts to deliver inference, and separately analyzes per-request prompt
length, token counts, error codes and latency, retained per request with a
customer identifier attached.
""", ["provider-processor-throughout", "provider-controller-for-telemetry",
      "joint-controllers-throughout", "telemetry-outside-excerpt-scope",
      "turns-on-deidentification-standard"], ["C", "H", "D"])

# ============================= INCIDENT: EASY (2) =============================

add("inc-e1", "incident", """
Identify the strongest primary suspect. Timeline: 09:40 a document index refresh
completes. 09:44 answer accuracy drops from 88% to 63% while generation latency
and token counts remain stable. Manual tests produce correct answers when
known-good passages are inserted directly into the prompt. Retrieval logs show
similar query volume, but median top-result similarity falls from 0.81 to 0.58.
The embedding model version did not change; the index was rebuilt with a
different distance metric.
""", ["vector-index-config", "embedding-service", "model-serving-runtime",
      "prompt-template-service", "permission-filter"], ["C", "E"])

add("inc-e2", "incident", """
Identify the most likely origin of cross-customer retrieval. Timeline: 13:00 a
caching layer is enabled for retrieval results. 13:18 the first report arrives
that a response cited another customer's document. 13:22 permission-filter logs
show the correct tenant ID entering the retrieval service. 13:25 direct uncached
retrieval tests return only authorized documents. 13:28 cache-hit responses
reproduce the leak, and the cache key contains normalized query text and
embedding-model version but not tenant ID.
""", ["cache-key-design", "permission-filter", "embedding-model",
      "model-decoder", "ingestion-pipeline"], ["C", "E"])

# ============================= INCIDENT: HARD (4) =============================

add("inc-h1", "incident", """
Identify the most likely originating change. Timeline: 14:01 a router
configuration push changes the maximum batch-size hint sent to model replicas.
14:02 a new inference runtime is deployed to 10% of model replicas. 14:05 p95
latency rises from 900ms to 2.8s for approximately 11% of requests. 14:09
affected requests show a threefold increase in decode time. 14:12 traffic is
evenly distributed. The 11% of affected requests are not confined to the canary
replicas, and the router change applied fleet-wide.
""", ["canary-runtime", "router-batch-config", "both-changes-interacting",
      "gpu-capacity-autoscaler", "cannot-isolate-from-evidence"], ["C", "H", "M"])

add("inc-h2", "incident", """
Identify the most likely origin of the outage. Timeline: 15:58 a client SDK
release enables retry-on-timeout with a 2-second timeout and three attempts.
16:00 traffic recorded at the router rises from 25 to 55 req/s. 16:04 request
queues grow on every model replica while GPU utilization stays near 62%. 16:06
router CPU reaches 96% and connection-establishment time increases. 16:08 model
decode time is normal for requests that reach a replica. 16:10 adding model
replicas does not reduce p95. Upstream user-session counts are unchanged from the
previous day.
""", ["router-capacity", "client-retry-amplification", "model-serving-capacity",
      "retrieval-database", "organic-traffic-growth"], ["C", "H", "M"])

add("inc-h3", "incident", """
Identify the most likely originating change. Timeline: 11:14 a tool-service
configuration change reduces the client-side call timeout from 30s to 5s. 11:15 a
prompt-template revision is released that reorders the tool-result block. 11:20
average tool calls per request rise from 1.3 to 4.9. 11:22 the same search query
appears repeatedly within individual traces. 11:25 tool-service p50 latency is
1.2s and p99 is 7.4s. 11:28 the model frequently emits a tool call after
receiving a valid tool result. No tool schema or model version changed.
""", ["prompt-template-revision", "tool-timeout-config", "both-changes-interacting",
      "tool-service-capacity", "cannot-isolate-from-evidence"], ["C", "H", "M"])

add("inc-h4", "incident", """
Identify the most likely cause of the quality regression. Timeline: over one
weekend two changes ship. Change 1: retrieval chunk size increases from 400 to
1,200 tokens with overlap unchanged. Change 2: the serving model auto-upgrades to
a new minor version. Monday: citation precision falls from 0.79 to 0.61, answers
grow 40% longer, retrieved-chunk relevance scored by a held-out rater is
unchanged, and refusal rate is flat. Rolling back either change individually is
not possible this week; the team must pick one to investigate first.
""", ["retrieval-chunk-size", "model-minor-upgrade", "both-changes-interacting",
      "rater-methodology-drift", "cannot-isolate-from-evidence"], ["C", "H", "M"])

# ============================== RESEARCH: OPEN (6) ============================

RESEARCH = [
    ("research-01", """
Compare the current enterprise offerings of three major hosted LLM providers for
a US company processing regulated healthcare data. Evaluate contractual data
retention, model-training policies, HIPAA support, private networking, regional
availability, audit certifications, rate limits and pricing. Use current primary
sources, identify material gaps or ambiguous claims, and recommend the best fit
for a mid-sized company processing about 20M tokens per day.
""", ["O", "R", "W"]),
    ("research-02", """
Investigate whether small language models have become meaningfully competitive
with frontier models for production customer-support classification and routing.
Use recent benchmarks, model documentation, independent evaluations and
deployment evidence. Distinguish benchmark gains from operational advantages,
compare accuracy, latency, throughput and cost, and state where the evidence
remains inconclusive.
""", ["O", "R", "W", "E"]),
    ("research-03", """
Assess the current evidence for and against retrieval-augmented generation as a
replacement for fine-tuning in enterprise knowledge assistants. Compare factual
accuracy, freshness, citation quality, maintenance burden, access control,
latency and total cost. Explain where the approaches are complementary rather
than interchangeable, and give decision criteria for choosing RAG, fine-tuning or
a hybrid.
""", ["O", "R", "W", "E"]),
    ("research-04", """
Determine which publicly available evaluations are most useful for comparing LLMs
used in production software engineering. Review recent benchmark results,
benchmark-design critiques, contamination concerns, agent scaffolding differences
and evidence from real-world coding tasks. Explain which metrics are
decision-useful, which can mislead, and propose a balanced evaluation framework
for selecting a model for an internal coding assistant.
""", ["O", "R", "W", "E"]),
    ("research-05", """
Research the environmental impact of serving large language models in production,
focusing on inference rather than training. Compare recent estimates of
electricity use, water use, hardware utilization and emissions across fixed
dedicated GPUs, autoscaled endpoints, serverless inference and external APIs.
Reconcile conflicting estimates, identify the assumptions driving the differences,
and recommend practical measurement and reduction strategies.
""", ["O", "R", "W"]),
    ("research-06", """
Analyze the current legal and policy landscape governing use of copyrighted
material in generative-AI training and retrieval systems in the United States and
European Union. Use statutes, regulatory guidance, major court developments,
provider policies and commentary representing multiple perspectives. Separate
settled requirements from unresolved questions, compare implications for model
developers and enterprise users, and outline a conservative compliance approach
without presenting it as legal advice.
""", ["O", "R", "W"]),
]
for tid, prompt, tags in RESEARCH:
    T.append({"task_id": tid, "use_case": "research",
              "prompt": prompt.strip(), "tags": tags})

with open("tasks3.jsonl", "w") as f:
    for t in T:
        f.write(json.dumps(t) + "\n")

from collections import Counter
print(f"{len(T)} tasks")
print("use_case:", dict(Counter(t["use_case"] for t in T)))
print("tier:", dict(Counter("E" if "E" in t["tags"] else "H" if "H" in t["tags"]
                            else "open" for t in T)))
print("max option label:", max((len(o) for t in T for o in t.get("options") or []),
                               default=0), "chars")
