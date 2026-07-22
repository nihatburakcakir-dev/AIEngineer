# AI Engineer v0.3.0 — Archived Release Notes

| Release date | Target branch | Unity compatibility |
| --- | --- | --- |
| 22 July 2026 | `develop` | Unity 6 / 6000.x |

> This is the English archive of the original detailed v0.3.0 release notes.
> For the current visual release overview, see [the main release notes](../RELEASE_NOTES_v0.3.0.md).

## Overview

v0.3.0 transforms AI Engineer from a simple command window into a local-first
Unity production tool. It can inspect a Unity project, the active scene,
existing C# APIs, project assets, and locally available Unity documentation,
then apply changes through a transaction log.

The primary goal of this release is to turn model output into a reviewable
change set before writing anything to the project, and to apply only operations
that pass validation.

## Major additions

### Local model and two-pass gameplay planning

- Added `qwen3:30b` support for text and code planning.
- Added local `llava:7b` support for reference-image analysis.
- Gameplay requests such as bombs, power-ups, projectiles, enemies, and chain
  reactions are handled in two stages:
  1. Behaviour, spawning/distribution, effects/audio, existing-system
     integration, and acceptance tests are identified.
  2. An executable Unity change set is generated from that architecture.
- The local model response budget was increased for code-heavy plans.
- Broken or incomplete JSON is replanned before it reaches Unity.

### Project-grounded validation

- Real GameObject paths from the active scene are provided to the model.
- Public methods and fields from project C# classes are extracted as a compact
  `script_api` summary.
- Calls to unavailable methods, such as a nonexistent `RemoveBall`, are blocked
  before execution.
- `add_component` and `set_property` operations can target only real Hierarchy
  objects.
- Missing prefabs, audio, materials, scenes, and other Unity asset paths are
  rejected during pre-validation.
- A new gameplay `MonoBehaviour` is not considered complete unless it is bound
  to a scene or prefab.
- A gameplay plan is not applied until requested random behaviour code and its
  effect connections are present.

### Autonomous application and rollback

- File operations, Unity operations, and validations run in separate stages.
- Unity compilation is awaited after C# files are written.
- When compilation succeeds, scene, prefab, material, effect, and component
  operations are applied.
- Play Mode validation can be run when requested.
- Unity and compiler diagnostics are sent back to the model on failure.
- If a repair cannot succeed, the transaction backup is restored.
- The latest successful operation can be undone from Control Center.

### Safe Unity output area

- The AI Engineer package directory, `Assets/AIEngineer`, is protected from
  autonomous edits.
- Games, characters, UI, and other generated content are stored under
  `Assets/AIEngineerGenerated`.
- If a package sample scene is open when a change is requested, the scene is
  copied to an editable project area first.
- Legacy `Assets/AIEngineer/GeneratedGames` and `GeneratedCharacters` paths are
  redirected to the new safe output area.

### Mobile UI and reference-image workflow

- The model can select `rebuild`, `background`, or `hero` layouts for a
  reference image.
- Image fitting can be `contain` or `cover`; images are no longer forced into a
  distorted shape.
- The CTA position can be selected from nine normalized anchors.
- A start CTA is generated as a real Unity `Button`.
- The button can reveal the existing gameplay root or open a valid Unity scene.
- Existing generated menus can be safely replaced based on the model decision.
- Landscape and portrait mobile CanvasScaler layouts are supported.

### Model providers

- Local Ollama is the primary operating mode.
- Qwen Code account connection and terminal workflow were added.
- Codex CLI account connection was added.
- Account-based providers still generate reviewable change sets; direct mutation
  authority is not granted to the model.
- Cloud use is optional, and local operation continues without an API key.

### Unity production capabilities

- C# creation and controlled text changes
- GameObject creation
- Component addition and serialized field binding
- Prefab and material creation
- ParticleSystem-based effect creation
- Mobile entry UI creation
- 2D and 3D character prefab creation
- Game prototypes and marble-shooter sample scenes
- Scene saving, validation, and transaction-based rollback

## Control Center workflow

Open `AI Engineer > Control Center` from the Unity menu.

1. Choose a workspace: Create, Analyze, Repair, Games, or Memory.
2. Write the request in Turkish or English.
3. Optionally select a reference image.
4. Select a local model or an account provider.
5. Generate and inspect the plan.
6. Apply only a plan with correct targets and paths.
7. Check Console, compilation, and Play Mode results.
8. Use **Undo last operation** when necessary.

## Installation and upgrade

For new installation or moving to another computer, see:

- `UnityPackage/INSTALL.md`
- `UnityPackage/BASKA_PC_KURULUM.md`
- `UnityPackage/CONTROL_CENTER_KULLANIM_KILAVUZU.md`
- `UnityPackage/MODEL_VE_OTONOM_KULLANIM.md`

When upgrading from an earlier version, allow Unity to finish script
compilation. Existing package-generated games are preserved; new output is
written under `Assets/AIEngineerGenerated`.
