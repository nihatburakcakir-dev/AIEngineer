using UnityEngine;
using AIEngineer.Registry;
using AIEngineer.Runtime;
using AIEngineer.Models;

namespace AIEngineer.Actions
{
    public class FindObjectAction : IAIAction
    {
        public string Name => "FindObject";

        public bool Execute(
            RuntimeContext context,
            TaskModel task
        )
        {
            GameObject obj =
                GameObject.Find(task.target);

            if(obj == null)
            {
                Debug.LogError(
                    $"Object not found : {task.target}"
                );

                return false;
            }

            context.SelectedObject = obj;
            context.SelectedTransform = obj.transform;

            Debug.Log(
                $"Found : {obj.name}"
            );

            return true;
        }
    }
}
