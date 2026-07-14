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

        workflow.workflow = "Full Test";

        workflow.tasks = new List<TaskModel>()
        {
            new TaskModel()
            {
                action = "FindObject",
                target = "WolfMouth"
            },

            new TaskModel()
            {
                action = "FindPrefab",
                target = "Magic fire pro blue"
            },

            new TaskModel()
            {
                action = "Instantiate"
            },

            new TaskModel()
            {
                action = "SetParent"
            },

            new TaskModel()
            {
                action = "ResetTransform"
            }
        };

        runner.Run(workflow);
    }
}