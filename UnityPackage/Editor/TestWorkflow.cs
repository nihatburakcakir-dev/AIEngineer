using UnityEditor;
using System.Collections.Generic;
using AIEngineer.Runtime;
using AIEngineer.Models;

public static class TestWorkflow
{
    [MenuItem("AI/Test Workflow")]
    public static void Run()
    {
        WorkflowRunner runner = new WorkflowRunner();

        WorkflowModel workflow = new WorkflowModel();

        workflow.workflow = "test";

        workflow.tasks = new List<TaskModel>()
        {
            new TaskModel()
            {
                action = "FindObject",
                target = "WolfMouth"
            }
        };

        runner.Run(workflow);
    }
}
