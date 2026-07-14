using UnityEngine;
using AIEngineer.Models;

namespace AIEngineer.Runtime
{
    public static class JsonWorkflowLoader
    {
        public static WorkflowModel Load(
            string json
        )
        {
            return JsonUtility.FromJson<WorkflowModel>(
                json
            );
        }
    }
}
