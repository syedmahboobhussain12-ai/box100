from __future__ import annotations
import random
import streamlit as st
from movies_data import MOVIES

st.set_page_config(page_title="Bollywood Box Office Draft", page_icon="🎬", layout="wide")

THEME_CSS = """
<style>
:root {
    --bg-top: #3a0007;
    --bg-mid: #1a0003;
    --bg-bottom: #0a0002;
    --gold: #d4af37;
}
[data-testid="stAppViewContainer"] {
    background: radial-gradient(circle at top, var(--bg-top) 0%, var(--bg-mid) 50%, var(--bg-bottom) 100%);
    color: #f8edd0;
}
[data-testid="stHeader"] {background: transparent;}
h1, h2, h3, h4, .gold-serif {
    font-family: "Times New Roman", "Georgia", serif !important;
    font-weight: 800 !important;
    color: var(--gold) !important;
}
.stButton > button {
    border: 1px solid var(--gold);
    color: var(--gold);
    background: rgba(10, 0, 2, 0.65);
    transition: all 0.3s ease;
}
.stButton > button:hover {
    background: rgba(212, 175, 55, 0.16);
    border-color: #fff;
    color: #fff;
}
div[data-testid="stMetric"] {
    border: 1px solid var(--gold);
    border-radius: 12px;
    background: rgba(10, 0, 2, 0.55);
    padding: 0.4rem 0.6rem;
}
.card {
    border: 1px solid var(--gold);
    border-radius: 12px;
    padding: 1rem;
    background: rgba(10, 0, 2, 0.62);
    margin-bottom: 1rem;
}
.movie-title {
    font-size: 2.2rem;
    color: var(--gold);
    font-weight: bold;
    margin-bottom: 0.1rem;
}
.ott-banner {
    background: linear-gradient(90deg, rgba(20,20,20,1) 0%, rgba(60,10,10,1) 100%);
    border-left: 5px solid var(--gold);
    padding: 1rem;
    border-radius: 8px;
    margin-top: 1rem;
}
.review-box {
    border-left: 4px solid #f8edd0;
    padding-left: 1rem;
    margin: 1.5rem 0;
    font-style: italic;
    color: #d8e2fd;
    font-size: 1.1rem;
    background: rgba(255,255,255,0.02);
    padding: 1rem;
    border-radius: 0 8px 8px 0;
}
</style>
"""

# --- CONSTANTS & TIERS ---
ELITE_TIER = {
    "S. S. Rajamouli", "Rajkumar Hirani", "Sanjay Leela Bhansali", 
    "Shah Rukh Khan", "Aamir Khan", "Amitabh Bachchan", "Prabhas", 
    "Alia Bhatt", "Deepika Padukone", "A. R. Rahman", "M. M. Keeravani", 
    "Salim Khan", "K. V. Vijayendra Prasad",
}
PREMIUM_TIER = {
    "Imtiaz Ali", "Rohit Shetty", "Siddharth Anand", "Nitesh Tiwari", 
    "Ranbir Kapoor", "Hrithik Roshan", "Ranveer Singh", "Vicky Kaushal", 
    "Kareena Kapoor", "Shraddha Kapoor", "Pritam", "Vishal-Shekhar",
    "Salman Khan", "Ajay Devgn", "Anushka Sharma", "Katrina Kaif", "Zoya Akhtar"
}
GLOBAL_DRAWS = {"Shah Rukh Khan", "Aamir Khan", "Prabhas", "Salman Khan"}

# Expanded to 6 Slots
ROLES = ["Director", "Genre", "Lead Male", "Lead Female", "Music Director", "Writer"]

# Math Constants
CRITIC_BASE_MULTIPLIER = 4.2
CRITIC_SYNERGY_MULTIPLIER = 0.8
OPENING_MIN_CR = 2.0
OPENING_LINEAR_RANGE_CR = 73.0
OPENING_SCORE_BASE = 60.0
OPENING_SCORE_SPAN = 75.0
OPENING_BONUS_THRESHOLD = 135.0
OPENING_BONUS_CAP = 10.0
OPENING_BONUS_MULTIPLIER = 0.35

# --- HELPER FUNCTIONS ---
def stable_range_score(text: str, min_points: int, max_points: int) -> int:
    span = max_points - min_points + 1
    return min_points + (sum(ord(ch) for ch in text) % span)

def dynamic_tier_score(name: str) -> int:
    # Give genre picks a flat baseline so it doesn't break math
    if any(g in name for g in ["Action", "Romance", "Drama", "Thriller", "Comedy"]):
        return 16
    if name in ELITE_TIER: return stable_range_score(name, 21, 23)
    if name in PREMIUM_TIER: return stable_range_score(name, 17, 20)
    return stable_range_score(name, 12, 14)

def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))

def format_inr_crore(crores: float) -> str:
    whole = int(crores)
    decimals = int(round((crores - whole) * 100))
    if decimals == 100:
        whole += 1; decimals = 0
    val_str = str(whole)
    last_three = val_str[-3:]
    remaining = val_str[:-3]
    chunks = []
    while len(remaining) > 2:
        chunks.insert(0, remaining[-2:])
        remaining = remaining[:-2]
    if remaining: chunks.insert(0, remaining)
    fmt_whole = ",".join(chunks + [last_three]) if len(val_str) > 3 else val_str
    return f"₹{fmt_whole}.{decimals:02d} Cr"

# --- GAME ENGINE LOGIC ---
def get_era_pool():
    if st.session_state.chosen_era == "All":
        return MOVIES
    return [m for m in MOVIES if m["era"] == st.session_state.chosen_era]

def inject_genre_and_roll():
    pool = get_era_pool()
    movie = random.choice(pool).copy()
    
    # Dynamically inject historically accurate genres based on era
    if movie["era"] == "Vintage":
        genres = ["Epic Historical Period Drama 🏰", "Classic Tragedy 🎭", "Gothic Romance 🥀"]
    elif movie["era"] == "90s":
        genres = ["High-Octane Action Masala 💥", "Soulful Romantic Drama 💖", "Family Entertainer 👨‍👩‍👧‍👦"]
    elif movie["era"] == "Modern":
        genres = ["Heartwarming Social Drama 🌍", "Gritty Crime Thriller 🚬", "Biopic 📖"]
    else:
        genres = ["Commercial Pan-India Epic 🌋", "Spy Universe Thriller 🕶️", "Mythological Fantasy ✨"]
        
    g_idx = stable_range_score(movie["title"], 0, len(genres)-1)
    movie["roles"] = movie["roles"].copy()
    movie["roles"]["Genre"] = genres[g_idx]
    
    return movie

def generate_cinematic_title(picks: dict[str, str]) -> str:
    genre = picks.get("Genre", "")
    base_hash = stable_range_score("".join(picks.values()), 0, 2)
    
    if "Action" in genre or "Thriller" in genre or "Spy" in genre:
        titles = ["Kshatriya: The Ultimate Warrior", "Vengeance Protocol", "Agni Patha"]
    elif "Romance" in genre or "Comedy" in genre or "Family" in genre:
        titles = ["Hum Tum Aur Ishq", "Prem Deewane", "Dil Ka Safar"]
    elif "Social" in genre or "Biopic" in genre or "Tragedy" in genre:
        titles = ["Satyamev Jayate", "Naya Bharat", "Umeed"]
    else:
        titles = ["Samrat Shaurya", "The Throne of Rajputana", "Rajvansh"]
        
    return titles[base_hash]

def generate_trade_review(bo_score: float, rt_score: float) -> tuple[str, str]:
    if bo_score >= 105 and rt_score >= 75:
        return (
            "A historic cinematic triumph where impeccable storytelling perfectly marries raw, unadulterated mass appeal!",
            "Word-of-mouth spread like wildfire on opening night, turning theater halls into an absolute festival celebration."
        )
    elif bo_score >= 100 and rt_score < 60:
        return (
            "Audiences completely ignored the critics' rants and flocked to single screens for pure front-row fan service.",
            "Massive star power and foot-tapping tracks carried this scriptless wonder all the way to the bank!"
        )
    elif bo_score < 85 and rt_score >= 75:
        return (
            "A brilliant, critically acclaimed masterpiece that unfortunately found zero takers at the multiplex counters.",
            "Superb directorial vision, but lacking the loud commercial hooks needed to survive outside the festival circuit."
        )
    elif bo_score < 80 and rt_score < 60:
        return (
            "An unmitigated disaster that failed on every conceivable level of filmmaking arithmetic.",
            "Zero on-screen chemistry, a dated screenplay, and flat music ensured empty seats by the evening show."
        )
    else:
        return (
            "A solid theatrical performer that hit all the standard commercial beats without taking any major risks.",
            "Fans went home happy, critics gave it a passing grade, and the producers recovered their investment."
        )

def determine_ott_platform(picks: dict[str, str], bo_score: float, rt_score: float) -> str:
    team = set(picks.values())
    if "S. S. Rajamouli" in team or "Prabhas" in team or "Action" in picks.get("Genre", ""):
        return "**Netflix 🔴** (Record-Breaking Multi-Lingual Global Deal: ₹250 Cr+)"
    if "Sanjay Leela Bhansali" in team or rt_score >= 80:
        return "**Netflix 🔴** (Trending #1 Globally in Non-English Films)"
    if bo_score > 105:
        return "**Amazon Prime Video 🔵** (Exclusive Post-Theatrical Festive Blockbuster Premiere)"
    if rt_score < 60:
        return "**Zee5 / JioCinema 🟠** (Picked up quietly for the late-night action/masala catalog)"
    return "**Disney+ Hotstar 🟢** (Family Weekend Premiere Streaming Rights)"

def draft_talent(role: str, name: str, movie_title: str, movie_year: int) -> None:
    st.session_state.locked_picks[role] = name
    st.session_state.pick_origins[role] = f"{movie_title} ({movie_year})"
    st.session_state.current_movie = inject_genre_and_roll()

def select_era(era_key: str):
    st.session_state.chosen_era = era_key
    st.session_state.current_movie = inject_genre_and_roll()

# --- INITIALIZATION ---
if "chosen_era" not in st.session_state: st.session_state.chosen_era = None
if "locked_picks" not in st.session_state: st.session_state.locked_picks = {}
if "pick_origins" not in st.session_state: st.session_state.pick_origins = {}

st.markdown(THEME_CSS, unsafe_allow_html=True)

# ==========================================
# SCREEN 1: ERA SELECTION LANDING PAGE
# ==========================================
if st.session_state.chosen_era is None:
    st.markdown("<h1 style='text-align: center; font-size: 4rem; margin-bottom: 0;'>Box Office 100</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-size: 1.2rem; color: #a9b4d0; margin-bottom: 3rem;'>Select your filmmaking era to begin the draft.</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3, gap="large")
    with col1:
        st.button("Vintage Classics 📜", use_container_width=True, on_click=select_era, args=("Vintage",))
        st.button("90s Romance & Masala 🕺", use_container_width=True, on_click=select_era, args=("90s",))
    with col2:
        st.button("Millennium Blockbusters 🛸", use_container_width=True, on_click=select_era, args=("Millennium",))
        st.button("Modern Defining Cinema 🎭", use_container_width=True, on_click=select_era, args=("Modern",))
    with col3:
        st.button("The Pan-India Era 🏔️", use_container_width=True, on_click=select_era, args=("2021-2026",))
        st.button("All-Era Madness 🌪️", use_container_width=True, on_click=select_era, args=("All",))

# ==========================================
# SCREEN 2: THE DRAFT WAR ROOM
# ==========================================
else:
    era_label = st.session_state.chosen_era if st.session_state.chosen_era != "All" else "All-Era Madness"
    st.markdown(f"<div style='background: rgba(212, 175, 55, 0.2); padding: 0.5rem 1rem; border-radius: 8px; display: inline-block; margin-bottom: 1rem; color: var(--gold); border: 1px solid var(--gold);'><strong>Active Mode:</strong> {era_label}</div>", unsafe_allow_html=True)
    st.markdown("<h1 class='gold-serif' style='margin-top:0;'>🎥 Bollywood Box Office Draft</h1>", unsafe_allow_html=True)
    
    all_filled = len(st.session_state.locked_picks) == len(ROLES)
    left_col, right_col = st.columns([1.2, 1.5], gap="large")

    # -- LEFT: ROSTER --
    with left_col:
        st.markdown("### Your Crew Roster")
        for role in ROLES:
            if role in st.session_state.locked_picks:
                name = st.session_state.locked_picks[role]
                origin = st.session_state.pick_origins[role]
                st.markdown(
                    f"""
                    <div class='card' style='border-color: #2ea043; background: rgba(46,160,67,0.08); padding: 0.75rem;'>
                        <strong style='color: var(--gold); text-transform: uppercase; font-size: 0.8rem;'>{role}</strong><br>
                        <span style='font-size: 1.1rem; font-weight: bold;'>{name}</span><br>
                        <span style='font-size: 0.8rem; color: #a9b4d0;'>Drafted from: {origin}</span>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.markdown(
                    f"""
                    <div class='card' style='border-style: dashed; opacity: 0.6; padding: 0.75rem;'>
                        <strong style='color: #99a2be; text-transform: uppercase; font-size: 0.8rem;'>{role}</strong><br>
                        <span style='color: #7e879f; font-style: italic;'>[Empty Slot]</span>
                    </div>
                    """, unsafe_allow_html=True)

    # -- RIGHT: DRAFTING --
    with right_col:
        if not all_filled:
            current_film = st.session_state.current_movie
            st.markdown("### Now Showing for Selection")
            st.markdown(
                f"""
                <div class='card' style='border-color: var(--gold); padding: 1.25rem;'>
                    <div class='movie-title'>{current_film['title']}</div>
                    <span style='color: #b8c2dd; font-size: 1rem;'>Era: <strong>{current_film['era']}</strong> | Year: <strong>{current_film['year']}</strong></span>
                </div>
                """, unsafe_allow_html=True)
            
            for role in ROLES:
                talent_name = current_film["roles"].get(role, "Not Found")
                is_filled = role in st.session_state.locked_picks
                st.button(f"Draft {talent_name} as {role}", key=f"btn_{role}_{current_film['title']}", disabled=is_filled, use_container_width=True, on_click=draft_talent, args=(role, talent_name, current_film["title"], current_film["year"]))
        else:
            st.success("🎉 All 6 slots locked! Analyzing theatrical performance...")

    # ==========================================
    # RESULTS METRICS & REVIEWS
    # ==========================================
    if all_filled:
        picks = st.session_state.locked_picks
        role_scores = {role: dynamic_tier_score(name) for role, name in picks.items()}
        base_score_total = sum(role_scores.values())
        
        # Synergy
        synergy_score = 0
        if "Shah Rukh Khan" in picks.values() and ("Aditya Chopra" in picks.values() or "Karan Johar" in picks.values()): synergy_score += 12
        if "S. S. Rajamouli" in picks.values() and "K. V. Vijayendra Prasad" in picks.values(): synergy_score += 12
        box_office_score = base_score_total + synergy_score

        # Math Engine
        rt_score = (base_score_total / len(picks)) * CRITIC_BASE_MULTIPLIER + (synergy_score * CRITIC_SYNERGY_MULTIPLIER)
        rt_score = clamp(rt_score, 12.0, 99.0)
        
        score_index = clamp((box_office_score - OPENING_SCORE_BASE) / OPENING_SCORE_SPAN, 0.0, 1.0)
        opening_day = OPENING_MIN_CR + (score_index * OPENING_LINEAR_RANGE_CR)
        if box_office_score > 130: opening_day += min(10.0, (box_office_score - 130) * 0.35)
        
        lifetime_domestic = opening_day * (2.0 + clamp((rt_score - 55) / 45, 0.0, 1.0) * 6.5)
        
        global_count = len(set(picks.values()) & GLOBAL_DRAWS)
        worldwide = lifetime_domestic * (1.30 + score_index * 0.35 + (global_count * 0.85))

        # Identity & Review Engine
        movie_title = generate_cinematic_title(picks)
        rev_line1, rev_line2 = generate_trade_review(box_office_score, rt_score)
        ott = determine_ott_platform(picks, box_office_score, rt_score)

        st.markdown("---")
        st.markdown(
            f"""
            <div style='text-align: center; margin: 3rem 0;'>
                <h4 style='color: #a9b4d0; text-transform: uppercase; letter-spacing: 2px;'>A {picks['Director']} Film</h4>
                <h1 style='font-size: 4rem; color: #fff; text-shadow: 2px 2px 8px rgba(212, 175, 55, 0.5); font-family: "Georgia", serif;'>"{movie_title}"</h1>
            </div>
            """, unsafe_allow_html=True)
        
        # Trade Review Box
        st.markdown(f"<div class='review-box'><strong>Trade Analyst Review:</strong><br>\"{rev_line1} {rev_line2}\"</div>", unsafe_allow_html=True)

        # Financials
        metrics = st.columns(5)
        metrics[0].metric("Box Office Score", f"{box_office_score:.1f}")
        rt_emoji = "🍅 Fresh" if rt_score >= 60 else "🤢 Splatted"
        metrics[1].metric(rt_emoji, f"{rt_score:.0f}%")
        metrics[2].metric("Opening Day", format_inr_crore(opening_day))
        metrics[3].metric("Lifetime Domestic", format_inr_crore(lifetime_domestic))
        metrics[4].metric("Worldwide Gross", format_inr_crore(worldwide))
        
        # OTT Banner
        st.markdown(f"<div class='ott-banner'><span style='color: #99a2be; font-size: 0.9rem; text-transform: uppercase;'>Streaming Rights Sold To:</span><br><span style='font-size: 1.2rem;'>{ott}</span></div>", unsafe_allow_html=True)
        
        st.write("")
        c1, c2, c3 = st.columns([1,1,2])
        with c1:
            if st.button("🔄 Play Era Again", use_container_width=True):
                st.session_state.locked_picks = {}
                st.session_state.pick_origins = {}
                st.session_state.current_movie = inject_genre_and_roll()
                st.rerun()
        with c2:
            if st.button("⚙️ Change Era", use_container_width=True):
                st.session_state.chosen_era = None
                st.session_state.locked_picks = {}
                st.session_state.pick_origins = {}
                st.rerun()
