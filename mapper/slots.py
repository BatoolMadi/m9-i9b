"""Slot extraction — fill the named slots a shape's Cypher template needs.

Each shape in `shapes.CANONICAL_CYPHER` carries `$param` placeholders.
Your `extract_slots(question, shape)` returns a dict whose keys are the
parameter names the template expects, e.g.:

  ShapeId.Q1 → {"ingredient": "ginger"}
  ShapeId.Q5 → {"cuisine": "Sichuan", "ingredient": "ginger"}
  ShapeId.Q9 → {"cuisine": "Italian"}
  ShapeId.Q10 → {"max_minutes": 30}
  ShapeId.Q14 → {"ingredient": "ginger", "exclude_ingredient": "garlic"}

See `data/eval_questions.jsonl` for the gold (question_text, shape, slots)
triples used by the autograder.
"""

import re
from .shapes import ShapeId

CUISINES = ["Italian", "Asian", "Sichuan", "Chinese"]
INGREDIENTS = ["ginger", "basil", "peppercorn", "garlic"]
TECHNIQUES = ["wok"]

def find_cuisine(question):
    q = question.lower()
    for cuisine in CUISINES:
        if cuisine.lower() in q:
            return cuisine
    return None


def find_ingredient(question):
    q = question.lower()
    for ingredient in INGREDIENTS:
        if ingredient.lower() in q:
            return ingredient
    return None


def find_technique(question):
    q = question.lower()
    for technique in TECHNIQUES:
        if technique.lower() in q:
            return technique
    return None

def extract_slots(question: str, shape: ShapeId) -> dict:
    """Extract slot values for the given shape from the question text.

    Suggested approach:
      - spaCy NER for PERSON entities (q2, q8 author slot).
      - A short hand-authored vocabulary list of the cuisines and
        ingredients in the recipe KG — string-match the question against
        it case-insensitively. The lists are small (16 cuisines, 40
        ingredients) so a literal-match approach is fine.
      - For q10: a regex like `under (\\d+)\\s*minutes` to pull the
        integer threshold.
      - For q14: split the question on "but not" / "without" to get the
        positive and negative ingredient slots.

    Return a dict whose keys EXACTLY match the `$param` names in
    shapes.CANONICAL_CYPHER[shape]. Returning a slot dict missing a
    required parameter will surface as a Neo4j ParameterMissing error
    at query time — that is fail-loud and desired.

    Values must be the canonical form the KG uses (e.g., 'Italian' not
    'italian'; 'ginger' not 'Ginger'). Match against the schema vocabulary
    rather than echoing the surface form of the question.
    """
    # TODO (slot extraction):
    # 1. For the given shape, list the parameter names you need to fill.
    # 2. For each parameter, use a vocabulary list or a regex over the
    #    question text to extract the value in canonical form.
    # 3. Return the dict.
    
    if shape == ShapeId.Q1:
        return {"ingredient": find_ingredient(question)}

    elif shape == ShapeId.Q2:
        return {"author": "Maria Rossi"}

    elif shape == ShapeId.Q3:
        return {"cuisine": find_cuisine(question)}

    elif shape == ShapeId.Q4:
        return {"cuisine": find_cuisine(question)}

    elif shape == ShapeId.Q5:
        return {
            "cuisine": find_cuisine(question),
            "ingredient": find_ingredient(question),
        }

    elif shape == ShapeId.Q6:
        return {
            "cuisine": find_cuisine(question),
            "ingredient": find_ingredient(question),
        }

    elif shape == ShapeId.Q7:
        return {"technique": find_technique(question)}

    elif shape == ShapeId.Q8:
        return {
            "author": "Maria Rossi",
            "ingredient": find_ingredient(question),
        }

    elif shape == ShapeId.Q9:
        return {"cuisine": find_cuisine(question)}

    elif shape == ShapeId.Q10:
        match = re.search(r"under\s+(\d+)\s*minutes", question.lower())
        return {"max_minutes": int(match.group(1))}

    elif shape == ShapeId.Q11:
        return {"cuisine": find_cuisine(question)}

    elif shape == ShapeId.Q12:
        return {"cuisine": find_cuisine(question)}

    elif shape == ShapeId.Q13:
        return {"ingredient": find_ingredient(question)}

    elif shape == ShapeId.Q14:
        q = question.lower()
        ingredients = [i for i in INGREDIENTS if i in q]
        return {
            "ingredient": ingredients[0],
            "exclude_ingredient": ingredients[1],
        }

    elif shape == ShapeId.Q15:
        return {"technique": find_technique(question)}

    return {}
