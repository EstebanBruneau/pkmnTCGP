from flask import Flask, render_template, redirect, url_for, session, request
import os
import sys

# Add src to the path so we can import game logic
src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src'))
if src_path not in sys.path:
    sys.path.insert(0, src_path)

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from src.game.engine import GameEngine
from src.game.player import Player

app = Flask(__name__)
app.secret_key = "supersecretkey"  # For session management

game = None  # Global for demo; for production, use a better state manager

@app.route("/", methods=["GET", "POST"])
def index():
    global game
    if request.method == "POST":
        p1 = Player(request.form["player1"])
        p2 = Player(request.form["player2"])
        game = GameEngine(p1, p2)
        game.setup_game()
        session["started"] = True
        return redirect(url_for("game_view"))
    return render_template("index.html")

@app.route("/game")
def game_view():
    global game
    if not session.get("started") or game is None:
        return redirect(url_for("index"))
    # For now, just show the board state as text
    # You may want to add a method to GameEngine to return board state as a string
    import io
    import contextlib
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        game.display_full_board()
    board_state = buf.getvalue()
    return render_template("game.html", board_state=board_state)

if __name__ == "__main__":
    app.run(debug=True)
