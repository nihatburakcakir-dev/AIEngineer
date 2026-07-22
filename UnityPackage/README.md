# AI Engineer Complete

Local-first Unity AI engineering tools, workflows, and samples for Unity 6.

Included workflows

- Project indexing, code model, graph and Unity expertise.
- Transactional planning, autonomous apply, compile repair, Play Mode validation and rollback.
- Visual analysis, character placeholders and game scaffolding.
- Local Ollama autonomous code/scene/prefab/effect generation with transactional rollback, Qwen Code and Codex ChatGPT Plus account providers, and optional API-key cloud routing.
- GOKBORU: ATES YOLU Turkish-mythology mobile marble-shooter sample.
- AI Engineer > Control Center editor dashboard.

Install

1. Use Assets > Import Package > Custom Package and select AIEngineer-Complete.unitypackage.
2. Open AI Engineer > Control Center for the dashboard.
3. Open Assets/AIEngineerGenerated/Games/ReferenceZumaPrototype/ReferenceZumaPrototype.unity for the themed mobile sample.

UPM alternative: copy UnityPackage outside Assets, then use Window > Package Manager > + > Add package from disk and choose package.json.

The dashboard sends project-aware requests to the local Python service. Models may
inspect the project but return a validated change-set; Unity takes a snapshot,
applies supported file/scene/prefab/effect operations, compiles, repairs and rolls
back on failure. Full autonomy can be disabled whenever review-first operation is
preferred.
