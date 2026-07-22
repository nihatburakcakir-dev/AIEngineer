# AI Engineer Complete - Installation

## Custom Unity package

1. In Unity open **Assets > Import Package > Custom Package**.
2. Select `AIEngineer-Complete.unitypackage`.
3. Open **AI Engineer > Control Center**.

All tools are installed under `Assets/AIEngineer`. The themed mobile sample is at:

`Assets/AIEngineerGenerated/Games/ReferenceZumaPrototype/ReferenceZumaPrototype.unity`

The complete Python phase implementation is included at
`Assets/AIEngineer/Documentation/AIEngineer-Python-Backend.zip`. Extract it on
the receiving computer when local planning, vision, learning memory, or tests
are required.

## UPM folder alternative

Copy the `UnityPackage` folder outside an existing project's `Assets` directory.
Then choose **Window > Package Manager > + > Add package from disk** and select
the included `package.json`.

## Local service

The Control Center creates validated autonomous change sets through the local
Python service. Local Ollama can plan and apply code, scene, prefab, material,
effect, and background operations after validation. It reads bounded project and
Unity-package documentation context, then Unity creates a backup, compiles and
rolls back failed work. Qwen Code and Codex ChatGPT Plus remain optional account
providers with account-to-account failover. See `MODEL_VE_OTONOM_KULLANIM.md`
for provider login and rollback behavior.
