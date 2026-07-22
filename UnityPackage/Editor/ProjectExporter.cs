using System.Collections.Generic;
using UnityEditor;

namespace AIEngineer.Editor
{
    public static class ProjectExporter
    {
        public static string[] GetPrefabs()
        {
            return GetAssets("t:Prefab");
        }

        public static string[] GetMaterials()
        {
            return GetAssets("t:Material");
        }

        public static string[] GetTextures()
        {
            return GetAssets("t:Texture");
        }

        public static string[] GetAudio()
        {
            return GetAssets("t:AudioClip");
        }

        public static string[] GetScripts()
        {
            return GetAssets("t:MonoScript");
        }

        public static string[] GetAnimations()
        {
            return GetAssets("t:AnimationClip");
        }

        public static string[] GetScenes()
        {
            return GetAssets("t:Scene");
        }

        static string[] GetAssets(
            string filter
        )
        {
            string[] guids =
                AssetDatabase.FindAssets(
                    filter
                );

            List<string> assets =
                new();

            foreach (string guid in guids)
            {
                string path =
                    AssetDatabase.GUIDToAssetPath(
                        guid
                    );

                assets.Add(path);
            }

            return assets.ToArray();
        }
    }
}
