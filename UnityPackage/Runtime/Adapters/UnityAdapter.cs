using UnityEngine;

namespace AIEngineer.Runtime.Adapters
{
    public static class UnityAdapter
    {
        public static GameObject Instantiate(
            GameObject prefab)
        {
            return Object.Instantiate(prefab);
        }
    }
}