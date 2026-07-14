using System;
using System.Collections.Generic;

[Serializable]
public class SceneObject
{
    public string name;

    public string path;

    public string tag;

    public string layer;

    public float[] position;

    public float[] rotation;

    public float[] scale;

    public List<string> components =
        new List<string>();
}
