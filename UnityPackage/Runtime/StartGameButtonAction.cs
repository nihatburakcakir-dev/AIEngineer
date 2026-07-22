using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.SceneManagement;

namespace AIEngineer.Runtime
{
    /// <summary>Runtime action attached to generated start buttons.</summary>
    public sealed class StartGameButtonAction : MonoBehaviour, IPointerClickHandler
    {
        public GameObject entranceRoot;
        public GameObject gameplayRoot;
        public string gameplayScenePath;

        public void OnPointerClick(PointerEventData eventData) => BeginGame();

        public void BeginGame()
        {
            var currentScenePath = SceneManager.GetActiveScene().path.Replace('\\', '/');
            var requestedScenePath = (gameplayScenePath ?? string.Empty).Replace('\\', '/');
            if (!string.IsNullOrWhiteSpace(requestedScenePath) && !string.Equals(currentScenePath, requestedScenePath, System.StringComparison.OrdinalIgnoreCase))
            {
                SceneManager.LoadScene(requestedScenePath);
                return;
            }
            if (gameplayRoot != null) gameplayRoot.SetActive(true);
            if (entranceRoot != null) entranceRoot.SetActive(false);
        }
    }
}
