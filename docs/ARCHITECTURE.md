# System architecture

The stack separates model serving, benchmark generation, deterministic scoring,
and subjective review.

```text
OpenAI client ──> vLLM or SGLang
                     │
       BF16 weights + paged KV + prefix/radix cache
                     │
       GDN recurrent state + 16-layer full-attention KV
                     │
             MI300X gfx942 / ROCm

Arro LongWriter fixtures ──> same API ──> raw result JSONL
         │                                      │
   gold event/knowledge/relationship state  machine metrics
                                                │
                                   blinded prose review + aggregate report
```

The 48 GDN layers carry recurrent state rather than an ordinary full-history KV
for every token. Only the 16 full-attention layers scale linearly with context;
the memory model therefore does not multiply a conventional 64-layer KV formula.
The vision tower is skipped for text-only story tests with `--language-model-only`.

Stable story prefixes are emitted before volatile scene requests so automatic
prefix caching can be measured honestly. The benchmark never places timestamps,
UUIDs, or request IDs before reusable content.
