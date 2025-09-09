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

def js_play_sound(file_path: Path, muted: bool, delay_ms: int = 0) -> str:
    if not file_path.exists():
        return ""
    b64 = base64.b64encode(file_path.read_bytes()).decode("utf-8")
    return f"""
    <script>
      setTimeout(() => {{
        const a = new Audio("data:audio/wav;base64,{b64}");
        a.muted = {str(muted).lower()};
        a.play().catch(()=>{{}});
      }}, {int(delay_ms)});
    </script>
    """

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
    ss.setdefault("mute", False)

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
    if st.session_state.hardcore:
        st.session_state.balance = 100
        st.session_state.total_deposited = 0

# ---------- UI ----------
st.set_page_config(page_title="Python Slot Machine", page_icon="🎰", layout="centered")
init_state()

# Header
col_img, col_title = st.columns([1, 2], vertical_alignment="center")
with col_img:
    if IMG_PREVIEW.exists():
        st.image(str(IMG_PREVIEW), use_container_width=True)
    else:
        st.caption(f"Preview not found: {IMG_PREVIEW.name}")
with col_title:
    st.title("Python Slot Machine")
    st.caption("Runs in your browser with Streamlit.")
    st.caption("Session saves in memory. Download or load a save file anytime.")
    st.caption(f"Mode: {'Hardcore' if st.session_state.hardcore else 'Easy'}")

# Sidebar
with st.sidebar:
    st.header("Settings")
    prev_hard = st.session_state.hardcore
    st.session_state.hardcore = st.toggle(
        "Hardcore mode",
        value=st.session_state.hardcore,
        help="Disables funding and resets, forces balance to 100.",
    )
    if st.session_state.hardcore and not prev_hard:
        st.session_state.balance = 100
        st.session_state.total_deposited = 0
        st.session_state.auto_spinning = False
        st.session_state.auto_spin_remaining = 0
        st.rerun()

    st.session_state.mute = st.toggle("Mute sounds", value=st.session_state.mute)
    bet = st.number_input("Bet per spin", min_value=1, max_value=20, value=5, step=1)

    st.divider()
    if not st.session_state.hardcore:
        st.header("Funds")
        deposit = st.number_input("Amount to add", min_value=1, max_value=100000, value=10, step=1)
        if st.button("Add funds"):
            st.session_state.balance += deposit
            st.session_state.total_deposited += deposit
            st.success(f"Added ${deposit}")
        st.caption(f"Total deposited: ${st.session_state.total_deposited}")
    else:
        st.header("Funds")
        st.caption("Funding disabled in Hardcore.")

    st.divider()
    st.header("Auto spin")
    speed = st.select_slider("Spin speed", options=["Slow", "Normal", "Fast"], value="Normal")
    st.session_state.auto_delay_ms = {"Slow": 900, "Normal": 350, "Fast": 120}[speed]
    auto_rounds = st.number_input("Rounds", min_value=1, max_value=100, value=10, step=1)
    s1, s2 = st.columns(2)
    with s1:
        start_auto = st.button("Start auto spin", disabled=st.session_state.auto_spinning)
    with s2:
        stop_auto = st.button("Stop auto spin", disabled=not st.session_state.auto_spinning)
    if start_auto:
        st.session_state.auto_spinning = True
        st.session_state.auto_spin_remaining = int(auto_rounds)
        st.rerun()
    if stop_auto:
        st.session_state.auto_spinning = False
        st.session_state.auto_spin_remaining = 0
        st.rerun()

    st.divider()
    st.write("Save or load")
    st.download_button("Download save", data=save_blob(), file_name="slot_save.json", mime="application/json")
    up = st.file_uploader("Load save", type=["json"])
    if up is not None:
        load_blob(up)
        st.success("Save loaded")
        st.rerun()

# Balance and counters
st.subheader(f"Balance: ${st.session_state.balance}")
st.text(f"Spins: {st.session_state.spins}   Wins: {st.session_state.wins}")

# Reels placeholders (render after handling actions)
cols = st.columns(3)
ph1 = cols[0].empty()
ph2 = cols[1].empty()
ph3 = cols[2].empty()

# Action buttons
a1, a2, a3 = st.columns([1, 1, 1])
can_spin = st.session_state.balance >= bet
spin_clicked = a1.button("Spin", use_container_width=True, disabled=not can_spin or st.session_state.auto_spinning)
reset_all_clicked = a2.button("Reset balance and stats", use_container_width=True, disabled=st.session_state.hardcore)
reset_stats_clicked = a3.button("Reset stats only", use_container_width=True, disabled=st.session_state.hardcore)

def do_spin():
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

# Handle actions first
if spin_clicked and can_spin and not st.session_state.auto_spinning:
    do_spin()

if st.session_state.auto_spinning:
    if st.session_state.auto_spin_remaining > 0 and st.session_state.balance >= bet:
        st.session_state.auto_spin_remaining -= 1
        do_spin()
        schedule_rerun(st.session_state.auto_delay_ms)
    else:
        st.session_state.auto_spinning = False
        st.session_state.auto_spin_remaining = 0

if reset_all_clicked:
    reset_all()
    st.rerun()
if reset_stats_clicked:
    reset_stats_only()
    st.rerun()

# Now render reels from current state
ph1.metric("Reel 1", st.session_state.last_reels[0])
ph2.metric("Reel 2", st.session_state.last_reels[1])
ph3.metric("Reel 3", st.session_state.last_reels[2])

# Status
if st.session_state.spins > 0:
    if st.session_state.last_win > 0:
        st.success(f"You won ${st.session_state.last_win}")
    else:
        st.info("No win this spin")

# Sounds every run
snd = []
if st.session_state.queue_spin_snd:
    snd.append(js_play_sound(SND_SPIN, muted=st.session_state.mute, delay_ms=0))
if st.session_state.queue_win_snd:
    snd.append(js_play_sound(SND_WIN, muted=st.session_state.mute, delay_ms=250))
if snd:
    st.markdown("".join(snd), unsafe_allow_html=True)
    st.session_state.queue_spin_snd = False
    st.session_state.queue_win_snd = False

st.caption("Symbols: 🍒 🍋 🔔 ⭐ 7️⃣")
