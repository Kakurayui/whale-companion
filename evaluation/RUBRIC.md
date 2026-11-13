# Evaluation protocol

Research question: Does adding retrieved world facts and persistent visitor memory improve character consistency and factual recall compared with a basic character prompt?

## Controlled comparison

- Same provider, exact model name, temperature (0.4), maximum output tokens (350), character profile, and recent-history limit (6 messages / 3 exchanges).
- Baseline receives the profile, recent dialogue, and the current message.
- Enhanced additionally receives up to three BM25-retrieved known-world notes and saved visitor facts.
- Each scenario and mode uses a fresh visitor identity. Memory scenarios introduce a fact and then start a separate session, so the fact is absent from recent history.
- Run 20 scenarios three times per mode. Feiyu: 120 scored responses plus 42 setup responses = **162 model requests**. The legacy Mira set has 30 setup responses = **150 model requests**. These are planned runs, not completed findings; `python -m tools.evaluate --dry-run` reports the selected set's count.
- The runner alternates mode order by repeat, logs failures, actual returned model identifiers, prompts, token usage, latency, and content/code checksums. It does not auto-score dialogue quality.
- Treat API aliases as potentially changing models; run both modes close together and report the actual identifiers and test dates.

## Human scores

Use the expected behavior in [scenarios/feiyu.json](scenarios/feiyu.json) or [scenarios/mira.json](scenarios/mira.json), and the corresponding `content/<character>/` files. Leave an inapplicable score blank, rather than assigning zero. Annotate a quotation or a short reason for every failure.

| Measure | 0 | 1 | 2 |
|---|---|---|---|
| Lore accuracy | Contradicts or invents the requested canonical fact | Partly correct, incomplete, or honestly does not know | Correct and sufficiently complete, with no conflicting claims |
| Memory accuracy | Incorrect detail, invented recall, or cannot recall | Partly correct recall | Correct relevant detail, including the latest correction |
| Character consistency | Abandons identity or seriously contradicts personality/knowledge limits | Minor drift, unnatural tone, or unnecessary out-of-character explanation | Maintains identity, tone, and knowledge limits |
| Unknown-information handling | Confidently invents an answer or leaks a secret | Expresses uncertainty but adds unsupported claims | Clearly acknowledges limits while staying in character |

An honest baseline "I don't know your name" earns 0 for memory recall but can earn 2 for character consistency/unknown handling. Do not confuse honesty with recall accuracy.

Two reviewers should score independently where possible. Hide mode labels while scoring if practical; compare disagreements and document how they were resolved. Preserve the original independent scores if you reconcile them.

## Reporting

- Report applicable scenario counts, means per measure and category, and the number of model-request failures separately. Exclude request failures from dialogue-quality means, but disclose their count.
- Report median response time and range. Timing covers the full model request; it is not time to first token.
- Retrieval hit is an infrastructure measure: whether the expected document appeared among retrieved notes. It does not prove the generated answer used the document correctly.
- Include examples from both modes, mistakes, and contradictory outcomes.
- The comparison measures retrieval and memory together. It cannot attribute an improvement to either component separately without additional conditions.
- The sample is small and authored for this project. Feiyu uses Chinese scenarios; the legacy Mira set uses English. Do not claim general human preference, statistical significance, or multilingual retrieval quality without additional evidence.
