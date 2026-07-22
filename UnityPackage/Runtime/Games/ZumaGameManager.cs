using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;

namespace AIEngineer.Games
{
    public sealed class ZumaGameManager : MonoBehaviour
    {
        private readonly List<ZumaMarble> marbles = new();
        private Text scoreLabel;
        private Text hintLabel;
        public static bool RuntimeReady { get; private set; }
        public static bool MechanicsVerified { get; private set; }
        public int Score { get; private set; }

        private void Start()
        {
            RuntimeReady = true;
            MechanicsVerified = false;
            UpdateScoreLabel();
            Debug.Log("AI Engineer Zuma prototype runtime ready.");
        }

        public void Configure(Text score, Text hint)
        {
            scoreLabel = score;
            hintLabel = hint;
        }
        public void Register(ZumaMarble marble) { if (!marbles.Contains(marble)) marbles.Add(marble); }

        public void ResolveHit(ZumaMarble hit, Color projectileColor)
        {
            if (hit == null || !SameColor(hit.Color, projectileColor)) return;
            var index = marbles.IndexOf(hit);
            var matching = new List<ZumaMarble> { hit };
            CollectMatching(index - 1, -1, hit.Color, matching);
            CollectMatching(index + 1, 1, hit.Color, matching);
            if (matching.Count < 3) return;
            foreach (var marble in matching) { marbles.Remove(marble); Destroy(marble.gameObject); }
            Score += matching.Count * 10;
            UpdateScoreLabel();
            Debug.Log($"Zuma match resolved: {matching.Count} marbles, score {Score}.");
        }

        private void CollectMatching(int index, int direction, Color color, List<ZumaMarble> matching)
        {
            while (index >= 0 && index < marbles.Count && SameColor(marbles[index].Color, color)) { matching.Add(marbles[index]); index += direction; }
        }

        private void UpdateScoreLabel()
        {
            if (scoreLabel != null) scoreLabel.text = $"PUAN\n{Score:0000}";
            if (hintLabel != null) hintLabel.text = "NISAN AL • ATES ET • UC AYNI RENGI BIRLESTIR";
        }
        private static bool SameColor(Color left, Color right) => Vector4.Distance(left, right) < 0.1f;

        public void RunAcceptanceProbe()
        {
            if (marbles.Count >= 3 && !MechanicsVerified)
                ResolveHit(marbles[1], marbles[1].Color);
            MechanicsVerified = Score > 0;
            Debug.Log(MechanicsVerified
                ? "AI Engineer Zuma mechanics acceptance passed: matching marbles removed and score increased."
                : "AI Engineer Zuma mechanics acceptance failed: matching-marble probe did not score.");
        }
    }
}
