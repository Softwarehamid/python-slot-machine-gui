# streamlit_app.py
import random
import json
from io import BytesIO
from pathlib import Path
import base64
import streamlit as st
import streamlit.components.v1 as components

# ---------- paths ----------
BASE_DIR = Path(__file__).parent
IMG_PREVIEW = BASE_DIR / "images" / "slot-machine-GUI.png"
SND_SPIN = BASE_DIR / "assets" / "sound" / "spin.wav"
SND_WIN  = BASE_DIR / "assets" / "sound" / "win.wav"

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

def schedule_rerun(delay_ms: int):
    st.markdown(
        f"""
        <script>
          setTimeout(() => {{
            (window.parent || window).postMessage({{type: "streamlit:rerun"}}, "*");
          }}, {int(delay_ms)});
        </script>
        """,
        unsafe_allow_html=True,
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
    ss.setdefault("auto_spinning", False)
    ss.setdefault("auto_spin_remaining", 0)
    ss.setdefault("auto_delay_ms", 350)
    ss.setdefault("mute", False)
    ss.setdefault("queue_spin", False)
    ss.setdefault("queue_win", False)

def reset_stats_only():
    st.session_state.spins = 0
    st.session_state.wins = 0
    st.session_state.last_reels = ["❔", "❔", "❔"]
    st.session_state.last_win = 0

def reset_all():
    reset_stats_only()
    st.session_state.balance = 100
    st.session_state.total_deposited = 0
    st.session_state.queue_spin = False
    st.session_state.queue_win = False

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
    if st.session_state.hardcore:
        st.session_state.balance = 100
        st.session_state.total_deposited = 0

# ---------- audio kernel ----------
def inject_audio_kernel():
    spin_b64 = base64.b64encode(SND_SPIN.read_bytes_
