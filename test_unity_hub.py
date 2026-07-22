from Source.Core.Workspace.unity_hub import UnityHub

hub = UnityHub()

print()

print("Unity Hub Projects")

print("------------------")

for project in hub.projects():

    print(project)
