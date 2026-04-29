# 🎵 VibeMatch — Applied AI Music Recommender

## Base Project

This project extends the **Music Recommender Simulation** built in Modules 1–3 of CodePath AI110. The original project's goal was to simulate how content-based filtering works by scoring songs against a user's taste profile using weighted proximity math. It produced ranked recommendations with plain-language explanations and documented its own biases through a model card. It had no AI API integration, no input validation, and no logging.

---

## What This Extension Adds

| Feature | What it does |
|---|---|
| **RAG (Retrieval-Augmented Generation)** | Top scored songs are retrieved and sent to Gemini as context. Gemini generates a natural-language summary grounded in those specific songs — not a generic response. |
| **Input Validation / Guardrails** | `_validate_prefs()` checks every user preference before scoring. Out-of-range values are clamped (e.g. `energy=1.5` → `1.0`) and a warning is logged. |
| **Structured Logging** | INFO and WARNING lines track every key event — songs loaded, profile scored, genre not found in catalog, API key missing, AI call succeeded or failed. Persisted to `recommender.log`. |
| **Implemented Recommender class** | `Recommender.recommend()` and `Recommender.explain_recommendation()` are now fully functional, not stubs. |
| **Expanded adversarial testing** | 6 edge-case profiles deliberately expose system failure modes (missing genre, conflicting signals, extreme values). |

---

## How The System Works

Real-world recommenders like Spotify and YouTube combine collaborative filtering (what similar users listened to) and content-based filtering (what the song itself sounds like). This simulation focuses on the content-based side — it builds a taste profile from a user's stated preferences and scores every song by how closely its audio features match. The priority is transparency: every recommendation includes a plain-language reason, and Gemini adds a natural-language summary grounded in the actual retrieved songs.

### Song Features

| Feature | Type | What it captures |
|---|---|---|
| `genre` | str | Musical category (e.g. lofi, pop, rock) |
| `mood` | str | Emotional feel (e.g. chill, happy, intense) |
| `energy` | float (0–1) | Calm vs. intense — highest-weight numeric feature |
| `tempo_bpm` | float | Speed in BPM (normalized before scoring) |
| `valence` | float (0–1) | Sad vs. happy emotional tone |
| `danceability` | float (0–1) | How suitable the song is for dancing |
| `acousticness` | float (0–1) | Acoustic vs. electronic production |

### Scoring Rule

```
score = +1.0  (if song.genre == user.favorite_genre)
      + 3.0 × (1 - |user.energy       - song.energy|)
      + 1.0 × (1 - |user.danceability - song.danceability|)
      + 1.0 × (1 - |user.valence      - song.valence|)
      + 1.0 × (1 - |user.acousticness - song.acousticness|)
      + 1.0 × (1 - |user.tempo_norm   - song.tempo_norm|)
      + 0.5 × (1 - |user.speechiness  - song.speechiness|)
```

Tempo is normalized to 0–1 before scoring using `(bpm - 60) / (168 - 60)`.

---

## System Architecture

```mermaid
flowchart TD
    A([User Profile\ngenre · mood · numeric targets]) --> V
    B([songs.csv\n20 songs]) --> C[Load songs into memory\nload_songs]

    V["Input Validation\n_validate_prefs\nclamp out-of-range values\nwarn on missing fields"]
    A --> V
    V --> D

    C --> D[Score every song\nscore_songs]

    D --> F[Categorical bonus\n+1.0 genre match]
    F --> G[Numeric proximity\nenergy ×3.0\ndanceability · valence\nacousticness · tempo ×1.0\nspeechiness ×0.5]
    G --> H[Sum → total score\nattach explanation string]
    H --> D2{All songs\nscored?}
    D2 -- No, next song --> D
    D2 -- Yes --> K[Sort descending\nslice top K]

    K --> M([CLI Output\nRanked songs + scores\n+ plain-language reasons])
    K --> R[RAG Step\nTop K songs retrieved\nas context]

    R --> AI[Gemini API\ngemini-2.5-flash\nGenerates 2-3 sentence\nnatural-language summary\ngrounded in retrieved songs]
    AI --> AIS([AI Summary\nappended to CLI output])

    LOG[Logging\nINFO: songs loaded · profile scoring · AI success\nWARNING: missing genre · sparse catalog · no API key\nERROR: API failure]
    V -.->|guardrail events| LOG
    D -.->|scoring events| LOG
    AI -.->|API events| LOG

    TEST[Test Suite\npytest · test_recommender.py\nVerifies recommend sorts by score\nVerifies explain returns non-empty string\n9 adversarial profiles run in main.py]
    M -.->|human review of results| TEST
```

> For an interactive version open [`flowchart.html`](flowchart.html) in a browser.

**Data flow summary:**
User Profile → Input Validation → Score every song → Sort/Rank → CLI Output + RAG (Gemini) → AI Summary. Logging runs throughout all steps. pytest verifies core logic independently.

---

## Setup Instructions

### 1. Clone the repository

```bash
git clone https://github.com/vaidehi2000/applied-ai-system-project.git
cd applied-ai-system-project
```

### 2. Create and activate a virtual environment

```bash
python -m venv .venv

# Mac / Linux
source .venv/bin/activate

# Windows
.venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Add your Gemini API key

Create a `.env` file in the project root:

```
GEMINI_API_KEY=your-key-here
```

> The system runs without an API key — scoring and ranking work normally. Only the AI summary step will be skipped with a warning logged.

### 5. Run the recommender

```bash
python -m src.main
```

### 6. Run the tests

```bash
pytest
```

---

## Sample Interactions

### Example 1 — High-Energy Pop

**Input:**
```python
{"genre": "pop", "mood": "happy", "energy": 0.9}
```

**Output:**
```
#1  Gym Hero by Max Pulse
    Genre: pop  |  Mood: intense
    Score: 3.91 / 9.00
      • Matches your favorite genre (pop)
      • Energy match: 0.97/1.00 (song=0.93, you=0.9)

#2  Sunrise City by Neon Echo
    Genre: pop  |  Mood: happy
    Score: 3.76 / 9.00
      • Matches your favorite genre (pop)
      • Energy match: 0.92/1.00 (song=0.82, you=0.9)

#3  Storm Runner by Voltline
    Genre: rock  |  Mood: intense
    Score: 2.97 / 9.00
      • Energy match: 0.99/1.00 (song=0.91, you=0.9)

  AI Summary:
  These recommendations align well with your high-energy pop preference. Gym Hero
  and Sunrise City both match your genre and deliver the intense, driving energy
  you're looking for, while Storm Runner earns its spot purely through its near-
  perfect energy match despite being rock.
```

---

### Example 2 — Chill Lofi

**Input:**
```python
{"genre": "lofi", "mood": "chill", "energy": 0.2}
```

**Output:**
```
#1  Library Rain by Paper Lanterns
    Genre: lofi  |  Mood: chill
    Score: 3.55 / 9.00
      • Matches your favorite genre (lofi)
      • Energy match: 0.85/1.00 (song=0.35, you=0.2)

#2  Focus Flow by LoRoom
    Genre: lofi  |  Mood: focused
    Score: 3.40 / 9.00
      • Matches your favorite genre (lofi)
      • Energy match: 0.80/1.00 (song=0.40, you=0.2)

#3  Midnight Coding by LoRoom
    Genre: lofi  |  Mood: chill
    Score: 3.34 / 9.00
      • Matches your favorite genre (lofi)
      • Energy match: 0.78/1.00 (song=0.42, you=0.2)

  AI Summary:
  All three picks are lofi tracks with low energy and high acousticness, matching
  your calm study-session vibe. Library Rain edges ahead because its energy of 0.35
  sits closest to your target of 0.2 among the lofi options in the catalog.
```

---

### Example 3 — K-Pop Fan *(adversarial)*

**Input:**
```python
{"genre": "k-pop", "mood": "euphoric", "energy": 0.85, "valence": 0.85, "danceability": 0.9, "acousticness": 0.05}
```

**Output:**
```
WARNING  Genre 'k-pop' not found in catalog — falling back to numeric-only scoring

#1  Sunrise City by Neon Echo
    Genre: pop  |  Mood: happy
    Score: 5.66 / 9.00
      • Energy match: 0.97/1.00 (song=0.82, you=0.85)

#2  Gym Hero by Max Pulse
    Genre: pop  |  Mood: intense
    Score: 5.66 / 9.00
      • Energy match: 0.92/1.00 (song=0.93, you=0.85)

#3  Drop Zone by Bassline Cult
    Genre: edm  |  Mood: euphoric
    Score: 5.55 / 9.00
      • Energy match: 0.90/1.00 (song=0.95, you=0.85)

  AI Summary:
  Since k-pop isn't represented in the catalog, the system fell back to numeric
  matching. These pop and EDM tracks share the high energy and danceability of
  k-pop, though the genre gap means this listener may not recognize these as
  satisfying substitutes.
```

> This example demonstrates the guardrail in action: the WARNING surfaces the silent failure instead of returning confusing results without explanation.

---

## Design Decisions

**Why energy gets 3× weight:**
Energy is the most immediately felt quality in music. A calm person hearing an intense song is the most jarring possible mismatch — more so than a tempo or danceability gap. The 3× weight reflects that.

**Why genre bonus is 1.0, not 2.0:**
The original base project used +2.0 for genre. Through adversarial testing, this caused the only folk song in the catalog ("Pine & Candle") to rank #1 for an Intense Folkie profile even though its energy was 0.31 against a target of 0.95. Halving the genre bonus reduces this without eliminating it entirely.

**Why mood bonus is disabled:**
Mood labels are exact string matches. "Intense" and "angry" feel emotionally close but score zero similarity. During experiments, enabling mood bonus produced worse results than disabling it for several adversarial profiles. A future fix would use semantic similarity rather than exact strings.

**Why RAG instead of a standalone AI call:**
The Gemini prompt is grounded in the actual retrieved songs, not a general description of the user profile. This means the AI summary references specific titles and attributes rather than generating generic advice — which is the point of RAG.

**Why clamp instead of reject on bad input:**
The system should degrade gracefully. If a UI passes `energy=1.2`, crashing is worse than clamping to `1.0` and warning. The guardrail logs the problem without breaking the user experience.

---

## Testing Summary

Nine profiles were tested in total — three standard (High-Energy Pop, Chill Lofi, Deep Intense Rock) and six adversarial designed to expose failure modes. The standard profiles mostly behaved as expected: Chill Lofi returned three lofi tracks in its top results, and High-Energy Pop correctly ranked "Gym Hero" and "Sunrise City" at the top. Deep Intense Rock also made sense — rock songs and high-energy metal tracks dominated, which matched the intent.

The adversarial profiles were where things got interesting. The most striking failure was the Intense Folkie profile: a user asking for folk music with energy 0.95 got "Pine & Candle" — the calmest folk song in the catalog with energy 0.31 — as their top recommendation. The system wasn't broken; it followed its rules exactly. The genre bonus was just strong enough to outrank every numeric signal. The K-Pop Fan profile showed a different problem: when a genre doesn't exist in the catalog, the system silently fell back to numeric scoring with no explanation to the user. Before we added the logging guardrail, there was no way to know that happened. The Sad But Happy profile (mood: happy, valence: 0.1) also showed that conflicting categorical and numeric signals produce confusing output — the mood bonus drowned out the valence preference entirely.

If I had more time, I'd fix the genre bonus first — scaling it down when only one or two songs of that genre exist in the catalog. That single change would fix the Intense Folkie and K-Pop Fan failures simultaneously. After that, I'd add a conflict warning when a user's mood and valence settings clearly contradict each other.

---

## Reflection

The most important thing this project taught me is that a system can be completely correct and completely wrong at the same time. When "Pine & Candle" ranked first for the Intense Folkie profile, the code did exactly what it was supposed to do — it followed the scoring rules perfectly. The problem was in the assumptions behind the design, not in the implementation. That gap between "the code runs" and "the system works" is something I now think about every time I look at any AI output.

Building this changed how I think about real recommenders like Spotify and TikTok. I used to assume that when an app recommended something unexpected, it had learned something subtle about my taste. Now I suspect it might just be a weighting artifact — some feature I accidentally signaled strongly that pulled results in a direction I didn't intend. The output always looks confident. Confidence is not the same as correctness, and formatted output makes it very hard to tell the difference.

AI tools were genuinely helpful during development — particularly for spotting cross-profile patterns at once. When I asked Copilot to analyze all nine profiles together, it identified that energy was dominating rankings across three different profiles for different reasons, which I hadn't noticed by looking at them individually. The flawed suggestion came when the AI predicted what *should* happen for the Sad But Happy profile before I ran the code — its prediction was reasonable but wrong, because the categorical bonuses overpowered the numeric signals more than expected. That taught me to verify outputs rather than trust predictions, even when the reasoning sounds solid. Human judgment still matters most at the moment of interpreting results — the model tells you what happened, but deciding whether that's acceptable requires understanding the context the model doesn't have.


## Profile Results

### High-Energy Pop
![PROFILE High-Energy Pop](screenshots/PROFILE%20High-Energy%20Pop.png)

### Chill Lofi
![PROFILE Chill Lofi](screenshots/PROFILE%20Chill%20Lofi.png)

### Deep Intense Rock
![PROFILE Deep Intense Rock](screenshots/PROFILE%20Deep%20Intense%20Rock.png)

### Sad But Happy *(adversarial)*
![PROFILE Sad But Happy](screenshots/PROFILE%20Sad%20But%20Happy.png)

### Intense Folkie *(adversarial)*
![PROFILE Intense Folkie](screenshots/PROFILE%20Intense%20Folkie.png)

### K-Pop Fan *(adversarial)*
![PROFILE Kpop Fan](screenshots/PROFILE%20Kpop%20Fan.png)

### The Void *(adversarial)*
![PROFILE The Void](screenshots/PROFILE%20The%20Void.png)

### Perfectly Average *(adversarial)*
![PROFILE Perfectly Average](screenshots/PROFILE%20Perfectly%20Average.png)

### Podcast Listener *(adversarial)*
![PROFILE Podcast Listener](screenshots/PROFILE%20Podcast%20Listener.png)

---

## Known Limitations

- Catalog is 20 songs — rare genres (folk, ambient) have 1–2 songs, so the genre bonus dominates for those profiles
- Mood matching is exact string only — "euphoric" and "happy" score zero similarity despite being emotionally close
- No diversity enforcement — top 5 can all be the same genre
- K-pop, Latin, Afrobeats, and non-Western genres are absent from the catalog

See [`model_card.md`](model_card.md) for a full bias analysis.
