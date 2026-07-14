using AIEngineer.Models;
using AIEngineer.Runtime;

namespace AIEngineer.Registry
{
    public interface IAIAction
    {
        string Name { get; }

        bool Execute(
            RuntimeContext context,
            TaskModel task
        );
    }
}
