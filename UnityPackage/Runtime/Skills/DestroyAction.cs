using UnityEngine;

using AIEngineer.Registry;
using AIEngineer.Runtime;
using AIEngineer.Models;

namespace AIEngineer.Actions
{
    public class DestroyAction : IAIAction
    {
        public string Name => "Destroy";

        public bool Execute(
            RuntimeContext context,
            TaskModel task
        )
        {
            if (
                context.SelectedObject == null
            )
            {
                Debug.LogError(
                    "No selected object."
                );

                return false;
            }

            Debug.Log(
                $"Destroy : {context.SelectedObject.name}"
            );

            Object.DestroyImmediate(
                context.SelectedObject
            );

            context.SelectedObject = null;
            context.SelectedTransform = null;

            return true;
        }
    }
}
