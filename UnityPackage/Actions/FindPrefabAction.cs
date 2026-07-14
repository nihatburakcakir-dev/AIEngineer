using UnityEngine;
using AIEngineer.Registry;
using AIEngineer.Runtime;
using AIEngineer.Models;
using AIEngineer.Unity;

namespace AIEngineer.Actions
{
    public class FindPrefabAction : IAIAction
    {
        public string Name => "FindPrefab";

        public bool Execute(
            RuntimeContext context,
            TaskModel task)
        {
            var prefab =
                PrefabRegistry.Find(task.target);

            if (prefab == null)
            {
                Debug.LogError(
                    $"Prefab not found : {task.target}");

                return false;
            }

            context.SelectedPrefab = prefab;

            Debug.Log(
                $"Prefab Found : {prefab.name}");

            return true;
        }
    }
}
