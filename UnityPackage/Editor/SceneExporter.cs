using System.Collections.Generic;
using UnityEngine;
using AIEngineer.Scene;

namespace AIEngineer.Editor
{
    public static class SceneExporter
    {
        public static List<SceneObjectModel> Export()
        {
            List<SceneObjectModel> list =
                new();

            foreach
            (
                GameObject go
                in Object.FindObjectsByType<GameObject>(
                    FindObjectsSortMode.None
                )
            )
            {
                SceneObjectModel obj =
                    new SceneObjectModel();

                obj.name = go.name;

                obj.path =
                    BuildPath(go.transform);

                obj.parent =
                    go.transform.parent
                    ?
                    go.transform.parent.name
                    :
                    "";

                obj.tag = go.tag;

                obj.layer = go.layer;

                obj.active =
                    go.activeSelf;

                obj.position =
                    new Vector3Model
                    {
                        x = go.transform.position.x,
                        y = go.transform.position.y,
                        z = go.transform.position.z
                    };

                obj.rotation =
                    new Vector3Model
                    {
                        x = go.transform.eulerAngles.x,
                        y = go.transform.eulerAngles.y,
                        z = go.transform.eulerAngles.z
                    };

                obj.scale =
                    new Vector3Model
                    {
                        x = go.transform.localScale.x,
                        y = go.transform.localScale.y,
                        z = go.transform.localScale.z
                    };

                List<string> children =
                    new();

                foreach
                (
                    Transform child
                    in go.transform
                )
                {
                    children.Add(
                        child.name
                    );
                }

                obj.children =
                    children.ToArray();

                List<string> comps =
                    new();

                foreach
                (
                    Component c
                    in go.GetComponents<Component>()
                )
                {
                    if (c == null)
                        continue;

                    comps.Add(
                        c.GetType().Name
                    );
                }

                obj.components =
                    comps.ToArray();

                list.Add(obj);
            }

            return list;
        }

        static string BuildPath(
            Transform t
        )
        {
            string path =
                t.name;

            while
            (
                t.parent != null
            )
            {
                t = t.parent;

                path =
                    t.name
                    + "/"
                    + path;
            }

            return path;
        }
    }
}
