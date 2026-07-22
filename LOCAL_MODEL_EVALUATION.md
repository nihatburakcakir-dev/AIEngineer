# Local Model Evaluation - Phase 8

Date: 21 July 2026

## Runtime configuration

- Local-only mode: enabled
- Text/planning/code model: `qwen3:8b`
- Vision model: `llava:7b`
- Endpoint: local Ollama at `127.0.0.1:11434`
- Cloud fallback: optional but inactive until the user adds their own API key environment variable and explicitly requests cloud mode.

## Live measurements

| Task | Model | Result | Time | Decision |
| --- | --- | --- | --- | --- |
| Structured planning reply | qwen3:8b | `LOCAL_BENCHMARK_OK` | 2.94 s | Use locally for chat, planning and small code-generation tasks. |
| Screenshot analysis | llava:7b | Rejected: incomplete/invalid strict JSON | 6.46 s | Keep local-only, but do not generate Unity content from this output. Require review or install/evaluate a stronger local vision model first. |

## Task policy

- Chat, planning, code generation: local `qwen3:8b`, then existing compile/test validators decide whether a change can proceed.
- Vision: local `llava:7b`; `ImageParser` rejects incomplete or schema-invalid evidence. Rejection is a safe outcome, not a fabricated visual analysis.
- Hybrid/cloud: supported as an explicit opt-in through OpenRouter-compatible `mode="cloud"` routing for both text and vision. It is inactive until the user configures their own key; the local default remains private and offline-capable.

## Acceptance conclusion

The essential offline path - text command to locally generated, validated simple work - is available without an internet dependency. The local vision evaluation is recorded as insufficient for unattended production generation with this model and remains protected by the strict parser.
