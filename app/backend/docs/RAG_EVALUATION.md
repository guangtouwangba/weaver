# RAG Evaluation with Ragas

## Overview

This system automatically evaluates RAG (Retrieval-Augmented Generation) quality using [Ragas](https://docs.ragas.io/) metrics after each user query.

## Features

- **Real-time Auto-Evaluation**: Automatically evaluates answer quality after each query
- **Sampling Control**: Configure evaluation sample rate to control costs
- **Multiple Metrics**: Tracks faithfulness, answer relevancy, context precision, and more
- **Database Logging**: Stores evaluation results in PostgreSQL
- **Loki Integration**: Sends metrics to Loki for Grafana visualization
- **Async Processing**: Evaluation runs in background, doesn't block user responses

## Metrics

### Faithfulness
- **Range**: 0.0 - 1.0 (higher is better)
- **Meaning**: Measures if the answer is grounded in the retrieved contexts
- **Use Case**: Detect hallucinations

### Answer Relevancy
- **Range**: 0.0 - 1.0 (higher is better)
- **Meaning**: Measures if the answer directly addresses the question
- **Use Case**: Ensure answers are on-topic

### Context Precision
- **Range**: 0.0 - 1.0 (higher is better)
- **Meaning**: Measures the precision of retrieved contexts
- **Use Case**: Evaluate retrieval quality

### Context Recall (Optional)
- **Range**: 0.0 - 1.0 (higher is better)
- **Meaning**: Measures what portion of ground truth is covered by contexts
- **Requirement**: Requires ground_truth answer (offline evaluation only)

## Configuration

### Environment Variables

```bash
# Enable real-time evaluation
EVALUATION_ENABLED=true

# Sample rate: 0.1 = evaluate 10% of queries (recommended)
# 1.0 = evaluate all queries (expensive)
# 0.0 = no evaluation
EVALUATION_SAMPLE_RATE=0.1
```

### Cost Considerations

- Each evaluation makes **additional LLM calls** (for scoring)
- Recommended: Start with `EVALUATION_SAMPLE_RATE=0.1` (10%)
- Production: Use sampling to balance cost vs. insight
- Use cheaper LLM models for evaluation (gpt-4o-mini) if possible

## Usage

### Real-time Evaluation (Automatic)

Once enabled, evaluation happens automatically:

```python
# User makes a query
POST /api/v1/chat/stream
{
  "message": "What is a Transformer?",
  "project_id": "uuid"
}

# Backend:
# 1. Processes query with RAG
# 2. Returns answer to user
# 3. Triggers evaluation in background (if sampled)
# 4. Logs metrics to database and Loki
```

### View Evaluation Results

#### Database Query

```sql
SELECT 
    question,
    metrics->>'faithfulness' as faithfulness,
    metrics->>'answer_relevancy' as answer_relevancy,
    metrics->>'context_precision' as context_precision,
    chunking_strategy,
    retrieval_mode,
    created_at
FROM evaluation_logs
WHERE project_id = 'your-project-id'
ORDER BY created_at DESC
LIMIT 10;
```

#### Python API

```python
from research_agent.infrastructure.evaluation.evaluation_logger import EvaluationLogger

logger = EvaluationLogger(session)

# Get metrics summary for a project
summary = await logger.get_metrics_summary(
    project_id=project_id,
    evaluation_type="realtime",
    limit=100
)

# Returns:
# {
#   "total_evaluations": 100,
#   "avg_faithfulness": 0.92,
#   "avg_answer_relevancy": 0.85,
#   "avg_context_precision": 0.88,
#   ...
# }
```

## Grafana Dashboard

### Loki Query Examples

**Average Faithfulness (Last 24h)**
```logql
avg_over_time(
  {service="rag-evaluation"}
  | json
  | unwrap metrics_faithfulness
  [24h]
)
```

**Evaluation Count by Chunking Strategy**
```logql
sum by (chunking_strategy) (
  count_over_time({service="rag-evaluation"}[24h])
)
```

**Low Faithfulness Alerts (< 0.8)**
```logql
{service="rag-evaluation"}
| json
| unwrap metrics_faithfulness
| metrics_faithfulness < 0.8
```

## Offline Batch Evaluation

For comparing different chunking strategies:

```python
from research_agent.infrastructure.evaluation.ragas_service import RagasEvaluationService

# Initialize
ragas_service = RagasEvaluationService(llm=llm, embeddings=embeddings)

# Evaluate batch
results = await ragas_service.evaluate_batch(
    questions=["Q1", "Q2", "Q3"],
    answers=["A1", "A2", "A3"],
    contexts_list=[["C1"], ["C2"], ["C3"]],
    ground_truths=["GT1", "GT2", "GT3"]  # Optional
)

# Results:
# {
#   "faithfulness": 0.93,
#   "answer_relevancy": 0.87,
#   "context_precision": 0.90
# }
```

## Troubleshooting

### Evaluation Not Running

1. Check if enabled:
   ```bash
   grep EVALUATION_ENABLED .env
   ```

2. Check sample rate (must be > 0):
   ```bash
   grep EVALUATION_SAMPLE_RATE .env
   ```

3. Check logs for evaluation:
   ```bash
   # Look for [Auto-Eval] logs
   tail -f logs/app.log | grep "Auto-Eval"
   ```

### Low Metrics Scores

- **Low Faithfulness** (< 0.8): Check for hallucinations, improve retrieval
- **Low Answer Relevancy** (< 0.7): Tune LLM prompt, improve question understanding
- **Low Context Precision** (< 0.8): Improve chunking strategy, use hybrid search

### High Costs

- Reduce `EVALUATION_SAMPLE_RATE` (e.g., from 1.0 to 0.1)
- Use cheaper LLM for evaluation (currently uses same model as RAG)
- Disable evaluation in development: `EVALUATION_ENABLED=false`

## Migration

Run the migration to create the `evaluation_logs` table:

```bash
cd app/backend
alembic upgrade head
```

## Example: Analyzing Strategy Performance

```python
# Query evaluations by strategy
strategies = ["recursive_1000", "markdown", "semantic"]

for strategy in strategies:
    results = await session.execute(
        select(EvaluationLogModel)
        .where(EvaluationLogModel.chunking_strategy == strategy)
        .limit(100)
    )
    
    evals = results.scalars().all()
    avg_faithfulness = sum(e.metrics["faithfulness"] for e in evals) / len(evals)
    
    print(f"{strategy}: Avg Faithfulness = {avg_faithfulness:.2f}")
```

## References

- Ragas Documentation: https://docs.ragas.io/
- Ragas Metrics: https://docs.ragas.io/en/latest/concepts/metrics/index.html
- Paper: https://arxiv.org/abs/2309.15217

