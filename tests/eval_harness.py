"""
Evaluation harness for VibeMatch.
Runs predefined reliability checks and prints a pass/fail summary.

Usage:
    python tests/eval_harness.py
"""

import sys
import logging
from pathlib import Path

# Silence logger output so test results stay readable
logging.disable(logging.CRITICAL)

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from recommender import load_songs, recommend_songs, _validate_prefs

CSV_PATH = Path(__file__).parent.parent / "data" / "songs.csv"


def run():
    songs = load_songs(str(CSV_PATH))
    results = []
    passed = 0

    def check(name, condition, detail=""):
        nonlocal passed
        status = "PASS" if condition else "FAIL"
        if condition:
            passed += 1
        results.append((status, name, detail))

    # 1. Chill Lofi: at least 2 lofi tracks in top 5
    recs = recommend_songs({"genre": "lofi", "mood": "chill", "energy": 0.2}, songs, k=5)
    lofi_count = sum(1 for s, _, _ in recs if s["genre"] == "lofi")
    check("Chill Lofi returns >=2 lofi tracks in top 5", lofi_count >= 2, f"got {lofi_count}")

    # 2. High-Energy Pop: at least 1 pop track in top 5
    recs = recommend_songs({"genre": "pop", "mood": "happy", "energy": 0.9}, songs, k=5)
    pop_count = sum(1 for s, _, _ in recs if s["genre"] == "pop")
    check("High-Energy Pop returns >=1 pop track in top 5", pop_count >= 1, f"got {pop_count}")

    # 3. Results are always sorted by score descending
    recs = recommend_songs({"genre": "rock", "mood": "angry", "energy": 0.95}, songs, k=5)
    scores = [score for _, score, _ in recs]
    check(
        "Results are sorted by score descending",
        scores == sorted(scores, reverse=True),
        f"scores={[round(s, 2) for s in scores]}",
    )

    # 4. Missing genre still returns k results (no crash)
    recs = recommend_songs({"genre": "k-pop", "energy": 0.85, "valence": 0.85}, songs, k=5)
    check("K-Pop Fan (missing genre) still returns 5 results", len(recs) == 5, f"got {len(recs)}")

    # 5. Validation clamps energy above 1.0
    prefs = _validate_prefs({"genre": "pop", "energy": 1.5})
    check("Validation clamps energy=1.5 -> 1.0", prefs["energy"] == 1.0, f"got {prefs['energy']}")

    # 6. Validation clamps energy below 0.0
    prefs = _validate_prefs({"genre": "pop", "energy": -0.3})
    check("Validation clamps energy=-0.3 -> 0.0", prefs["energy"] == 0.0, f"got {prefs['energy']}")

    # 7. Extreme values (The Void) don't crash the system
    try:
        recs = recommend_songs(
            {"genre": "ambient", "energy": 0.0, "valence": 0.0,
             "danceability": 0.0, "acousticness": 1.0},
            songs, k=5,
        )
        check("Extreme values (The Void) don't crash", len(recs) == 5, f"got {len(recs)}")
    except Exception as e:
        check("Extreme values (The Void) don't crash", False, str(e))

    # 8. All scores are non-negative
    recs = recommend_songs({"genre": "pop", "energy": 0.5}, songs, k=5)
    min_score = min(score for _, score, _ in recs)
    check("All scores are non-negative", min_score >= 0, f"min score={min_score:.2f}")

    # 9. Every result includes a non-empty explanation string
    recs = recommend_songs({"genre": "lofi", "energy": 0.3}, songs, k=3)
    all_explained = all(isinstance(exp, str) and exp.strip() for _, _, exp in recs)
    check("Every result has a non-empty explanation", all_explained)

    # 10. Top score is strictly higher than bottom score (ranking has real effect)
    recs = recommend_songs(
        {"genre": "pop", "mood": "happy", "energy": 0.8, "valence": 0.8}, songs, k=5
    )
    check(
        "Top score > bottom score (ranking has real effect)",
        recs[0][1] > recs[-1][1],
        f"top={recs[0][1]:.2f}, bottom={recs[-1][1]:.2f}",
    )

    # ── Summary ──────────────────────────────────────────────
    print("\n" + "=" * 56)
    print("  EVAL HARNESS — VibeMatch Reliability Report")
    print("=" * 56)
    for status, name, detail in results:
        suffix = f"  ({detail})" if detail else ""
        print(f"  [{status}]  {name}{suffix}")
    print("=" * 56)
    print(f"  Result: {passed}/{len(results)} tests passed")
    if passed == len(results):
        print("  All checks passed [OK]")
    else:
        print(f"  {len(results) - passed} check(s) failed [!!]")
    print("=" * 56 + "\n")

    return passed == len(results)


if __name__ == "__main__":
    success = run()
    sys.exit(0 if success else 1)
