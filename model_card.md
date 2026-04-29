# 🎧 Model Card: Music Recommender Simulation

## 1. Model Name

**SongPicker 1.0**

---

## 2. Intended Use

SongPicker is designed to suggest songs from a small catalog based on a user's stated preferences: their favorite genre, the mood they want, and how energetic they want the music to feel.

It is built for classroom exploration. It is not meant for real users on a real platform. It assumes the user can describe their taste in simple terms like "I want chill lofi" or "I want high-energy pop." It does not learn from listening history and it does not know anything about a user beyond what they tell it directly.

**Not intended for:** production music apps, personalized recommendations based on behavior, or any use case with real users who expect accurate results.

---

## 3. How the Model Works

Every song in the catalog gets a score. The score measures how closely the song matches what the user said they want.

There are two types of signals:

**Categorical bonuses**: if the song's genre matches the user's favorite genre, it gets a bonus. Same for mood. These are all-or-nothing: either it matches or it does not.

**Numeric proximity**: for features like energy, danceability, and emotional tone (valence), the system measures the gap between what the user wants and what the song actually sounds like. A smaller gap means a higher score. For example, if you want high energy (1.0) and the song has energy 0.9, that is a great match. If the song has energy 0.2, that is a poor match.

Energy is weighted more heavily than other features because it is the most immediately noticeable quality. Playing a calm song for someone who wanted intense music is the worst mismatch. Tempo is normalized before scoring so it stays on the same scale as everything else.

After every song is scored, they are sorted from highest to lowest and the top 5 are returned.

---

## 4. Data

The catalog has 20 songs. Each song has the following features: genre, mood, energy, tempo, valence (how happy or sad it sounds), danceability, acousticness, and speechiness.

The genres represented are: pop, lofi, rock, ambient, jazz, synthwave, indie pop, r&b, hip-hop, classical, country, metal, blues, reggae, edm, folk, and dreampop.

The catalog is not balanced. Some genres have 3 songs (lofi), some have 1 (edm, folk, metal, reggae, blues). No songs were added or removed from the original dataset.

The data reflects a fairly mainstream, Western listening palette. There is no K-pop, Latin, Afrobeats, or classical non-Western music. Users whose taste falls outside these genres will get poor results.

---

## 5. Strengths

The system works best when the user's favorite genre is well-represented in the catalog and their preferences do not conflict with each other.

The Chill Lofi profile worked very well. It returned three lofi tracks in the top 4, and the one non-lofi result ("Spacewalk Thoughts") is genuinely similar in feel. The High-Energy Pop profile also behaved sensibly, with "Sunrise City" and "Gym Hero" at the top.

The scoring is transparent. Every recommendation comes with a plain-language reason, so a user can see exactly why a song was chosen. Most real recommenders do not offer that.

---

## 6. Limitations and Bias

The most significant weakness discovered during experiments is that the genre bonus disproportionately controls rankings, regardless of how well a song actually matches the user's sonic preferences. During the "Intense Folkie" adversarial test, "Pine & Candle", a quiet nostalgic folk track with an energy score of 0.31, ranked first for a user who explicitly wanted energy 0.95, purely because it was the only folk song that triggered the genre bonus. This means a user asking for intense, high-energy music was handed the calmest song in the catalog as their top recommendation. The problem is structural: categorical bonuses are fixed point values that do not scale with how well the rest of the song fits, so a single genre match can overpower every numeric signal combined. Until the genre bonus is weighted relative to catalog density, giving less credit when only one song of that genre exists, the system will consistently mislead users whose favorite genre is rare in the dataset.

Additional biases:
- **Ghost genre problem:** If your favorite genre is not in the catalog (e.g. K-Pop), the system silently ignores that preference with no warning and falls back to numeric scoring only.
- **Conflicting preferences are invisible:** Setting `mood: happy` and `valence: 0.1` at the same time produces no conflict warning. The mood bonus wins and the valence preference is effectively ignored.
- **Energy creates a filter bubble:** With energy weighted at ×3.0, high-energy users almost never see calm songs and low-energy users almost never see intense ones, regardless of whether the rest of the song would suit them.

---

## 7. Evaluation

Nine user profiles were tested in total: three standard profiles (High-Energy Pop, Chill Lofi, Deep Intense Rock) and six adversarial ones designed to expose weaknesses in the scoring logic (Sad But Happy, Intense Folkie, K-Pop Fan, The Void, Perfectly Average, Podcast Listener). For each profile, the top 5 recommendations were inspected to check whether they matched what a reasonable listener would actually want.

The standard profiles behaved largely as expected: Chill Lofi surfaced lofi tracks, and High-Energy Pop correctly ranked "Sunrise City" and "Gym Hero" at the top. The surprises came entirely from the adversarial profiles. The most striking result was the Sad But Happy profile, which set `mood: happy` but `valence: 0.1`, intentionally conflicting signals. Despite the contradiction, "Sunrise City" (valence=0.84) still scored 6.64 out of 9, because the genre and mood bonuses completely drowned out the valence penalty. The system showed no sign of the conflict; it behaved as if the valence preference did not exist.

The K-Pop Fan profile confirmed a different failure mode: when a user's favorite genre is absent from the catalog entirely, the system silently falls back to numeric-only scoring with no warning. "Drop Zone" (EDM) was recommended to a K-Pop listener purely because its energy and danceability were close matches, a result that would confuse any real user. Two sensitivity experiments were also run: doubling the energy weight to ×3.0 and halving the genre bonus to 1.0, then separately commenting out the mood check. The weight shift caused the Intense Folkie result to partially correct itself, but the K-Pop Fan and Sad But Happy profiles were nearly unchanged, confirming that energy already dominated those rankings before the shift.

---

## 8. Future Work

1. **Scale the genre bonus by catalog density.** If only one song of a given genre exists, the genre bonus should be smaller, not the same as a genre with ten songs. This would stop a single label match from overriding everything else.

2. **Add a "no match found" warning.** If the user's favorite genre does not appear in the catalog at all, the system should say so instead of silently returning unrelated results. A simple check before scoring would be enough.

3. **Add diversity enforcement.** Right now the top 5 can all be from the same genre. A real recommender would ensure variety. For example, no more than 2 songs from the same genre in the top 5, so the user gets a broader sense of what matches their vibe.

---

## 9. Ethics and Responsible Use

**Could this system be misused, and how would you prevent it?**

This is a classroom project with 20 songs, so direct misuse is not a realistic concern here. But the failure modes in this system map directly to real problems at production scale. The K-Pop Fan case is the clearest example: the system ignored the genre preference entirely and returned EDM recommendations instead, with no indication that anything went wrong. The output looked identical to a genuine match, with the same format, same scores, and same explanations. At scale, that kind of silent failure could be used to push users toward catalog content a platform wants to promote rather than what the user actually asked for. The user would have no way to tell the difference.

The most practical prevention is making failures visible. The logging guardrail added in this version (`WARNING: Genre 'k-pop' not found in catalog`) is a step in that direction, but the warning only appears in a log file. In a real system it would need to surface in the interface. The other problem is filter bubbles: with energy weighted at 3x, high-energy users almost never see calm songs and vice versa. That is not a bug, it is a design choice, but it would need to be intentional and documented in a real product rather than just being a side effect of the weights.

**What surprised you while testing reliability?**

What surprised me most was that the broken results looked exactly like the correct ones. I expected the failed profiles to produce obviously wrong output, like strange scores, missing results, or something that would flag itself. That did not happen. The K-Pop Fan got a clean, formatted list of five songs with scores and explanations, and nothing in that output showed that the genre preference was never matched. It looked just as authoritative as the Chill Lofi results that were genuinely good. The system does not crash when something goes wrong. It just returns confident-looking output regardless. That is what the adversarial profiles were designed to test, and running them made it very clear that you cannot tell whether a recommender is working correctly just by looking at the results.

---

## 10. Personal Reflection

**Biggest learning moment**

The biggest learning moment was the "Pine & Candle" result. A quiet acoustic folk song ranked first for a user who explicitly asked for maximum energy, just because it was the only folk song in the catalog. The system was not broken. It was doing exactly what the code said. That was the unsettling part. It made me realize that a recommender can follow its rules perfectly and still give a completely wrong answer. The bug was not in the code; it was in the assumptions behind the design.

**How AI tools helped, and when I needed to double-check**

Using Claude to run the adversarial profiles and analyze the scoring logic saved a lot of time I would have spent manually tracing through the math. It was especially useful for spotting patterns across all nine profiles at once, like noticing that energy was dominating three different profiles for different reasons. That kind of cross-profile pattern is hard to see when you are looking at one result at a time. Where I needed to double-check was when the AI described what *should* happen versus what the code *actually* does. For example, it correctly predicted that the Sad But Happy profile would show conflicting signals, but I still needed to run the code myself to see the actual scores and confirm that the valence preference truly had almost no effect. Predictions and outputs are not the same thing.

**What surprised me about simple algorithms feeling like recommendations**

The most surprising thing was how convincing the output looked even when the logic was wrong. When the system returned "Sunrise City" and "Gym Hero" for a happy pop listener, it felt right. Those are genuinely good matches. It was easy to trust the list. The problem is that the same confidence in the output showed up for the broken profiles too. The K-Pop Fan got a clean, formatted list of five songs with scores and explanations, and nothing in that output signaled that the genre preference was completely ignored. A real user would have no reason to question it. That is what makes simple scoring feel like intelligence: it is always decisive, and decisiveness reads as confidence even when it should not.

**What I would try next**

If I extended this project, the first thing I would do is make the genre bonus smarter. I would scale it down when only one or two songs of that genre exist, so a rare genre match cannot overpower everything else. Second, I would add a warning message when a user's favorite genre has zero songs in the catalog, rather than silently falling back to numeric scoring. Third, I would experiment with a diversity rule that prevents the top 5 from being dominated by a single genre, so users get a broader set of options even when one genre scores consistently well. All three of these changes came directly from watching the system fail, which is probably the most useful thing this project taught me about how to improve any system: run it until it breaks, then fix what you learned.
