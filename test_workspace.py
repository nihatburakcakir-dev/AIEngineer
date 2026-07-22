from Source.Core.Workspace.workspace_manager import WorkspaceManager

manager = WorkspaceManager()

versions = manager.find_unity_versions()

print()

print("Installed Unity versions")

print("-----------------------")

for i, item in enumerate(versions):

    print(
        i + 1,
        item["version"]
    )

if versions:

    manager.set_unity(
        versions[0]["path"]
    )

    print()

    print(
        "Selected :",
        manager.unity_path()
    )
