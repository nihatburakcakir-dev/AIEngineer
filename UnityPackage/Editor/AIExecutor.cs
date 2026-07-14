using UnityEngine;
using UnityEditor;
using System.Linq;

public static class AIExecutor
{
    public static void Execute(
        string action,
        string target,
        string effect
    )
    {
        switch(action)
        {
            case "SELECT_OBJECT":
                SelectObject(target);
                break;

            case "ADD_EFFECT":
                AddEffect(target,effect);
                break;
        }
    }

    static void SelectObject(string target)
    {
        GameObject obj = GameObject.Find(target);

        if(obj==null)
            return;

        Selection.activeGameObject=obj;

        EditorGUIUtility.PingObject(obj);
    }

    static void AddEffect(
        string target,
        string effect
    )
    {
        GameObject parent =
            GameObject.Find(target);

        if(parent==null)
        {
            Debug.LogError(
                "Target not found."
            );
            return;
        }

        string guid =
            AssetDatabase.FindAssets(effect + " t:Prefab")
            .FirstOrDefault();

        if(string.IsNullOrEmpty(guid))
        {
            Debug.LogError(
                "Prefab not found : " + effect
            );
            return;
        }

        string path =
            AssetDatabase.GUIDToAssetPath(guid);

        GameObject prefab =
            AssetDatabase.LoadAssetAtPath<GameObject>(
                path
            );

        GameObject instance =
            (GameObject)PrefabUtility.InstantiatePrefab(prefab);

        instance.transform.SetParent(
            parent.transform,
            false
        );

        instance.transform.localPosition=Vector3.zero;
        instance.transform.localRotation=Quaternion.identity;

        Selection.activeGameObject=instance;

        Debug.Log(
            "Effect created : " + effect
        );
    }
}
