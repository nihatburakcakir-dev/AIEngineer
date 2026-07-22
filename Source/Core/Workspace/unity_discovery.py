import os
from pathlib import Path

class UnityDiscovery:

    def __init__(self):

        self.editor_root = Path(
            r"C:\Program Files\Unity\Hub\Editor"
        )

    def installed_versions(self):

        versions = {}

        if not self.editor_root.exists():

            return versions

        for folder in self.editor_root.iterdir():

            exe = folder / "Editor" / "Unity.exe"

            if exe.exists():

                versions[folder.name] = str(exe)

        return versions

    def find_projects(self, root="C:\\"):

        projects = []

        for current, dirs, files in os.walk(root):

            if "ProjectSettings" in dirs:

                version_file = os.path.join(
                    current,
                    "ProjectSettings",
                    "ProjectVersion.txt"
                )

                if os.path.exists(version_file):

                    projects.append(current)

                    dirs.clear()

        return projects

    def project_version(self, project):

        version_file = os.path.join(
            project,
            "ProjectSettings",
            "ProjectVersion.txt"
        )

        if not os.path.exists(version_file):

            return None

        with open(
            version_file,
            encoding="utf8"
        ) as f:

            for line in f:

                if line.startswith("m_EditorVersion:"):

                    return line.split(":")[1].strip()

        return None

    def match_unity(self, project):

        version = self.project_version(project)

        if version is None:

            return None

        installed = self.installed_versions()

        if version not in installed:

            return None

        return {

            "project": project,

            "version": version,

            "unity": installed[version]

        }
