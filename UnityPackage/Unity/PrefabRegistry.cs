using UnityEditor;
using UnityEngine;
using System.Collections.Generic;

namespace AIEngineer.Unity
{
    public static class PrefabRegistry
    {
        static readonly Dictionary<string, GameObject> prefabs = new();

        public static void Build()
        {
            prefabs.Clear();

            string[] guids =
                AssetDatabase.FindAssets("t:Prefab");

            foreach (string guid in guids)
            {
                string path =
                    AssetDatabase.GUIDToAssetPath(guid);

                GameObject prefab =
                    AssetDatabase.LoadAssetAtPath<GameObject>(path);

                if (prefab != null)
                    prefabs[prefab.name] = prefab;
            }

            Debug.Log($"Prefab Registry : {prefabs.Count}");
        }

        public static GameObject Find(string name)
        {
            prefabs.TryGetValue(name, out var prefab);
            return prefab;
        }
    }
}
