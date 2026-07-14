using System.Collections.Generic;

namespace AIEngineer.Registry
{
    public class ActionRegistry
    {
        readonly Dictionary<string, IAIAction>
            actions = new();

        public void Register(
            IAIAction action
        )
        {
            actions[action.Name] = action;
        }

        public IAIAction Get(
            string name
        )
        {
            actions.TryGetValue(
                name,
                out var action
            );

            return action;
        }
    }
}
