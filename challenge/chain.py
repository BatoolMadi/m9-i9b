"""GraphCypherQAChain-style helper for the live-LLM Tier 3 path.

Triple-stated Tier 3 scoring methodology (verbatim in
integration-task-spec.md, the published Integration Guide Tier 3
section, and this docstring):

- The 15 canonical eval questions in data/eval_questions.jsonl are scored by
  exact-result-set equivalence against the deterministic mapper's output on
  the same fixture graph (the deterministic mapper is the gold).
- A Tier 3 answer is correct iff the executed Cypher returns exactly the
  same set of result rows as the deterministic mapper for that question;
  row order matters only for the two ranked questions (#9, #12) where
  ORDER BY is in the canonical shape.
- A Tier 3 answer that raises UnsupportedCypherError (allowlist rejection)
  counts as incorrect for that question but is REPORTED SEPARATELY in the autograder summary so learners can distinguish "LLM emitted unsafe Cypher"
  from "LLM emitted safe-but-wrong Cypher".
- Aggregation: report per-question correctness plus an overall accuracy
  (correct / 15). No partial credit on rows.
"""



from __future__ import annotations

import ast
from typing import Any

from challenge import llm_client

from .allowlist import UnsupportedCypherError, validate_query_shape
from .few_shots import EXAMPLE_PAIRS, SCHEMA_PREAMBLE


# Graceful import — langchain_neo4j is optional (not installed in CI).
# When unavailable, set the symbol to None and let callers decide whether
# to skip with a clear reason or use a fake.
try:
    from langchain_neo4j import GraphCypherQAChain  # type: ignore
    LANGCHAIN_AVAILABLE = True
except ImportError:
    GraphCypherQAChain = None  # type: ignore
    LANGCHAIN_AVAILABLE = False


def build_prompt(question: str) -> str:
    """Compose the LLM prompt: schema preamble + few-shots + question.

    Course-helper stub. The exact prompt format is up to you, but at
    minimum:
      - Start with SCHEMA_PREAMBLE.
      - Append each EXAMPLE_PAIRS entry as "Q: ...\\nCypher: ...".
      - End with "Q: {question}\\nCypher:" so the LLM continues with Cypher.
    """
    # TODO: assemble the prompt string from SCHEMA_PREAMBLE + EXAMPLE_PAIRS + question.
    
    prompt = SCHEMA_PREAMBLE + "\n\n"

    for example in EXAMPLE_PAIRS:
        prompt += f"Q: {example['q']}\n"
        prompt += f"Cypher: {example['cypher']}\n"
        prompt += f"Params: {example['params']}\n\n"

    prompt += f"Q: {question}\nCypher:"
    return prompt


def run_chain(driver, llm_client, question: str) -> dict[str, Any]:
    """Run one question through the chain end-to-end.

    Returns a dict with keys:
      - "question": the input question
      - "cypher":   the LLM-emitted Cypher string (or None if the LLM
                    refused / returned empty)
      - "params":   the params dict the LLM emitted (or {} if none)
      - "rows":     list of result rows from session.run (or [] if
                    the allowlist rejected the Cypher)
      - "rejected": True iff the allowlist raised; False otherwise
      - "rejection_reason": the UnsupportedCypherError message, or None

    Required behaviour:
      1. Build the prompt via build_prompt(question).
      2. Invoke the LLM (llm_client.invoke(prompt) — LangChain Runnable
         convention).
      3. Parse the LLM response to extract a Cypher string and a params
         dict. (The few-shot format is "Cypher: ...\\nParams: {...}".)
      4. Call validate_query_shape(cypher). Catch UnsupportedCypherError
         and return a dict with rejected=True.
      5. If validation passed, run the Cypher via session.run(cypher,
         **params) and return the rows.
    """
    # TODO: orchestrate prompt → LLM → parse → allowlist → execute.
    
    prompt = build_prompt(question)
    response = llm_client.invoke(prompt)
    text = str(response)

    cypher = ""
    params = {}

    if "Cypher:" in text:
        cypher_part = text.split("Cypher:", 1)[1]

        if "Params:" in cypher_part:
            cypher_text, params_text = cypher_part.split("Params:", 1)
            cypher = cypher_text.strip()

            try:
                params = ast.literal_eval(params_text.strip())
            except Exception:
                params = {}
        else:
            cypher = cypher_part.strip()
    else:
        cypher = text.strip()
    try:
        validate_query_shape(cypher)
    except UnsupportedCypherError as e:
        return {
            "question": question,
            "cypher": cypher,
            "params": params,
            "rows": [],
            "rejected": True,
            "rejection_reason": str(e),
        }

    with driver.session() as session:
        result = session.run(cypher, **params)
        rows = [row.data() for row in result]

    return {
        "question": question,
        "cypher": cypher,
        "params": params,
        "rows": rows,
        "rejected": False,
        "rejection_reason": None,
    }