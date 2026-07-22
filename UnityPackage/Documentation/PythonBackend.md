# Python backend bundle

`AIEngineer-Python-Backend.zip` contains the current Python implementation for
the completed phases: the clean `Source/` tree, a portable `ai_config.json`
template, and local/cloud setup notes. Python bytecode caches, machine-specific
paths, local learning history, databases, models, and credentials are excluded.

## Use on another computer

1. Import `AIEngineer-Complete.unitypackage`.
2. Create a folder named `AIEngineerBackend` next to the Unity project and
   extract `AIEngineer-Python-Backend.zip` into it. The expected result is
   `AIEngineerBackend/Source/Server/server.py`.
3. Update `ai_config.json` so `project_root`, `unity_path`, and any optional
   provider settings match the target computer. Keep API keys in the named
   environment variables; do not write secrets into this file.
4. Install/start Ollama if local text or vision models are desired.
5. In Unity open **AI Engineer > Control Center**. Use **Choose backend folder**
   when the backend was extracted somewhere else, then start the local engine.

The Unity assets remain usable without the Python service; requests requiring
local planning or image analysis need the extracted backend.
