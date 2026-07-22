from Source.Core.Workspace.unity_discovery import UnityDiscovery

finder = UnityDiscovery()

projects = finder.find_projects(
    r"C:\Bozkut1"
)

print()

for project in projects:

    info = finder.match_unity(project)

    if info:

        print()

        print("Project")

        print(info["project"])

        print()

        print("Unity")

        print(info["version"])

        print()

        print(info["unity"])
