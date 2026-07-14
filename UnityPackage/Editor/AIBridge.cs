using System.Collections.Generic;
using System.Linq;
using System.Text;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Networking;
using UnityEngine.SceneManagement;

[System.Serializable]
public class AIRequest
{
    public string prompt;
}

[System.Serializable]
public class AIResponse
{
    public string action;
    public string target;
    public string effect;
}

[System.Serializable]
public class SceneObjectList
{
    public List<SceneObject> items;

    public SceneObjectList(List<SceneObject> list)
    {
        items = list;
    }
}

public class AIBridge : EditorWindow
{
    string prompt = "Kurdun agzina mavi ates efekti ekle";

    [MenuItem("AI Engineer/Open Bridge")]
    public static void ShowWindow()
    {
        GetWindow<AIBridge>("AI Engineer");
    }

    private void OnGUI()
    {
        GUILayout.Label("AI Engineer", EditorStyles.boldLabel);

        GUILayout.Space(10);
        GUILayout.Label("Project");
        GUILayout.Label(Application.productName);

        GUILayout.Label("Unity");
        GUILayout.Label(Application.unityVersion);

        GUILayout.Label("Scene");
        GUILayout.Label(EditorSceneManager.GetActiveScene().name);

        GUILayout.Space(20);
        GUILayout.Label("Prompt");
        prompt = EditorGUILayout.TextField(prompt);

        GUILayout.Space(10);

        if (GUILayout.Button("Send To Python"))
            SendProjectInfo();
    }

    List<SceneObject> GetSceneObjects()
    {
        List<SceneObject> list = new();

        foreach (GameObject root in SceneManager.GetActiveScene().GetRootGameObjects())
            AddSceneObject(root.transform, list);

        return list;
    }

    void AddSceneObject(Transform t, List<SceneObject> list)
    {
        SceneObject obj = new();

        obj.name = t.name;
        obj.path = GetPath(t);
        obj.tag = t.tag;
        obj.layer = LayerMask.LayerToName(t.gameObject.layer);

        obj.position = new float[] { t.position.x, t.position.y, t.position.z };
        obj.rotation = new float[] { t.eulerAngles.x, t.eulerAngles.y, t.eulerAngles.z };
        obj.scale = new float[] { t.localScale.x, t.localScale.y, t.localScale.z };

        foreach (var c in t.GetComponents<UnityEngine.Component>())
            if (c != null)
                obj.components.Add(c.GetType().Name);

        list.Add(obj);

        foreach (Transform child in t)
            AddSceneObject(child, list);
    }

    string GetPath(Transform t)
    {
        if (t.parent == null)
            return t.name;

        return GetPath(t.parent) + "/" + t.name;
    }

    List<string> GetPrefabs()
    {
        return AssetDatabase.FindAssets("t:Prefab")
            .Select(g => AssetDatabase.GUIDToAssetPath(g))
            .Select(System.IO.Path.GetFileNameWithoutExtension)
            .Distinct()
            .ToList();
    }

    async void SendProjectInfo()
    {
        List<SceneObject> objects = GetSceneObjects();
        List<string> prefabs = GetPrefabs();

        string objectsJson = JsonUtility.ToJson(new SceneObjectList(objects));
        string prefabJson = string.Join(",", prefabs.ConvertAll(x => "\"" + x + "\""));

        string json =
            "{"
            + "\"project\":\"" + Application.productName + "\","
            + "\"unity\":\"" + Application.unityVersion + "\","
            + "\"scene\":\"" + EditorSceneManager.GetActiveScene().name + "\","
            + "\"prompt\":\"" + prompt.Replace("\"", "\\\"") + "\","
            + "\"objects\":" + objectsJson.Replace("{\"items\":", "").TrimEnd('}')
            + ",\"prefabs\":[" + prefabJson + "]"
            + "}";

        byte[] body = Encoding.UTF8.GetBytes(json);

        UnityWebRequest request = new UnityWebRequest("http://127.0.0.1:8080", "POST");
        request.uploadHandler = new UploadHandlerRaw(body);
        request.downloadHandler = new DownloadHandlerBuffer();
        request.SetRequestHeader("Content-Type", "application/json");

        await request.SendWebRequest();

        if (request.result != UnityWebRequest.Result.Success)
        {
            Debug.LogError(request.error);
            return;
        }

        AIResponse response = JsonUtility.FromJson<AIResponse>(request.downloadHandler.text);

        if (response == null)
            return;

        AIExecutor.Execute(response.action, response.target, response.effect);
    }
}
