# Model and upstream licenses

The code in this repository is separate from downloaded model weights.

| Component | Revision / source | License evidence |
|---|---|---|
| Brainwaves | `nightmedia/Qwen3.8-27B-Brainwaves` at `f9545772aab3abcb84b2f1822134a1c4a052669f` | [model card](https://huggingface.co/nightmedia/Qwen3.8-27B-Brainwaves), metadata `apache-2.0` |
| Qwen3.8/3.5 architecture | Qwen upstream | [Qwen3.8 repository](https://github.com/QwenLM/Qwen3.8), [Qwen3.5-27B card](https://huggingface.co/Qwen/Qwen3.5-27B) |
| vLLM | installed container/runtime | [vLLM license](https://github.com/vllm-project/vllm) |
| SGLang (optional) | pinned commit documented in `docs/RESEARCH.md` | [SGLang license](https://github.com/sgl-project/sglang) |

The model card identifies Brainwaves as an experimental merge and declares
Apache-2.0 metadata; it does not grant this repository ownership of the model or
its upstream component weights. Review all upstream terms before redistribution.
