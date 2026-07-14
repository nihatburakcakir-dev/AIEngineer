using UnityEngine;
using AIEngineer.Registry;
using AIEngineer.Runtime;
using AIEngineer.Models;
using AIEngineer.Runtime.Adapters;

namespace AIEngineer.Actions
{
    public class InstantiateAction : IAIAction
    {
        public string Name => "Instantiate";

        public bool Execute(
            RuntimeContext context,
            TaskModel task)
        {
            if (context.SelectedPrefab == null)
            {
                Debug.LogError("No prefab selected.");
                return false;
            }

            GameObject obj =
                UnityAdapter.Instantiate(
                    context.SelectedPrefab);

            context.LastCreatedObject = obj;

            Debug.Log(
                $"Instantiate : {obj.name}");

            return true;
        }
    }
}