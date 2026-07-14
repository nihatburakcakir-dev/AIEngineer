using UnityEngine;
using UnityEngine.Networking;

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

            requestData.objects =
                SceneExporter.Export();

            string json =
                JsonUtility.ToJson(
                    requestData,
                    true
                );

            Debug.Log(
                json
            );

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

            if (
                request.result !=
                UnityWebRequest.Result.Success
            )
            {
                Debug.LogError(
                    request.error
                );

                return "";
            }

            return
                request.downloadHandler.text;
        }
    }
}
