using UnityEngine;
using AIEngineer.Registry;
using AIEngineer.Runtime;
using AIEngineer.Models;

namespace AIEngineer.Actions
{
    public class SetParentAction : IAIAction
    {
        public string Name => "SetParent";

        public bool Execute(
            RuntimeContext context,
            TaskModel task)
        {
            if (context.SelectedObject == null)
            {
                Debug.LogError("No selected object.");
                return false;
            }

            if (context.LastCreatedObject == null)
            {
                Debug.LogError("No created object.");
                return false;
            }

            context.LastCreatedObject.transform.SetParent(
                context.SelectedObject.transform,
                false);

            Debug.Log(
                $"Parent : {context.LastCreatedObject.name} -> {context.SelectedObject.name}");

            return true;
        }
    }
}
