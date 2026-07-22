using UnityEngine;
using UnityEngine.Networking;

using UnityEditor;

using System.IO;
using System.Text;
using System.Threading.Tasks;

using AIEngineer.Scene;

namespace AIEngineer.Editor
{
    public static class RequestSender
    {
        public static async Task<string> Send(
            string prompt
        )
        {
            RequestModel requestData =
                new RequestModel();

            requestData.prompt =
                prompt;

            requestData.projectPath =
                Directory.GetParent(
                    Application.dataPath
                ).FullName;

            requestData.objects =
                SceneExporter.Export();

            requestData.project =
                new ProjectModel
                {
                    prefabs =
                        ProjectExporter.GetPrefabs(),

                    materials =
                        ProjectExporter.GetMaterials(),

                    textures =
                        ProjectExporter.GetTextures(),

                    audio =
                        ProjectExporter.GetAudio(),

                    scripts =
                        ProjectExporter.GetScripts(),

                    animations =
                        ProjectExporter.GetAnimations(),

                    scenes =
                        ProjectExporter.GetScenes()
                };

            string json =
                JsonUtility.ToJson(
                    requestData,
                    true
                );

            Debug.Log(json);

            using UnityWebRequest request =
                new UnityWebRequest(
                    "http://127.0.0.1:8080",
                    "POST"
                );

            byte[] body =
                Encoding.UTF8.GetBytes(
                    json
                );

            request.uploadHandler =
                new UploadHandlerRaw(
                    body
                );

            request.downloadHandler =
                new DownloadHandlerBuffer();

            request.SetRequestHeader(
                "Content-Type",
                "application/json"
            );

            var op =
                request.SendWebRequest();

            while (!op.isDone)
            {
                await Task.Yield();
            }

            if
            (
                request.result !=
                UnityWebRequest.Result.Success
            )
            {
                Debug.LogError("========== REQUEST FAILED ==========");

                Debug.LogError(
                    "Result : " + request.result
                );

                Debug.LogError(
                    "Error : " + request.error
                );

                Debug.LogError(
                    "HTTP Code : " + request.responseCode
                );

                if
                (
                    request.downloadHandler != null
                )
                {
                    Debug.LogError(
                        "SERVER RESPONSE:"
                    );

                    Debug.LogError(
                        request.downloadHandler.text
                    );
                }

                Debug.LogError("====================================");

                return "";
            }

            return
                request.downloadHandler.text;
        }
    }
}

