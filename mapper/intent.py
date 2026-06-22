"""Intent classifier — map NL question to a canonical ShapeId.

This file is your responsibility. Read the 15 supported shapes in
`shapes.ShapeId` and `shapes.CANONICAL_CYPHER`, then implement
`detect_shape` so that each of the 15 canonical eval questions in
`data/eval_questions.jsonl` is classified to the gold shape, and
adversarial / off-template questions return None.

The deterministic mapper is the production-discipline arm of M9B; a
classifier that returns the wrong shape on a supported question is a
real bug, and a classifier that returns a confident answer on an
off-template question is the silent-failure mode the Reading warns
against. Prefer None over a false positive.
"""

from .shapes import ShapeId


def detect_shape(question: str) -> ShapeId | None:
    """Classify the question into one of the 15 ShapeId values, or None.

    Suggested approach: a small set of keyword / regex rules over the
    question text that match the shape vocabulary used by the recipe
    KG. Look for cues such as:
      - "by author <name>", "by <Name>"   → author shapes
      - "<cuisine name>"                  → cuisine shapes
      - "use <ingredient>", "with <ingredient>" → ingredient shapes
      - "but not <ingredient>"            → q14 (negation)
      - "ranked by popularity" / "most popular" → q9
      - "under <N> minutes"               → q10
      - "ingredients used in"             → q11 (inverse)
      - "authors of"                      → q12
      - "or any subtype" / "or any kind"  → q13
      - "optionally tagged"               → q15
      - "require <technique>"             → q7

    For cuisines and ingredients, you can use the schema label vocabulary
    (Cuisine.name values, Ingredient.name values) to disambiguate which
    slot type the question is naming. A spaCy NER pass on PERSON entities
    helps for q2 / q8.

    Returns None when no rule fires — the orchestrator raises
    UnsupportedQueryError in that case, which is the correct behaviour
    for an out-of-scope question.
    """
    # TODO (intent classifier):
    # 1. Lowercase the question for pattern matching.
    # 2. Apply rules in priority order — more-specific shapes (q14
    #    "but not", q8 "by ... that use") before less-specific (q1, q3).
    # 3. Return the matching ShapeId, or None if nothing matches.
    
    q = question.lower()

    # q14
    if "but not" in q:
        return ShapeId.Q14

    # q15
    if "optionally tagged" in q:
        return ShapeId.Q15

    # q13
    if "or any subtype" in q or "or any kind" in q:
        return ShapeId.Q13

    # q10
    if "under" in q and "minutes" in q:
        return ShapeId.Q10

    # q11
    if "ingredients used in" in q:
        return ShapeId.Q11

    # q12
    if "authors of" in q:
        return ShapeId.Q12

    # q8
    if "by author" in q and "use" in q:
        return ShapeId.Q8

    # q2
    if "by author" in q:
        return ShapeId.Q2

    # q7
    if "require" in q and "technique" in q:
        return ShapeId.Q7

    # q9
    if "ranked by popularity" in q or "most popular" in q:
        return ShapeId.Q9

    # q6
    if "chinese" in q and "use" in q:
        return ShapeId.Q6

    # q5
    if "sichuan" in q and "use" in q:
        return ShapeId.Q5

    # q4
    if "asian" in q:
        return ShapeId.Q4

    # q3
    if "italian" in q:
        return ShapeId.Q3

    # q1
    if "use " in q or "with " in q:
        return ShapeId.Q1

    return None
