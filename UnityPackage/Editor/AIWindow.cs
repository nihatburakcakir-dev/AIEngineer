using UnityEditor;
using UnityEngine;

using AIEngineer.Runtime;
using AIEngineer.Models;

namespace AIEngineer.Editor
{
    public class AIWindow : EditorWindow
    {
        string prompt = "";

        static void Open()
        {
            GetWindow<AIWindow>(
                "AI Engineer"
            );
        }

        void OnEnable()
        {
            Debug.Log(
                "[AI] AIWindow Enabled"
            );

            ServerManager.Start();
        }

        void OnGUI()
        {
            GUILayout.Label(
                "AI Engineer",
                EditorStyles.boldLabel
            );

            GUILayout.Space(10);

            GUILayout.Label(

                ServerManager.IsRunning ?

                "🟢 Server Started By Unity"

                :

                "🟡 External / Unknown"

            );

            GUILayout.Space(15);

            GUILayout.Label(
                "Prompt"
            );

            prompt =
                EditorGUILayout.TextArea(
                    prompt,
                    GUILayout.Height(120)
                );

            GUILayout.Space(10);

            GUI.enabled =
                !string.IsNullOrWhiteSpace(
                    prompt
                );

            if (
                GUILayout.Button(
                    "Execute"
                )
            )
            {
                Execute();
            }

            GUI.enabled = true;
        }

        async void Execute()
        {
            string json =
                await RequestSender.Send(
                    prompt
                );

            if (
                string.IsNullOrWhiteSpace(
                    json
                )
            )
            {
                Debug.LogError(
                    "Empty Response"
                );

                return;
            }

            Debug.Log(
                json
            );

            WorkflowModel workflow =
                JsonWorkflowLoader.Load(
                    json
                );

            if (
                workflow == null
            )
            {
                Debug.LogError(
                    "Workflow Parse Failed"
                );

                return;
            }

            WorkflowRunner runner =
                new WorkflowRunner();

            runner.Run(
                workflow
            );
        }
    }
}
