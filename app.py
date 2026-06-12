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
h1, h2, h3, .gold-serif {
    font-family: "Times New Roman", "Georgia", serif !important;
    font-weight: 800 !important;
    color: var(--gold) !important;
}
.stButton > button {
    border: 1px solid var(--gold);
    color: var(--gold);
    background: rgba(10, 0, 2, 0.65);
}
.stButton > button:hover {
    background: rgba(212, 175, 55, 0.16);
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
</style>
"""

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
ROLES = ["Director", "Lead Male", "Lead Female", "Music Director", "Writer"]

ELITE_RANGE = (21, 23)
PREMIUM_RANGE = (17, 20)
BASELINE_RANGE = (12, 14)
OPENING_MIN_CR = 2.0
OPENING_LINEAR_RANGE_CR = 73.0
OPENING_SCORE_BASE = 60.0
OPENING_SCORE_SPAN = 75.0
OPENING_BONUS_THRESHOLD = 135.0
OPENING_BONUS_CAP = 10.0
OPENING_BONUS_MULTIPLIER = 0.35
ACCLAIM_BASELINE = 55.0
ACCLAIM_SPAN = 45.0
BASE_WOM_MULTIPLIER = 2.0
MAX_WOM_BONUS = 6.5
BASE_OVERSEAS_MULTIPLIER = 1.30
SCORE_OVERSEAS_BONUS = 0.35
PER_GLOBAL_DRAW_BONUS = 0.85
GLOBAL_DRAW_PRESENCE_BONUS = 0.40
CRITIC_BASE_MULTIPLIER = 4.2
CRITIC_SYNERGY_MULTIPLIER = 0.8

def stable_range_score(name: str, min_points: int, max_points: int) -> int:
    span = max_points - min_points + 1
    return min_points + (sum(ord(ch) for ch in name) % span)

def dynamic_tier_score(name: str) -> int:
    if name in ELITE_TIER:
        return stable_range_score(name, ELITE_RANGE[0], ELITE_RANGE[1])
    if name in PREMIUM_TIER:
        return stable_range_score(name, PREMIUM_RANGE[0], PREMIUM_RANGE[1])
    return stable_range_score(name, BASELINE_RANGE[0], BASELINE_RANGE[1])

def team_synergy_boost(picks: dict[str, str]) -> tuple[int, list[str]]:
    selected = set(picks.values())
    boosts = 0
    notes = []
    if "Shah Rukh Khan" in selected and ("Aditya Chopra" in selected or "Yash Chopra" in selected or "Karan Johar" in selected):
        boosts += 12
        notes.append("Shah Rukh Khan + Legacy Director duo (+12)")
    if "S. S. Rajamouli" in selected and "K. V. Vijayendra Prasad" in selected:
        boosts += 12
        notes.append("Rajamouli + K.V. Vijayendra Prasad epic synergy (+12)")
    if "Aamir Khan" in selected and ("Rajkumar Hirani" in selected or "Nitesh Tiwari" in selected):
        boosts += 12
        notes.append("Aamir Khan + Visionary Director pairing (+12)")
    if "A. R. Rahman" in selected and ("Imtiaz Ali" in selected or "Sanjay Leela Bhansali" in selected or "Mani Ratnam" in selected):
        boosts += 12
        notes.append("Auteur Director + A.R. Rahman musical magic (+12)")
    return boosts, notes

def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))

def indian_group(number: int) -> str:
    value = str(number)
    if len(value) <= 3:
        return value
    last_three = value[-3:]
    remaining = value[:-3]
    chunks = []
    while len(remaining) > 2:
        chunks.insert(0, remaining[-2:])
        remaining = remaining[:-2]
    if remaining:
        chunks.insert(0, remaining)
    return ",".join(chunks + [last_three])

def format_inr_crore(crores: float) -> str:
    whole = int(crores)
    decimals = int(round((crores - whole) * 100))
    if decimals == 100:
        whole += 1
        decimals = 0
    return f"₹{indian_group(whole)}.{decimals:02d} Cr"

def calculate_box_office(box_office_score: float, critical_acclaim: float, picks: dict[str, str]) -> tuple[float, float, float]:
    score_index = clamp((box_office_score - OPENING_SCORE_BASE) / OPENING_SCORE_SPAN, 0.0, 1.0)
    opening_day = OPENING_MIN_CR + (score_index * OPENING_LINEAR_RANGE_CR)
    if box_office_score > OPENING_BONUS_THRESHOLD:
        opening_day += min(OPENING_BONUS_CAP, (box_office_score - OPENING_BONUS_THRESHOLD) * OPENING_BONUS_MULTIPLIER)

    acclaim_index = clamp((critical_acclaim - ACCLAIM_BASELINE) / ACCLAIM_SPAN, 0.0, 1.0)
    word_of_mouth_factor = BASE_WOM_MULTIPLIER + acclaim_index * MAX_WOM_BONUS
    lifetime_domestic = opening_day * word_of_mouth_factor

    team = set(picks.values())
    global_count = len(team & GLOBAL_DRAWS)
    overseas_multiplier = BASE_OVERSEAS_MULTIPLIER + score_index * SCORE_OVERSEAS_BONUS + (global_count * PER_GLOBAL_DRAW_BONUS)
    if global_count:
        overseas_multiplier += GLOBAL_DRAW_PRESENCE_BONUS
    worldwide = lifetime_domestic * overseas_multiplier
    return opening_day, lifetime_domestic, worldwide

def draft_talent(role: str, name: str, movie_title: str) -> None:
    st.session_state.locked_picks[role] = name
    st.session_state.pick_origins[role] = f"{movie_title} ({st.session_state.current_movie['year']})"
    # Automatically roll a new movie for the next choice
    st.session_state.current_movie = random.choice(MOVIES)

# State initialization
if "locked_picks" not in st.session_state:
    st.session_state.locked_picks = {}
if "pick_origins" not in st.session_state:
    st.session_state.pick_origins = {}
if "current_movie" not in st.session_state:
    st.session_state.current_movie = random.choice(MOVIES)

st.markdown(THEME_CSS, unsafe_allow_html=True)
st.markdown("<h1 class='gold-serif'>🎥 Bollywood Box Office Draft War Room</h1>", unsafe_allow_html=True)
st.caption("Draft 5 core roles. Test your luck with random historical movie rolls. Predict the box office dhamaka.")

all_filled = len(st.session_state.locked_picks) == len(ROLES)

left_col, right_col = st.columns([1.2, 1.5], gap="large")

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
                """,
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                f"""
                <div class='card' style='border-style: dashed; opacity: 0.6; padding: 0.75rem;'>
                    <strong style='color: #99a2be; text-transform: uppercase; font-size: 0.8rem;'>{role}</strong><br>
                    <span style='color: #7e879f; font-style: italic;'>[Empty Slot]</span>
                </div>
                """,
                unsafe_allow_html=True
            )

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
            """,
            unsafe_allow_html=True
        )
        
        st.markdown("#### Choose ONE role to draft from this movie:")
        
        for role in ROLES:
            talent_name = current_film["roles"][role]
            is_role_filled = role in st.session_state.locked_picks
            
            # Button is disabled if you already locked that role on your team
            st.button(
                f"Draft {talent_name} as {role}",
                key=f"btn_{role}_{current_film['title']}_{current_film['year']}",
                disabled=is_role_filled,
                use_container_width=True,
                on_click=draft_talent,
                args=(role, talent_name, current_film["title"])
            )
    else:
        st.success("🎉 All slots filled! Scroll down to see your box office metrics below.")

# Global results display once drafting or simulation begins
if st.session_state.locked_picks:
    picks = st.session_state.locked_picks
    role_scores = {role: dynamic_tier_score(name) for role, name in picks.items()}
    base_score_total = sum(role_scores.values())
    synergy_score, synergy_notes = team_synergy_boost(picks)
    box_office_score = base_score_total + synergy_score

    critical_acclaim = (base_score_total / len(picks)) * CRITIC_BASE_MULTIPLIER + (synergy_score * CRITIC_SYNERGY_MULTIPLIER)
    critical_acclaim = clamp(critical_acclaim, 45.0, 100.0)

    opening_day, lifetime_domestic, worldwide = calculate_box_office(box_office_score, critical_acclaim, picks)

    st.markdown("---")
    st.markdown("## Projections & Chemistry Evaluation")
    
    if synergy_notes:
        st.markdown("<div class='card' style='border-color: #2ea043;'>", unsafe_allow_html=True)
        st.write("🔥 **Active Chemistry Synergy Bonuses:**")
        for note in synergy_notes:
            st.write(f"• {note}")
        st.markdown("</div>", unsafe_allow_html=True)

    metrics = st.columns(5)
    metrics[0].metric("Box Office Score", f"{box_office_score:.1f}")
    metrics[1].metric("Critical Acclaim", f"{critical_acclaim:.1f}/100")
    metrics[2].metric("Opening Day", format_inr_crore(opening_day))
    metrics[3].metric("Lifetime Domestic", format_inr_crore(lifetime_domestic))
    metrics[4].metric("Worldwide Gross", format_inr_crore(worldwide))
    
    st.write("")
    if st.button("Reset War Room Draft", type="primary", use_container_width=True):
        st.session_state.locked_picks = {}
        st.session_state.pick_origins = {}
        st.session_state.current_movie = random.choice(MOVIES)
        st.rerun()
