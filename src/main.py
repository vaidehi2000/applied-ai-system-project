"""
Command line runner for the Music Recommender Simulation.
"""

import sys
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from recommender import load_songs, recommend_songs, generate_rag_explanation
from agent import run_agent

# Configure logging once at the entry point: INFO to console + persistent log file
_LOG_FILE = Path(__file__).parent.parent / "recommender.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)-8s %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(_LOG_FILE, encoding="utf-8"),
    ],
)
logger = logging.getLogger("main")

CSV_PATH = Path(__file__).parent.parent / "data" / "songs.csv"

def main() -> None:
    songs = load_songs(str(CSV_PATH))
    print(f"Loaded {len(songs)} songs\n")

    # DEMO_MODE: set to True to run only 3 profiles (saves API quota for recording)
    # Set to False to run all 9 profiles
    DEMO_MODE = False

    all_profiles = {
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

    demo_profiles = {
        "Chill Lofi": all_profiles["Chill Lofi"],
        "K-Pop Fan": all_profiles["K-Pop Fan"],
        "High-Energy Pop": all_profiles["High-Energy Pop"],
    }

    profiles = demo_profiles if DEMO_MODE else all_profiles

    for profile_name, user_prefs in profiles.items():
        logger.info("Scoring profile: %s", profile_name)
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

        # RAG: send retrieved songs to Claude for a natural-language summary
        top_songs = [song for song, _, _ in recommendations]
        ai_summary = generate_rag_explanation(user_prefs, top_songs)
        print(f"\n  AI Summary:\n  {ai_summary}\n")


def run_agent_demo(songs: list) -> None:
    """Run the agentic workflow on one clean and one adversarial profile."""
    print("\n" + "#" * 54)
    print("  AGENT MODE — Multi-Step Reasoning Demo")
    print("#" * 54)

    agent_profiles = {
        "Chill Lofi": {
            "genre": "lofi", "mood": "chill", "energy": 0.2,
        },
        "Intense Folkie": {
            "genre": "folk", "mood": "intense",
            "energy": 0.95, "valence": 0.5,
            "danceability": 0.9, "acousticness": 0.9,
        },
    }

    for profile_name, user_prefs in agent_profiles.items():
        logger.info("Running agent for profile: %s", profile_name)
        run_agent(user_prefs, songs, k=5)


if __name__ == "__main__":
    main()
    run_agent_demo(load_songs(str(CSV_PATH)))
