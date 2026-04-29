"""
Agentic recommendation workflow with observable intermediate steps.

The agent runs four steps for a given user profile:
  STEP 1 - ANALYZE   : Inspect preferences for issues (missing genre, conflicts, extremes)
  STEP 2 - RETRIEVE  : Score catalog and fetch top-K songs
  STEP 3 - VERIFY    : Check whether results actually match intent
  STEP 4 - EXPLAIN   : Generate AI summary grounded in retrieved songs + analysis context
"""

import logging
from typing import Dict, List, Tuple

logger = logging.getLogger("agent")


def _analyze(user_prefs: Dict, songs: List[Dict]) -> List[str]:
    """STEP 1: Identify potential issues with the user profile before scoring."""
    issues = []

    user_genre = user_prefs.get("genre", "")
    if user_genre:
        genre_count = sum(1 for s in songs if s.get("genre") == user_genre)
        if genre_count == 0:
            issues.append(f"genre '{user_genre}' is absent from catalog — numeric-only fallback will be used")
        elif genre_count <= 2:
            issues.append(f"genre '{user_genre}' has only {genre_count} song(s) — genre bonus may dominate")

    energy = user_prefs.get("energy")
    valence = user_prefs.get("valence")
    if energy is not None and valence is not None:
        if energy >= 0.8 and valence <= 0.3:
            issues.append("high energy + low valence — intense but sad, potential conflicting signal")
        if energy <= 0.2 and valence >= 0.8:
            issues.append("low energy + high valence — calm but very happy, unusual combination")

    mood = user_prefs.get("mood", "")
    if mood and valence is not None:
        happy_moods = {"happy", "euphoric", "romantic"}
        sad_moods = {"melancholic", "sad", "angry"}
        if mood in happy_moods and valence <= 0.3:
            issues.append(f"mood='{mood}' conflicts with valence={valence} — categorical bonus may override numeric intent")
        if mood in sad_moods and valence >= 0.8:
            issues.append(f"mood='{mood}' conflicts with valence={valence} — categorical bonus may override numeric intent")

    return issues


def _verify(user_prefs: Dict, recommendations: List[Tuple]) -> List[str]:
    """STEP 3: Check whether the top result actually matches user intent."""
    warnings = []

    if not recommendations:
        warnings.append("no results returned")
        return warnings

    top_song, top_score, _ = recommendations[0]

    energy_target = user_prefs.get("energy")
    if energy_target is not None:
        energy_gap = abs(energy_target - top_song.get("energy", 0))
        if energy_gap > 0.4:
            warnings.append(
                f"top result '{top_song['title']}' has energy={top_song['energy']} "
                f"but target is {energy_target} (gap={energy_gap:.2f}) — poor energy match"
            )

    user_genre = user_prefs.get("genre", "")
    if user_genre:
        top_genre = top_song.get("genre", "")
        if top_genre != user_genre:
            warnings.append(
                f"top result '{top_song['title']}' is {top_genre}, not {user_genre} — genre bonus did not win"
            )

    genres_in_top5 = [s.get("genre") for s, _, _ in recommendations]
    if len(set(genres_in_top5)) == 1:
        warnings.append(f"all top results are the same genre ({genres_in_top5[0]}) — no diversity in results")

    return warnings


def run_agent(user_prefs: Dict, songs: List[Dict], k: int = 5) -> Tuple[List, str]:
    """
    Run the 4-step agentic workflow. Prints each step so intermediate reasoning is visible.
    Returns (recommendations, ai_summary).
    """
    import os
    from dotenv import load_dotenv
    from recommender import recommend_songs

    profile_label = user_prefs.get("genre", "unknown") + "/" + user_prefs.get("mood", "unknown")

    print(f"\n  {'='*50}")
    print(f"  AGENT WORKFLOW — {profile_label}")
    print(f"  {'='*50}")

    # ── STEP 1: ANALYZE ──────────────────────────────────────
    print("\n  [STEP 1: ANALYZE] Inspecting user preferences...")
    issues = _analyze(user_prefs, songs)
    if issues:
        for issue in issues:
            print(f"    ! {issue}")
        logger.warning("Agent analysis flagged %d issue(s) for profile '%s'", len(issues), profile_label)
    else:
        print("    No issues detected — preferences look consistent")
    logger.info("Agent STEP 1 complete: %d issue(s) found", len(issues))

    # ── STEP 2: RETRIEVE ─────────────────────────────────────
    print("\n  [STEP 2: RETRIEVE] Scoring catalog and fetching top songs...")
    recommendations = recommend_songs(user_prefs, songs, k=k)
    top_titles = [s["title"] for s, _, _ in recommendations]
    print(f"    Retrieved: {top_titles}")
    logger.info("Agent STEP 2 complete: retrieved %d songs", len(recommendations))

    # ── STEP 3: VERIFY ───────────────────────────────────────
    print("\n  [STEP 3: VERIFY] Checking result quality...")
    verify_warnings = _verify(user_prefs, recommendations)
    if verify_warnings:
        for w in verify_warnings:
            print(f"    ! {w}")
        logger.warning("Agent verification flagged %d issue(s)", len(verify_warnings))
    else:
        print("    Results look consistent with user intent")
    logger.info("Agent STEP 3 complete: %d verification warning(s)", len(verify_warnings))

    # ── STEP 4: EXPLAIN ──────────────────────────────────────
    print("\n  [STEP 4: EXPLAIN] Generating AI summary...")
    ai_summary = _generate_agent_summary(user_prefs, recommendations, issues, verify_warnings)
    print(f"    {ai_summary}")
    logger.info("Agent STEP 4 complete: AI summary generated")

    print(f"\n  {'='*50}\n")
    return recommendations, ai_summary


def _generate_agent_summary(
    user_prefs: Dict,
    recommendations: List[Tuple],
    issues: List[str],
    verify_warnings: List[str],
) -> str:
    """STEP 4: Call Gemini with retrieved songs + analysis context for a grounded summary."""
    import os
    from dotenv import load_dotenv

    load_dotenv()
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        logger.warning("GEMINI_API_KEY not set — skipping AI summary")
        return "[AI summary unavailable: API key not configured]"

    try:
        from google import genai
        client = genai.Client(api_key=api_key)

        song_lines = []
        for i, (song, score, _) in enumerate(recommendations, 1):
            song_lines.append(
                f"{i}. \"{song['title']}\" by {song['artist']} "
                f"(genre={song['genre']}, mood={song['mood']}, "
                f"energy={song['energy']}, valence={song['valence']}, score={score:.2f})"
            )
        retrieved = "\n".join(song_lines)
        prefs_summary = ", ".join(f"{k}={v}" for k, v in user_prefs.items())

        analysis_context = ""
        if issues:
            analysis_context += f"\nProfile issues detected: {'; '.join(issues)}."
        if verify_warnings:
            analysis_context += f"\nResult quality warnings: {'; '.join(verify_warnings)}."

        prompt = (
            f"A music listener has these preferences: {prefs_summary}.{analysis_context}\n\n"
            f"Based only on the following retrieved songs:\n{retrieved}\n\n"
            f"In 2-3 sentences, explain why these songs were recommended. "
            f"If there were any profile issues or result warnings, briefly acknowledge them. "
            f"Be specific — reference song titles."
        )

        response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
        return response.text.strip()

    except Exception as e:
        logger.error("Agent AI summary failed: %s", e)
        return f"[AI summary unavailable: {e}]"
