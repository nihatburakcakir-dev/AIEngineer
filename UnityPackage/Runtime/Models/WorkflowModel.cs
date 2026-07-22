using System;
using System.Collections.Generic;

namespace AIEngineer.Models
{
    [Serializable]
    public class WorkflowModel
    {
        public string workflow;

        public List<TaskModel> tasks;
    }
}
