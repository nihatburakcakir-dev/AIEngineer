using UnityEngine;
using AIEngineer.Models;
using AIEngineer.Registry;
using AIEngineer.Actions;
using AIEngineer.Unity;

namespace AIEngineer.Runtime
{
    public class WorkflowRunner
    {
        private readonly ActionRegistry registry =
            new ActionRegistry();

        private readonly RuntimeContext context =
            new RuntimeContext();

        public WorkflowRunner()
        {
            PrefabRegistry.Build();

            registry.Register(
                new FindObjectAction()
            );

            registry.Register(
                new FindPrefabAction()
            );

            registry.Register(
                new InstantiateAction()
            );

            registry.Register(
                new SetParentAction()
            );

            registry.Register(
                new ResetTransformAction()
            );

            registry.Register(
                new DestroyAction()
            );
        }

        public bool Run(
            WorkflowModel workflow
        )
        {
            Debug.Log(
                $"Workflow : {workflow.workflow}"
            );

            foreach (var task in workflow.tasks)
            {
                var action =
                    registry.Get(task.action);

                if (action == null)
                {
                    Debug.LogError(
                        $"Unknown Action : {task.action}"
                    );

                    return false;
                }

                if (
                    !action.Execute(
                        context,
                        task
                    )
                )
                {
                    return false;
                }
            }

            return true;
        }
    }
}
