import random
import json
import base64
from io import BytesIO
from uuid import uuid4
from pathlib import Path

import streamlit as st

# ---------- paths ----------
BASE_DIR = Path(__file__).parent
SND_SPIN = BASE_DIR / "assets" / "sound" / "spin.wav"
SND_WIN  = BASE_DIR / "assets" / "sound" / "win.wav"
IMG_PREVIEW = BASE_DIR / "images" / "slot-machine-GUI.png"

# ---------- game data ----------
SYMBOLS = ["🍒", "🍋", "🔔", "⭐", "7️⃣"]
PAYOUTS = {
    ("7️⃣","7️⃣","7️⃣"): 50,
    ("⭐","⭐","⭐"): 25,
    ("🔔","🔔","🔔"): 15,
    ("🍋","🍋","🍋"): 10,
    ("🍒","🍒","🍒"): 8,
}

# ---------- helpers ----------
def spin_reels():
    return [random.choice(SYMBOLS) for _ in range(3)]

def payout(reels, bet):
    t = tuple(reels)
    if t in PAYOUTS:
        return bet * PAYOUTS[t]
    if len(set(reels)) == 2:
        return bet * 2
    return 0

def audio_html(file_path: Path, muted: bool) -> str:
    if not file_path.exists():
        return ""
    b64 = base64.b64encode(file_path.read_bytes()).decode("utf-8")
    return (
        f'<audio id="snd-{uuid4()}" autoplay {"muted" if muted else ""} style="display:none">'
        f'<source src="data:audio/wav;base64,{b64}" type="audio/wav"></audio>'
    )

def init_state():
    ss = st.session_state
    ss.setdefault("balance", 100)
    ss.setdefault("spins", 0)
    ss.setdefault("wins", 0)
    ss.setdefault("hardcore", False)
    ss.setdefault("last_reels", ["❔", "❔", "❔"])
    ss.setdefault("last_win", 0)
    ss.setdefault("total_deposited", 0)
    ss.setdefault("queue_spin_snd", False)
    ss.setdefault("queue_win_snd", False)

def reset_stats_only():
    st.session_state.spins = 0
    st.session_state.wins = 0
    st.session_state.last_reels = ["❔", "❔", "❔"]
    st.session_state.last_win = 0

def reset_all():
    reset_stats_only()
    st.session_state.balance = 100
    st.session_state.total_deposited = 0
    st.session_state.queue_spin_snd = False
    st.session_state.queue_win_snd = False

def save_blob():
    data = {
        "balance": st.session_state.balance,
        "spins": st.session_state.spins,
        "wins": st.session_state.wins,
        "hardcore": st.session_state.hardcore,
        "total_deposited": st.session_state.total_deposited,
    }
    buf = BytesIO()
    buf.write(json.dumps(data).encode("utf-8"))
    buf.seek(0)
    return buf

def load_blob(uploaded):
    data = json.loads(uploaded.read().decode("utf-8"))
    st.session_state.balance = int(data.get("balance", 100))
    st.session_state.spins = int(data.get("spins", 0))
    st.session_state.wins = int(data.get("wins", 0))
    st.session_state.hardcore = bool(data.get("hardcore", False))
    st.session_state.total_deposited = int(data.get("total_deposited", 0))

# ---------- UI ----------
st.set_page_config(page_title="Python Slot Machine", page_icon="🎰", layout="centered")
init_state()

col_img, col_title = st.columns([1, 2], vertical_alignment="center")
with col_img:
    if IMG_PREVIEW.exists():
        st.image(str(IMG_PREVIEW), use_column_width=True)
    else:
        st.caption(f"Preview not found: {IMG_PREVIEW.name}")

with col_title:
    st.title("Python Slot Machine")
    st.caption("Runs in your browser with Streamlit.")
    st.caption("Session saves in memory. Download or load a save file anytime.")

with st.sidebar:
    st.header("Settings")
    st.session_state.hardcore = st.toggle(
        "Hardcore mode",
        value=st.session_state.hardcore,
        help="Disables all reset actions.",
    )
    mute = st.toggle("Mute sounds", value=False)
    bet = st.number_input("Bet per spin", min_value=1, max_value=20, value=5, step=1)

    st.divider()
    st.header("Funds")
    deposit = st.number_input("Amount to add", min_value=1, max_value=100000, value=10, step=1)
    if st.button("Add funds"):
        st.session_state.balance += deposit
        st.session_state.total_deposited += deposit
        st.success(f"Added ${deposit}")
    st.caption(f"Total deposited: ${st.session_state.total_deposited}")

    st.divider()
    st.write("Save or load")
    st.download_button("Download save", data=save_blob(), file_name="slot_save.json", mime="application/json")
    up = st.file_uploader("Load save", type=["json"])
    if up is not None:
        load_blob(up)
        st.success("Save loaded")

st.subheader(f"Balance: ${st.session_state.balance}")
st.text(f"Spins: {st.session_state.spins}   Wins: {st.session_state.wins}")

r1, r2, r3 = st.columns(3)
with r1:
    st.metric("Reel 1", st.session_state.last_reels[0])
with r2:
    st.metric("Reel 2", st.session_state.last_reels[1])
with r3:
    st.metric("Reel 3", st.session_state.last_reels[2])

# actions
c1, c2, c3 = st.columns([1, 1, 1])
can_spin = st.session_state.balance >= bet

spin_clicked = c1.button("Spin", use_container_width=True, disabled=not can_spin)
reset_all_clicked = c2.button(
    "Reset balance and stats",
    use_container_width=True,
    disabled=st.session_state.hardcore,
)
reset_stats_clicked = c3.button(
    "Reset stats only",
    use_container_width=True,
    disabled=st.session_state.hardcore,
)

# spin
if spin_clicked and can_spin:
    st.session_state.queue_spin_snd = True
    st.session_state.balance -= bet
    reels = spin_reels()
    st.session_state.last_reels = reels
    win_amt = payout(reels, bet)
    st.session_state.last_win = win_amt
    st.session_state.spins += 1
    if win_amt > 0:
        st.session_state.wins += 1
        st.session_state.balance += win_amt
        st.session_state.queue_win_snd = True
    st.rerun()

# resets
if reset_all_clicked:
    reset_all()
    st.rerun()

if reset_stats_clicked:
    reset_stats_only()
    st.rerun()

# status
if st.session_state.last_win > 0:
    st.success(f"You won ${st.session_state.last_win}")
else:
    st.info("No win this spin")

# sounds
html_parts = []
if st.session_state.queue_spin_snd:
    html_parts.append(audio_html(SND_SPIN, muted=mute))
if st.session_state.queue_win_snd:
    html_parts.append(audio_html(SND_WIN, muted=mute))

if html_parts:
    st.markdown("\n".join(html_parts), unsafe_allow_html=True)
    st.session_state.queue_spin_snd = False
    st.session_state.queue_win_snd = False

st.caption("Symbols: 🍒 🍋 🔔 ⭐ 7️⃣")
