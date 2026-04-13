"""
Command line runner for the Music Recommender Simulation.

This file helps you quickly run and test your recommender.

You will implement the functions in recommender.py:
- load_songs
- score_song
- recommend_songs
"""

from pathlib import Path
from recommender import load_songs, recommend_songs

CSV_PATH = Path(__file__).parent.parent / "data" / "songs.csv"

def main() -> None:
    songs = load_songs(str(CSV_PATH))
    print(f"Loaded {len(songs)} songs\n")

    # Distinct user preference profiles
    profiles = {
        "High-Energy Pop": {
            "genre": "pop", "mood": "happy", "energy": 0.9,
        },
        "Chill Lofi": {
            "genre": "lofi", "mood": "chill", "energy": 0.2,
        },
        "Deep Intense Rock": {
            "genre": "rock", "mood": "angry", "energy": 0.95,
        },
        # --- Adversarial / edge-case profiles ---
        "Sad But Happy": {
            "genre": "pop", "mood": "happy",
            "energy": 0.8, "valence": 0.1,
            "danceability": 0.8, "acousticness": 0.1,
        },
        "Intense Folkie": {
            "genre": "folk", "mood": "intense",
            "energy": 0.95, "valence": 0.5,
            "danceability": 0.9, "acousticness": 0.9,
        },
        "K-Pop Fan": {
            "genre": "k-pop", "mood": "euphoric",
            "energy": 0.85, "valence": 0.85,
            "danceability": 0.9, "acousticness": 0.05,
        },
        "The Void": {
            "genre": "ambient", "mood": "chill",
            "energy": 0.0, "valence": 0.0,
            "danceability": 0.0, "acousticness": 1.0,
            "tempo_bpm": 60, "speechiness": 0.0,
        },
        "Perfectly Average": {
            "genre": "pop", "mood": "happy",
            "energy": 0.5, "valence": 0.5,
            "danceability": 0.5, "acousticness": 0.5,
            "tempo_bpm": 114, "speechiness": 0.05,
        },
        "Podcast Listener": {
            "genre": "hip-hop", "mood": "melancholic",
            "energy": 0.5, "valence": 0.4,
            "danceability": 0.5, "acousticness": 0.1,
            "speechiness": 1.0,
        },
    }

    for profile_name, user_prefs in profiles.items():
        recommendations = recommend_songs(user_prefs, songs, k=5)

        print("=" * 54)
        print(f"  PROFILE: {profile_name}")
        print("=" * 54)

        for i, (song, score, explanation) in enumerate(recommendations, start=1):
            print(f"\n#{i}  {song['title']} by {song['artist']}")
            print(f"    Genre: {song['genre']}  |  Mood: {song['mood']}")
            print(f"    Score: {score:.2f} / 9.00")
            print("    Why:")
            for reason in explanation.split(" | "):
                print(f"      • {reason}")
            print("    " + "-" * 46)

        print()


if __name__ == "__main__":
    main()
