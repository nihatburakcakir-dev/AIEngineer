using UnityEngine;
using AIEngineer.Registry;
using AIEngineer.Runtime;
using AIEngineer.Models;

namespace AIEngineer.Actions
{
    public class ResetTransformAction : IAIAction
    {
        public string Name => "ResetTransform";

        public bool Execute(
            RuntimeContext context,
            TaskModel task)
        {
            if (context.LastCreatedObject == null)
            {
                Debug.LogError("No created object.");
                return false;
            }

            Transform t =
                context.LastCreatedObject.transform;

            t.localPosition = Vector3.zero;
            t.localRotation = Quaternion.identity;
            t.localScale = Vector3.one;

            Debug.Log(
                $"Reset Transform : {t.name}");

            return true;
        }
    }
}
