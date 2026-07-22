using UnityEngine;

namespace AIEngineer.Characters
{
    /// <summary>Records the concept art used for a generated placeholder prefab.</summary>
    public sealed class CharacterSourceImage : MonoBehaviour
    {
        [SerializeField] private Texture2D sourceImage;

        public Texture2D SourceImage => sourceImage;

        public void SetSourceImage(Texture2D image)
        {
            sourceImage = image;
        }
    }
}
