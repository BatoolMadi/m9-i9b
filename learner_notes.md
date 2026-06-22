# Integration 9B - Learner Notes

Document your design choices and what you learned. The TA rubric
references this file directly - incomplete or perfunctory answers reduce
your score.

## 1. Intents you handled and how you classified them

Describe your `detect_shape` rules. Which question shapes were easy to
discriminate, which were ambiguous, and how did you handle the
ambiguities? Cite at least one specific question from
`data/eval_questions.jsonl` where two shapes were plausible candidates.

My Answer:

I implemented `detect_shape` using rule-based keyword matching over the lowercased question text. The classifier applies rules in priority order, where more specific shapes are checked before broader ones to avoid false positives.

Examples of rules:

* `"but not"` : Q14 (negation)
* `"optionally tagged"` : Q15
* `"or any subtype"` : Q13
* `"under <N> minutes"` : Q10
* `"ingredients used in"` : Q11
* `"authors of"` : Q12
* `"by author" + "use"` : Q8
* `"by author"` : Q2
* `"require" + "technique"` : Q7
* `"ranked by popularity"` : Q9

The easiest shapes to classify were highly specific ones like Q10, Q14, and Q15 because they contain unique keywords.

The most ambiguous shapes were:

* Q3 vs Q4 (direct cuisine match vs subclass traversal)
* Q5 vs Q6 (direct cuisine + ingredient vs hierarchical cuisine + ingredient)
* Q2 vs Q8 (author only vs author + ingredient)

For example, "Find Sichuan recipes that use ginger" could initially look similar to Q6 because both involve cuisine + ingredient. However, Sichuan maps to Q5 (direct cuisine match), while Chinese maps to Q6 because it requires subclass traversal.

## 2. A question that worked end-to-end

Pick one of the 15 canonical questions, walk through the pipeline:
what `detect_shape` returned, what `extract_slots` returned, the
compiled Cypher (with $param placeholders), the bound params dict, and
the rows the driver returned. Paste the actual CLI output.

My Answer:

I used the question:

`Find recipes that use ginger`

Pipeline walkthrough:

1. Intent Detection

* `detect_shape(question)` returned:
* `ShapeId.Q1`

2. Slot Extraction

* `extract_slots(question, ShapeId.Q1)` returned:

```python
{"ingredient": "ginger"}
```

3. Cypher Compilation

Compiled query:

```cypher
MATCH (r:Recipe)-[:USES_INGREDIENT]->(:Ingredient {name: $ingredient})
RETURN r.name AS recipe
ORDER BY r.name
LIMIT 50
```

4. Bound Parameters

```python
{"ingredient": "ginger"}
```

5. Neo4j Execution

The query was executed through:

```python
session.run(cypher, **params)
```

6. Returned Rows

Example returned rows:

```python
{'recipe': 'Ginger Chicken Stir Fry'}
{'recipe': 'Spicy Ginger Noodles'}
```

CLI output:

```bash
python cli.py "Find recipes that use ginger"
{'recipe': 'Ginger Chicken Stir Fry'}
{'recipe': 'Spicy Ginger Noodles'}
```

This confirmed the full NL -> intent -> slots -> Cypher -> Neo4j pipeline worked correctly.

## 3. A failure mode you diagnosed

Either a question that you initially mis-classified (and why), or an
adversarial / off-template question and what your `UnsupportedQueryError`
message told the caller. If you implemented Tier 3, you may also use a
case where the LLM emitted unsafe Cypher and your allowlist rejected it

* describe the prompt, the Cypher returned, and the clause that
  triggered the rejection.

My Answer:

One failure mode I encountered was incorrect classification caused by overlapping patterns.

For example, the question:

`Find recipes by author Maria Rossi that use basil`

contains both:

* `by author`
* `use basil`

This means it could incorrectly match:

* Q2 (author-only)
  or
* Q1 (ingredient-only)

The correct shape is Q8 because it combines both author and ingredient constraints.

I fixed this by checking more specific patterns before general ones. Specifically, I placed the Q8 rule (`by author` + `use`) before Q2 and Q1.

I also tested off-template questions. For unsupported inputs, the pipeline raises `UnsupportedQueryError` instead of returning an empty result list. This fail-loud behavior improves debugging and prevents silent failures.

## 4. A design tradeoff between the deterministic mapper and the Tier 3 chain

When would you prefer the deterministic mapper over the LLM chain in
production, and vice versa? Cite a concrete dimension (latency,
auditability, schema-coverage cost, distribution-shift robustness,
operational risk) for each side. Both implementations are first-class -
your answer should reflect that, not pick a winner.

My Answer:

The deterministic mapper is best for production systems where auditability, safety, and predictable behavior are critical.

Advantages:

* Low latency
* Fully deterministic
* Easy to debug
* Strong safety due to parameterized Cypher templates
* High explainability because every query maps to a known template

This approach works best when the schema and question surface are bounded.

The Tier 3 LLM chain is better when input distribution is open-ended and users may ask many variations of questions.

Advantages:

* More flexible with natural language
* Handles unseen phrasing better
* Scales better when question templates become too large to maintain manually

However, it introduces tradeoffs:

* Higher latency
* More operational complexity
* Potential safety risks from LLM-generated Cypher
* Requires allowlist validation and stronger safeguards

In production, I would prefer the deterministic mapper for stable and high-safety systems, and the LLM chain for broader user-facing systems where flexibility matters more.
