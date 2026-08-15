# NexuX Editorial Benchmark Protocol

This benchmark is the gate for claims about clip-selection quality. It is not a proxy for any proprietary social-platform algorithm.

## Dataset

Use a stratified corpus of real videos covering podcasts, interviews, lectures, tutorials, commentary, gaming, vlogs, news, multi-speaker discussions, low-dialogue footage, and difficult audio. Keep source videos private/local when licensing requires it.

For each source, human editors provide 3-10 preferred clip intervals and a short reason for each selection. Each source should be rated by at least 3 independent editors.

## Metrics

- Top-1 IoU: overlap between NexuX top clip and the best human reference.
- Recall@K: fraction of human reference intervals matched by the top K candidates above a configured IoU threshold.
- Mean best IoU: best human overlap averaged across returned candidates.
- Duration compliance: share of clips inside the configured target range.
- Diversity: fraction of selected clips whose pairwise overlap stays below the configured threshold.
- Human preference: blinded A/B preference between NexuX and a baseline/editor selection.
- Editorial failure rate: clips with missing setup, missing payoff, premature cut, semantic corruption, or unusable framing.

## Required comparisons

For every release candidate, compare NexuX against:

1. a deterministic baseline (highest legacy heuristic score), and
2. a human-selected reference set.

Commercial-product comparisons are only valid when the same source material, output constraints, and blinded review procedure are used.

## Acceptance gate

Do not claim NexuX is superior to another editor from heuristic score alone. A superiority claim requires a published test corpus, matched source inputs, predeclared metrics, and statistically meaningful human preference results.
