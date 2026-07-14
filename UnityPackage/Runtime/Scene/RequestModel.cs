using System;
using System.Collections.Generic;

namespace AIEngineer.Scene
{
    [Serializable]
    public class RequestModel
    {
        public string prompt;

        public List<SceneObjectModel> objects;
    }
}
