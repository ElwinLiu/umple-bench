# LLM as Judge

LLM-as-a-Judge is an evaluation methodology where a language model is used to assess the quality of outputs produced by another LLM or agent. Instead of relying solely on human reviewers or simple heuristic metrics, you prompt a capable model (the "judge") to score and reason about outputs against defined criteria.

## Why Use LLM as Judge?

- **Scalable**: Judge thousands of outputs quickly vs. human annotators
- **Human-like**: Captures nuance (helpfulness, toxicity, relevance) better than simple metrics
- **Repeatable**: With a fixed rubric, you can rerun the same prompts for consistent results
- **Flexible**: Can evaluate custom properties specific to your use case

## How It Works

The core idea is straightforward:

1. Present an LLM with the **input** (task/prompt)
2. Add the **agent's output** to evaluate
3. Provide a **scoring rubric** defining what "good" looks like
4. The judge model returns a score with chain-of-thought reasoning

## Types of LLM Judges

### Single Output Scoring

Either reference-based or referenceless, evaluates a single output:

```
Prompt: Given a QUESTION and RESPONSE, evaluate if the response is helpful.
Helpful responses are clear, relevant, and actionable.
Return a score from 1-5 with reasoning.
```

### Pairwise Comparison

Takes multiple outputs and chooses a "winner":

```
Prompt: Which response is better for the given task?
Consider accuracy, clarity, and completeness.
Return the winner (A or B) with justification.
```

## Implementing in Harbor

### Basic Verifier Script

Create a verifier that uses LLM judgment:

```bash
#!/bin/bash
# tests/test.sh

OUTPUT_FILE="/logs/agent/output.txt"
JUDGE_PROMPT="Evaluate if the agent completed the task correctly..."

# Use OpenAI/Anthropic API to judge
JUDGE_RESULT=$(curl -s https://api.openai.com/v1/chat/completions \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -d "{
    model: gpt-4,
    messages: [
      {role: system, content: 'You are a judge...'},
      {role: user, content: '$JUDGE_PROMPT\n\nOutput: $(cat $OUTPUT_FILE)'}
    ]
  }" | jq -r '.choices[0].message.content')

# Extract score and write reward
SCORE=$(echo "$JUDGE_RESULT" | jq -r '.score')
echo "$SCORE" > /logs/verifier/reward.txt
```

### Multi-Metric Evaluation

For more detailed evaluation, use reward.json:

```bash
#!/bin/bash

# Evaluate multiple criteria
CORRECTNESS=$(evaluate_correctness)
HELPFULNESS=$(evaluate_helpfulness)
EFFICIENCY=$(evaluate_efficiency)

# Write multi-metric rewards
cat > /logs/verifier/reward.json << EOF
{
  "correctness": $CORRECTNESS,
  "helpfulness": $HELPFULNESS,
  "efficiency": $EFFICIENCY,
  "overall": $(echo "($CORRECTNESS + $HELPFULNESS + $EFFICIENCY) / 3" | bc)
}
EOF
```

## Best Practices

### Prompt Engineering

- **Be specific**: Define clear evaluation criteria
- **Include examples**: Provide few-shot examples when possible
- **Chain-of-thought**: Ask for reasoning before scoring
- **Handle edge cases**: Define what to do with invalid outputs

### Choosing the Judge Model

- Use a capable model (GPT-4, Claude 3 Opus, etc.)
- Ensure the model supports structured output
- Consider cost vs. accuracy tradeoffs

### Avoiding Bias

- **Position swapping**: For pairwise comparisons, swap order to avoid position bias
- **Multiple judges**: Use ensemble of judges for important evaluations
- **Human validation**: Spot-check LLM judgments with human evaluation

## Limitations

- **Subjectivity**: LLM judgments can reflect model biases
- **Cost**: Running LLM judges can be expensive at scale
- **Capability**: Judge model capability affects evaluation quality
- **Context length**: Long outputs may exceed context limits

## Alternative: Heuristic Verifiers

For tasks with clear success criteria, prefer deterministic verifiers:

```bash
#!/bin/bash
# Simple deterministic check
if [ -f "/app/output.txt" ] && grep -q "success" "/app/output.txt"; then
    echo "1" > /logs/verifier/reward.txt
else
    echo "0" > /logs/verifier/reward.txt
fi
```

Use LLM judges for:
- Open-ended tasks
- Subjective quality assessment
- Complex reasoning evaluation
