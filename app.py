from __future__ import annotations

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
}
</style>
"""

ELITE_TIER = {
    "S.S. Rajamouli",
    "Rajkumar Hirani",
    "Sanjay Leela Bhansali",
    "Shah Rukh Khan",
    "Aamir Khan",
    "Amitabh Bachchan",
    "Prabhas",
    "Alia Bhatt",
    "Deepika Padukone",
    "A.R. Rahman",
    "M.M. Keeravani",
    "Salim-Javed",
    "K.V. Vijayendra Prasad",
}

PREMIUM_TIER = {
    "Imtiaz Ali",
    "Rohit Shetty",
    "Siddharth Anand",
    "Nitesh Tiwari",
    "Ranbir Kapoor",
    "Hrithik Roshan",
    "Ranveer Singh",
    "Vicky Kaushal",
    "Kareena Kapoor",
    "Shraddha Kapoor",
    "Pritam",
    "Vishal-Shekhar",
}

GLOBAL_DRAWS = {"Shah Rukh Khan", "Aamir Khan", "Prabhas"}
ROLES = list(MOVIES.keys())


def stable_range_score(name: str, min_points: int, max_points: int) -> int:
    span = max_points - min_points + 1
    return min_points + (sum(ord(ch) for ch in name) % span)


def dynamic_tier_score(name: str) -> int:
    if name in ELITE_TIER:
        return stable_range_score(name, 21, 23)
    if name in PREMIUM_TIER:
        return stable_range_score(name, 17, 20)
    return stable_range_score(name, 12, 14)


def team_synergy_boost(picks: dict[str, str]) -> tuple[int, list[str]]:
    selected = set(picks.values())
    boosts = 0
    notes = []
    if "Shah Rukh Khan" in selected and ("Aditya Chopra" in selected or "Yash Chopra" in selected):
        boosts += 12
        notes.append("Shah Rukh Khan + Chopra legacy duo (+12)")
    if "S.S. Rajamouli" in selected and "K.V. Vijayendra Prasad" in selected:
        boosts += 12
        notes.append("Rajamouli + K.V. Vijayendra Prasad epic synergy (+12)")
    if "Aamir Khan" in selected and ("Rajkumar Hirani" in selected or "Nitesh Tiwari" in selected):
        boosts += 12
        notes.append("Aamir Khan + visionary director pairing (+12)")
    if "A.R. Rahman" in selected and ("Imtiaz Ali" in selected or "Sanjay Leela Bhansali" in selected):
        boosts += 12
        notes.append("Auteur director + A.R. Rahman musical magic (+12)")
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
    score_index = clamp((box_office_score - 60) / 75, 0.0, 1.0)
    opening_day = 2 + (score_index * 73)
    if box_office_score > 135:
        opening_day += min(10.0, (box_office_score - 135) * 0.35)

    acclaim_index = clamp((critical_acclaim - 55) / 45, 0.0, 1.0)
    word_of_mouth_factor = 2.0 + acclaim_index * 6.5
    lifetime_domestic = opening_day * word_of_mouth_factor

    team = set(picks.values())
    global_count = len(team & GLOBAL_DRAWS)
    overseas_multiplier = 1.30 + score_index * 0.35 + (global_count * 0.85)
    if global_count:
        overseas_multiplier += 0.40
    worldwide = lifetime_domestic * overseas_multiplier
    return opening_day, lifetime_domestic, worldwide


def lock_role(role: str) -> None:
    selected = st.session_state.get(f"pick_{role}")
    if selected:
        st.session_state.locked_picks[role] = selected
        st.rerun()


if "locked_picks" not in st.session_state:
    st.session_state.locked_picks = {}

st.markdown(THEME_CSS, unsafe_allow_html=True)
st.markdown("<h1 class='gold-serif'>🎥 Bollywood Box Office Draft War Room</h1>", unsafe_allow_html=True)
st.caption("Draft 5 core roles. Build chemistry. Predict the box office dhamaka.")

all_filled = len(st.session_state.locked_picks) == len(ROLES)

if not all_filled:
    cols = st.columns(len(ROLES))
    for idx, role in enumerate(ROLES):
        with cols[idx]:
            st.markdown(f"<h3 class='gold-serif'>{role}</h3>", unsafe_allow_html=True)
            current_locked = st.session_state.locked_picks.get(role)
            if current_locked:
                st.success(f"Locked: {current_locked}")
            else:
                key = f"pick_{role}"
                default_choice = MOVIES[role][0]
                if key not in st.session_state:
                    st.session_state[key] = default_choice
                st.selectbox("Pick talent", MOVIES[role], key=key, label_visibility="collapsed")
                st.button("Lock Role", key=f"lock_{role}", on_click=lock_role, args=(role,), use_container_width=True)
else:
    st.info("All 5 slots locked. Draft board hidden for a clean final projection view.")

if st.session_state.locked_picks:
    picks = st.session_state.locked_picks
    role_scores = {role: dynamic_tier_score(name) for role, name in picks.items()}
    base_score_total = sum(role_scores.values())
    synergy_score, synergy_notes = team_synergy_boost(picks)
    box_office_score = base_score_total + synergy_score

    critical_acclaim = (base_score_total / len(picks)) * 4.2 + (synergy_score * 0.8)
    critical_acclaim = clamp(critical_acclaim, 45.0, 100.0)

    opening_day, lifetime_domestic, worldwide = calculate_box_office(box_office_score, critical_acclaim, picks)

    st.markdown("## Final Team & Projections")
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    for role in ROLES:
        if role in picks:
            st.write(f"**{role}:** {picks[role]} · Score: {dynamic_tier_score(picks[role])}")
    if synergy_notes:
        st.write("**Synergy Bonuses:**")
        for note in synergy_notes:
            st.write(f"- {note}")
    st.markdown("</div>", unsafe_allow_html=True)

    metrics = st.columns(5)
    metrics[0].metric("Box Office Score", f"{box_office_score:.1f}")
    metrics[1].metric("Critical Acclaim", f"{critical_acclaim:.1f}/100")
    metrics[2].metric("Opening Day", format_inr_crore(opening_day))
    metrics[3].metric("Lifetime Domestic", format_inr_crore(lifetime_domestic))
    metrics[4].metric("Worldwide Gross", format_inr_crore(worldwide))

if st.button("Reset Draft"):
    for role in ROLES:
        st.session_state.pop(f"pick_{role}", None)
    st.session_state.locked_picks = {}
    st.rerun()
