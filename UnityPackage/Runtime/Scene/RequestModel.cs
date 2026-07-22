using System;
using System.Collections.Generic;

namespace AIEngineer.Scene
{
    [Serializable]
    public class RequestModel
    {
        public string prompt;

        public string projectPath;

        public List<SceneObjectModel> objects;

        public ProjectModel project;
    }
}
