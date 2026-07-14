using System;

namespace AIEngineer.Scene
{
    [Serializable]
    public class SceneObjectModel
    {
        public string name;

        public string path;

        public string parent;

        public string[] children;

        public string[] components;

        public string tag;

        public int layer;

        public bool active;

        public Vector3Model position;

        public Vector3Model rotation;

        public Vector3Model scale;
    }

    [Serializable]
    public class Vector3Model
    {
        public float x;

        public float y;

        public float z;
    }
}
