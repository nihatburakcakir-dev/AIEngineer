# Optional Cloud Models

> Güncel sürümde Control Center ayrıca `Qwen (account > Codex)` ve
> `Codex Plus (account > Qwen)` seçeneklerini sunar. Hesap çağrısı başarısızsa
> diğer hesap denenir; ikisi de yoksa iş uygulanmadan durur. Qwen OAuth ücretsiz
> kotası 15 Nisan 2026'da kaldırılmıştır; Qwen Code'un kendisi açık kaynaktır.
> Codex CLI, `codex login` ile ChatGPT Plus abonelik oturumunu kullanabilir.

The project remains local-first. Cloud use is optional and disabled until a key exists in the user environment.

## OpenRouter free models

1. Create an OpenRouter API key in your own account.
2. In a new Windows PowerShell window, set it without putting the secret in this repository:

```powershell
setx OPENROUTER_API_KEY "your-key-here"
```

3. Restart Unity/Codex or open a new terminal so Windows exposes the new environment variable.
4. Use `mode="cloud"` when requesting text, planning or code generation. Use `OptionalVisionRouter(...).analyze(image, mode="cloud")` for visual analysis.

The default model route is `openrouter/free`; availability and rate limits are provider-controlled. `mode="local"` remains the default, so no image or prompt leaves the machine unless cloud mode is explicitly selected.

Never paste an API key into `ai_config.json`, source code, a Unity scene, or a git commit.
