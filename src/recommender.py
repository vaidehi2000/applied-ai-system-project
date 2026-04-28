from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

@dataclass
class Song:
    """
    Represents a song and its attributes.
    Required by tests/test_recommender.py
    """
    id: int
    title: str
    artist: str
    genre: str
    mood: str
    energy: float
    tempo_bpm: float
    valence: float
    danceability: float
    acousticness: float

@dataclass
class UserProfile:
    """
    Represents a user's taste preferences.
    Required by tests/test_recommender.py

    Numeric targets (0.0–1.0) are used in proximity scoring:
        feature_score = 1 - |target - song.feature|
    Categorical fields (genre, mood) add bonus points on match.
    """
    name: str
    favorite_genre: str
    favorite_mood: str
    # Numeric taste targets — each maps directly to a Song feature
    target_energy: float        # 0=calm, 1=intense
    target_valence: float       # 0=sad, 1=happy
    target_danceability: float  # 0=still, 1=danceable
    target_acousticness: float  # 0=electronic, 1=acoustic
    target_speechiness: float   # 0=instrumental, 1=spoken
    target_tempo_bpm: float     # raw BPM (normalized before scoring)


# ---------------------------------------------------------------------------
# Predefined taste profiles as dicts — used by recommend_songs() in main.py
#
# Keys mirror Song field names so scoring can do:
#   score += 1 - abs(profile[key] - song[key])  for each numeric key
# ---------------------------------------------------------------------------

PROFILE_LATE_NIGHT_STUDIER: Dict = {
    "name": "Late Night Studier",
    # Categorical — matched for bonus points, not distance
    "favorite_genre": "lofi",
    "favorite_mood":  "chill",
    # Numeric targets — derived from avg of lofi songs in dataset
    "target_energy":        0.38,   # very calm
    "target_valence":       0.58,   # neutral-positive
    "target_danceability":  0.60,   # mild movement ok
    "target_acousticness":  0.78,   # strongly acoustic/warm
    "target_speechiness":   0.03,   # no vocals preferred
    "target_tempo_bpm":     77.0,   # slow, ~walking pace
}

PROFILE_WORKOUT_BEAST: Dict = {
    "name": "Workout Beast",
    "favorite_genre": "edm",
    "favorite_mood":  "intense",
    "target_energy":        0.94,   # near maximum
    "target_valence":       0.74,   # pumped, positive
    "target_danceability":  0.89,   # highly rhythmic
    "target_acousticness":  0.05,   # electronic only
    "target_speechiness":   0.06,   # minimal vocals fine
    "target_tempo_bpm":     138.0,  # fast, driving beat
}

PROFILE_SUNDAY_ACOUSTIC: Dict = {
    "name": "Sunday Acoustic",
    "favorite_genre": "folk",
    "favorite_mood":  "nostalgic",
    "target_energy":        0.35,   # quiet and calm
    "target_valence":       0.67,   # warm but not euphoric
    "target_danceability":  0.47,   # gentle sway at most
    "target_acousticness":  0.90,   # strongly acoustic
    "target_speechiness":   0.07,   # some vocals ok
    "target_tempo_bpm":     94.0,   # leisurely
}

# Dataclass versions — kept for Recommender class and test compatibility
PROFILE_LATE_NIGHT_STUDIER_OBJ = UserProfile(
    name="Late Night Studier",
    favorite_genre="lofi",
    favorite_mood="chill",
    target_energy=0.38,
    target_valence=0.58,
    target_danceability=0.60,
    target_acousticness=0.78,
    target_speechiness=0.03,
    target_tempo_bpm=77.0,
)

PROFILE_WORKOUT_BEAST_OBJ = UserProfile(
    name="Workout Beast",
    favorite_genre="edm",
    favorite_mood="intense",
    target_energy=0.94,
    target_valence=0.74,
    target_danceability=0.89,
    target_acousticness=0.05,
    target_speechiness=0.06,
    target_tempo_bpm=138.0,
)

PROFILE_SUNDAY_ACOUSTIC_OBJ = UserProfile(
    name="Sunday Acoustic",
    favorite_genre="folk",
    favorite_mood="nostalgic",
    target_energy=0.35,
    target_valence=0.67,
    target_danceability=0.47,
    target_acousticness=0.90,
    target_speechiness=0.07,
    target_tempo_bpm=94.0,
)

class Recommender:
    """
    OOP implementation of the recommendation logic.
    Required by tests/test_recommender.py
    """
    def __init__(self, songs: List[Song]):
        self.songs = songs

    def recommend(self, user: UserProfile, k: int = 5) -> List[Song]:
        # TODO: Implement recommendation logic
        return self.songs[:k]

    def explain_recommendation(self, user: UserProfile, song: Song) -> str:
        # TODO: Implement explanation logic
        return "Explanation placeholder"

def load_songs(csv_path: str) -> List[Dict]:
    """Read songs.csv and return a list of dicts with numeric fields cast to int or float."""
    import csv

    int_fields   = {"id"}
    float_fields = {"energy", "tempo_bpm", "valence", "danceability",
                    "acousticness", "speechiness", "instrumentalness"}

    songs = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            for field in int_fields:
                if field in row:
                    row[field] = int(row[field])
            for field in float_fields:
                if field in row:
                    row[field] = float(row[field])
            songs.append(row)
    return songs

def score_songs(user_prefs: Dict, songs: List[Dict], k: int = 5) -> List[Tuple[Dict, float, str]]:
    """Score every song against user preferences and return all (song, score, explanation) tuples."""
    TEMPO_MIN, TEMPO_MAX = 60, 168  # BPM range across catalog

    scored = []

    for song in songs:
        score = 0.0
        reasons = []

        # --- Categorical bonuses ---
        # WEIGHT SHIFT TEST: genre halved (2.0 -> 1.0), energy doubled (1.5 -> 3.0)
        if song.get("genre") == user_prefs.get("genre"):
            score += 1.0
            reasons.append(f"Matches your favorite genre ({song['genre']})")

        # FEATURE REMOVAL TEST: mood check disabled to observe ranking sensitivity
        # if song.get("mood") == user_prefs.get("mood"):
        #     score += 1.0
        #     reasons.append(f"Matches your preferred mood ({song['mood']})")

        # --- Numeric proximity scores ---
        if "energy" in user_prefs:
            energy_score = 1 - abs(user_prefs["energy"] - song["energy"])
            score += 3.0 * energy_score
            reasons.append(f"Energy match: {energy_score:.2f}/1.00 (song={song['energy']}, you={user_prefs['energy']})")

        if "danceability" in user_prefs:
            dance_score = 1 - abs(user_prefs["danceability"] - song["danceability"])
            score += 1.0 * dance_score

        if "valence" in user_prefs:
            valence_score = 1 - abs(user_prefs["valence"] - song["valence"])
            score += 1.0 * valence_score

        if "acousticness" in user_prefs:
            acoustic_score = 1 - abs(user_prefs["acousticness"] - song["acousticness"])
            score += 1.0 * acoustic_score

        if "tempo_bpm" in user_prefs:
            user_tempo_norm = (user_prefs["tempo_bpm"] - TEMPO_MIN) / (TEMPO_MAX - TEMPO_MIN)
            song_tempo_norm = (song["tempo_bpm"] - TEMPO_MIN) / (TEMPO_MAX - TEMPO_MIN)
            tempo_score = 1 - abs(user_tempo_norm - song_tempo_norm)
            score += 1.0 * tempo_score

        if "speechiness" in user_prefs:
            speech_score = 1 - abs(user_prefs["speechiness"] - song["speechiness"])
            score += 0.5 * speech_score

        explanation = " | ".join(reasons) if reasons else "Close numeric match to your taste profile"
        scored.append((song, score, explanation))

    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:k]


def recommend_songs(user_prefs: Dict, songs: List[Dict], k: int = 5) -> List[Tuple[Dict, float, str]]:
    """Return the top-k songs sorted by score descending using score_songs."""
    return sorted(score_songs(user_prefs, songs), key=lambda x: x[1], reverse=True)[:k]

def generate_rag_explanation(user_prefs: Dict, top_songs: List[Dict]) -> str:
    """
    RAG step: retrieve the top songs (already scored), then send them to Claude
    to generate a natural-language explanation grounded in that retrieved data.
    """
    import os
    from dotenv import load_dotenv
    import anthropic

    load_dotenv()
    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

    # Format retrieved songs into a readable block for the prompt
    song_lines = []
    for i, song in enumerate(top_songs, 1):
        song_lines.append(
            f"{i}. \"{song['title']}\" by {song['artist']} "
            f"(genre={song['genre']}, mood={song['mood']}, "
            f"energy={song['energy']}, valence={song['valence']})"
        )
    retrieved = "\n".join(song_lines)

    # Build a concise user preference summary
    prefs_summary = ", ".join(f"{k}={v}" for k, v in user_prefs.items())

    prompt = (
        f"A music listener has these preferences: {prefs_summary}.\n\n"
        f"Based only on the following songs retrieved from the catalog:\n{retrieved}\n\n"
        f"In 2-3 sentences, explain why these songs are a good match for this listener. "
        f"Be specific — reference the song titles and their attributes."
    )

    try:
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=256,
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text
    except Exception as e:
        return f"[AI summary unavailable: {e}]"
