import random
import json
from io import BytesIO
from pathlib import Path

import streamlit as st

# ---------------- paths ----------------
BASE_DIR = Path(__file__).parent
SND_SPIN = BASE_DIR / "assets" / "sound" / "spin.wav"
SND_WIN  = BASE_DIR / "assets" / "sound" / "win.wav"
IMG_PREVIEW = BASE_DIR / "images" / "slot-machine-GUI.png"

# ---------------- game data ----------------
SYMBOLS = ["🍒", "🍋", "🔔", "⭐", "7️⃣"]
PAYOUTS = {
    ("7️⃣","7️⃣","7️⃣"): 50,
    ("⭐","⭐","⭐"): 25,
    ("🔔","🔔","🔔"): 15,
    ("🍋","🍋","🍋"): 10,
    ("🍒","🍒","🍒"): 8,
}

# ---------------- helpers ----------------
def spin_reels():
    return [random.choice(SYMBOLS) for _ in range(3)]

def payout(reels, bet):
    trip = tuple(reels)
    if trip in PAYOUTS:
        return bet * PAYOUTS[trip]
    if len(set(reels)) == 2:   # two of a kind
        return bet * 2
    return 0

def init_state():
    ss = st.session_state
    ss.setdefault("balance", 100)
    ss.setdefault("spins", 0)
    ss.setdefault("wins", 0)
    ss.setdefault("hardcore", False)
    ss.setdefault("last_reels", ["❔","❔","❔"])
    ss.setdefault("last_win", 0)

def reset_stats():
    if st.session_state.hardcore:
        st.warning("Hardcore mode is on. Reset is disabled.")
        return
    st.session_state.balance = 100
    st.session_state.spins = 0
    st.session_state.wins = 0
    st.session_state.last_reels = ["❔","❔","❔"]
    st.session_state.last_win = 0

def save_blob():
    data = {
        "balance": st.session_state.balance,
        "spins": st.session_state.spins,
        "wins": st.session_state.wins,
        "hardcore": st.session_state.hardcore,
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

# ---------------- UI ----------------
st.set_page_config(page_title="Python Slot Machine", page_icon="🎰", layout="centered")
init_state()

# header with preview image, no PIL
col_img, col_title = st.columns([1,2], vertical_alignment="center")
with col_img:
    try:
        if IMG_PREVIEW.exists():
            st.image(str(IMG_PREVIEW), use_container_width=True)
        else:
            st.caption(f"Preview not found: {IMG_PREVIEW}")
    except Exception as e:
        st.caption(f"Preview load error: {e}")

with col_title:
    st.title("Python Slot Machine")
    st.caption("Runs in your browser with Streamlit.")
    st.caption("Session saves live in your browser. You can also download a save file.")

with st.sidebar:
    st.header("Settings")
    st.session_state.hardcore = st.toggle(
        "Hardcore mode",
        value=st.session_state.hardcore,
        help="Disables reset while on."
    )
    bet = st.number_input("Bet per spin", min_value=1, max_value=20, value=5, step=1)

    st.divider()
    st.write("Save or load")
    st.download_button(
        "Download save",
        data=save_blob(),
        file_name="slot_save.json",
        mime="application/json",
    )
    up = st.file_uploader("Load save", type=["json"])
    if up is not None:
        load_blob(up)
        st.success("Save loaded")

st.subheader(f"Balance: ${st.session_state.balance}")
st.text(f"Spins: {st.session_state.spins}   Wins: {st.session_state.wins}")

r1, r2, r3 = st.columns(3)
with r1:  st.metric("Reel 1", st.session_state.last_reels[0])
with r2:  st.metric("Reel 2", st.session_state.last_reels[1])
with r3:  st.metric("Reel 3", st.session_state.last_reels[2])

left, right = st.columns(2)

if left.button("Spin", use_container_width=True):
    # play spin sound with string path
    if SND_SPIN.exists():
        st.audio(str(SND_SPIN))
    if st.session_state.balance < bet:
        st.error("Not enough balance")
    else:
        st.session_state.balance -= bet
        reels = spin_reels()
        st.session_state.last_reels = reels
        win_amt = payout(reels, bet)
        st.session_state.last_win = win_amt
        st.session_state.spins += 1
        if win_amt > 0:
            st.session_state.wins += 1
            st.session_state.balance += win_amt
            if SND_WIN.exists():
                st.audio(str(SND_WIN))

if right.button("Reset balance and stats", use_container_width=True):
    reset_stats()

if st.session_state.last_win > 0:
    st.success(f"You won ${st.session_state.last_win}")
else:
    st.info("No win this spin")

st.caption("Symbols: 🍒 🍋 🔔 ⭐ 7️⃣")
