import tkinter as tk
import random
import json
import os
import threading
import time
from playsound import playsound
from tkinter import messagebox

MAX_LINES = 3
MAX_BET = 100
MIN_BET = 1
ROWS = 3
COLS = 3

SAVE_FILE = "data/save_data.json"
SPIN_SOUND = "assets/sound/spin.wav"
WIN_SOUND = "assets/sound/win.wav"

sound_enabled = True
auto_spin_count = 0
hardcore_mode = True

symbol_count = {
    "A": 2,
    "B": 4,
    "C": 6,
    "D": 8
}

symbol_value = {
    "A": 5,
    "B": 4,
    "C": 3,
    "D": 2
}

def toggle_mode():
    global hardcore_mode
    hardcore_mode = not hardcore_mode
    mode_label.config(text=f"Mode: {'HARDCORE' if hardcore_mode else 'CASUAL'}")
    root.config(bg="#550000" if hardcore_mode else "#1e1e1e")
    header.config(bg=root["bg"])
    subtext.config(bg=root["bg"])
    balance_label.config(bg=root["bg"])
    result_label.config(bg=root["bg"])
    win_lines_label.config(bg=root["bg"])
    stats_label.config(bg=root["bg"])
    for frame in [deposit_frame, lines_frame, bet_frame, auto_frame, slots_frame]:
        frame.config(bg=root["bg"])

def check_winnings(columns, lines, bet, values):
    winnings = 0
    winnings_lines = []
    for line in range(lines):
        symbol = columns[0][line]
        for column in columns:
            if column[line] != symbol:
                break
        else:
            winnings += values[symbol] * bet
            winnings_lines.append(line + 1)
    return winnings, winnings_lines

def get_slot_machine_spin(rows, cols, symbols):
    all_symbols = [s for s, count in symbols.items() for _ in range(count)]
    columns = []
    for _ in range(cols):
        current_symbols = all_symbols[:]
        column = [current_symbols.pop(random.randint(0, len(current_symbols) - 1)) for _ in range(rows)]
        columns.append(column)
    return columns

def load_game():
    if not os.path.exists(SAVE_FILE):
        return {"balance": 0, "total_spins": 0, "total_wins": 0, "biggest_win": 0}
    with open(SAVE_FILE, "r") as f:
        return json.load(f)

def save_game():
    with open(SAVE_FILE, "w") as f:
        json.dump(stats, f, indent=4)

def reset_stats():
    if hardcore_mode:
        messagebox.showinfo("Hardcore Mode", "Stat reset is disabled in Hardcore Mode.")
        return
    stats["total_spins"] = 0
    stats["total_wins"] = 0
    stats["biggest_win"] = 0
    update_stats_display()
    save_game()

def reset_balance():
    if hardcore_mode:
        messagebox.showinfo("Hardcore Mode", "Balance reset is disabled in Hardcore Mode.")
        return
    confirm = messagebox.askyesno("Reset Balance", "Are you sure you want to reset your balance to $500?")
    if confirm:
        stats["balance"] = 500
        update_balance(0)

def update_balance(amount):
    stats["balance"] += amount
    balance_label.config(text=f"Balance: ${stats['balance']}")
    save_game()

def deposit():
    try:
        amount = int(deposit_entry.get())
        if amount > 0:
            update_balance(amount)
            deposit_entry.delete(0, tk.END)
    except ValueError:
        pass

def toggle_sound():
    global sound_enabled
    sound_enabled = not sound_enabled
    mute_button.config(text="🔊 Sound: ON" if sound_enabled else "🔇 Sound: OFF")

def spin(auto=False):
    def spin_process():
        global auto_spin_count
        try:
            lines = int(lines_entry.get())
            bet = int(bet_entry.get())
            total_bet = lines * bet

            if lines < 1 or lines > MAX_LINES or bet < MIN_BET or bet > MAX_BET:
                result_label.config(text="Invalid bet or lines.")
                auto_spin_count = 0
                return

            if total_bet > stats["balance"]:
                result_label.config(text="Insufficient balance.")
                auto_spin_count = 0
                return

            if sound_enabled:
                playsound(SPIN_SOUND)

            slots = get_slot_machine_spin(ROWS, COLS, symbol_count)
            display_slot_machine(slots)

            winnings, win_lines = check_winnings(slots, lines, bet, symbol_value)
            update_balance(winnings - total_bet)

            stats["total_spins"] += 1
            result_label.config(text=f"You won: ${winnings}")
            win_lines_label.config(text="Winning Lines: " + (", ".join(map(str, win_lines)) if win_lines else "None"))
            update_stats_display()

            if winnings > 0:
                if sound_enabled:
                    threading.Thread(target=playsound, args=(WIN_SOUND,), daemon=True).start()
                stats["total_wins"] += 1
                stats["biggest_win"] = max(stats["biggest_win"], winnings)

            save_game()

            if auto and auto_spin_count > 1:
                auto_spin_count -= 1
                time.sleep(1)
                spin(auto=True)
            else:
                auto_spin_count = 0

        except ValueError:
            result_label.config(text="Please enter valid numbers.")
            auto_spin_count = 0

    threading.Thread(target=spin_process, daemon=True).start()

def start_auto_spin():
    global auto_spin_count
    try:
        count = int(auto_spin_entry.get())
        if count > 0:
            auto_spin_count = count
            spin(auto=True)
    except ValueError:
        result_label.config(text="Enter a valid number of auto spins.")

def update_stats_display():
    win_rate = (stats["total_wins"] / stats["total_spins"] * 100) if stats["total_spins"] else 0
    stats_label.config(text=(
        f"Total Spins: {stats['total_spins']}\n"
        f"Wins: {stats['total_wins']}\n"
        f"Biggest Win: ${stats['biggest_win']}\n"
        f"Win Rate: {win_rate:.1f}%"
    ))

def display_slot_machine(columns):
    for widget in slots_frame.winfo_children():
        widget.destroy()
    for r in range(ROWS):
        for c in range(COLS):
            label = tk.Label(slots_frame, text=columns[c][r], font=("Courier", 20), width=4, height=2, bg="#333", fg="lime", relief="groove")
            label.grid(row=r, column=c, padx=10, pady=10)

stats = load_game()

root = tk.Tk()
root.title("🎰 Slot Machine Game")
root.geometry("600x960")
root.config(bg="#550000" if hardcore_mode else "#1e1e1e")

mode_label = tk.Label(root, text=f"Mode: {'HARDCORE' if hardcore_mode else 'CASUAL'}", font=("Helvetica", 10, "bold"), fg="white", bg=root["bg"])
mode_label.pack(pady=2)
tk.Button(root, text="Toggle Mode ⚙️", command=toggle_mode, bg="#444", fg="white").pack(pady=2)

header = tk.Label(root, text="🎰 Python Slot Machine", font=("Helvetica", 24, "bold"), fg="white", bg=root["bg"])
header.pack(pady=10)
subtext = tk.Label(root, text="Deposit, bet, and spin to win!", font=("Helvetica", 14), fg="gray", bg=root["bg"])
subtext.pack()

balance_label = tk.Label(root, text=f"Balance: ${stats['balance']}", font=("Helvetica", 16), fg="white", bg=root["bg"])
balance_label.pack(pady=5)

deposit_frame = tk.Frame(root, bg=root["bg"])
deposit_frame.pack(pady=10)
tk.Label(deposit_frame, text="Deposit:", fg="white", bg=root["bg"]).pack(side="left")
deposit_entry = tk.Entry(deposit_frame)
deposit_entry.pack(side="left", padx=5)
tk.Button(deposit_frame, text="Add", command=deposit).pack(side="left")

lines_frame = tk.Frame(root, bg=root["bg"])
lines_frame.pack(pady=5)
tk.Label(lines_frame, text=f"Lines (1-{MAX_LINES}):", fg="white", bg=root["bg"]).pack(side="left")
lines_entry = tk.Entry(lines_frame, width=5)
lines_entry.pack(side="left", padx=5)

bet_frame = tk.Frame(root, bg=root["bg"])
bet_frame.pack(pady=5)
tk.Label(bet_frame, text=f"Bet per line (${MIN_BET}-{MAX_BET}):", fg="white", bg=root["bg"]).pack(side="left")
bet_entry = tk.Entry(bet_frame, width=5)
bet_entry.pack(side="left", padx=5)

tk.Button(root, text="Spin 🎲", font=("Helvetica", 14), bg="lime", fg="black", command=spin).pack(pady=10)

auto_frame = tk.Frame(root, bg=root["bg"])
auto_frame.pack(pady=5)
tk.Label(auto_frame, text="Auto Spins:", fg="white", bg=root["bg"]).pack(side="left")
auto_spin_entry = tk.Entry(auto_frame, width=5)
auto_spin_entry.pack(side="left", padx=5)
tk.Button(auto_frame, text="Start Auto Spin 🔁", command=start_auto_spin).pack(side="left")

mute_button = tk.Button(root, text="🔊 Sound: ON", font=("Helvetica", 12), command=toggle_sound, bg="#444", fg="white")
mute_button.pack(pady=5)

reset_button = tk.Button(root, text="🧹 Reset Stats", font=("Helvetica", 12), command=reset_stats, bg="#555", fg="white")
reset_button.pack(pady=5)
reset_balance_button = tk.Button(root, text="💵 Reset Balance", font=("Helvetica", 12), command=reset_balance, bg="#555", fg="white")
reset_balance_button.pack(pady=5)

result_label = tk.Label(root, text="", font=("Helvetica", 14), fg="white", bg=root["bg"])
result_label.pack()
win_lines_label = tk.Label(root, text="", font=("Helvetica", 12), fg="gray", bg=root["bg"])
win_lines_label.pack()

slots_frame = tk.Frame(root, bg=root["bg"])
slots_frame.pack(pady=20)

stats_label = tk.Label(root, text="", font=("Helvetica", 12), fg="white", bg=root["bg"])
stats_label.pack(pady=10)
update_stats_display()

root.mainloop()
