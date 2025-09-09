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

def schedule_rerun(delay_ms: int):
    st.markdown(
        f"""
        <script>
          setTimeout(() => {{
            window.parent.postMessage({{type: "streamlit:rerun"}}, "*");
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
    ss.setdefault("queue_spin_snd", False)
    ss.setdefault("queue_win_snd", False)
    ss.setdefault("auto_spinning", False)
    ss.setdefault("auto_spin_remaining", 0)
    ss.setdefault("auto_delay_ms", 350)

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
