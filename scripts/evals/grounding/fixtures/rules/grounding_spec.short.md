Claim grounding (investing-insight):

SUPPORTED only if the claim restates cited factual_payload leaves as field/value pairs for that same leaf.

UNSUPPORTED if any of these hold:
- reverse pairing (A's value presented as B's value)
- cross-field mix (a number/date/string bound to the wrong field)
- leftover extra fact, event, name, or open-class word not in the payload
- Unicode leftover or a single extra letter token
- wrapper/meta used as fact: evidence_id, kind, ref, *_id
- year used as a full date, or a number used for a different field
- negation or novel paraphrase that adds words not in the payload

Copula words (is/was/were/are) and ":" are noise; they do not create a relation.
A true field/value pair may appear in either order and is SUPPORTED.
Token presence in the payload bag is not enough: the field must match that leaf's value.
An allowed evidence_id is not enough.
