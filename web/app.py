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
from src.models.cards import PokemonCard

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
        
    return render_template(
        "game.html",
        game=game,
        player1=game.player1,
        player2=game.player2,
        current_turn=game.current_turn,
        current_player=game.current_player,
        setup_phase=game.setup_phase,
        needs_setup=game.needs_setup
    )

@app.route("/choose_active/<int:player_num>/<int:card_idx>")
def choose_active(player_num, card_idx):
    global game
    if not session.get("started") or game is None:
        return redirect(url_for("index"))
        
    player = game.players[player_num - 1]  # Convert to 0-based index
    
    # Only allow choice during setup phase
    if not game.setup_phase or player.active is not None:
        return "Cannot choose active Pokémon at this time", 400
        
    # Validate card choice
    if not (0 <= card_idx < len(player.hand)):
        return "Invalid card index", 400
        
    chosen_card = player.hand[card_idx]
    if not (isinstance(chosen_card, PokemonCard) and not chosen_card.can_evolve_from):
        return "Invalid card choice - must be a basic Pokémon", 400
        
    # Move card from hand to active position
    player.hand.remove(chosen_card)
    player.active = chosen_card
    
    # Mark this player's setup as complete
    player_idx = game.players.index(player)
    game.setup_complete[player_idx] = True
    
    # Check if setup phase is complete
    if all(game.setup_complete):
        game.setup_phase = False
        
    return redirect(url_for("game_view"))

if __name__ == "__main__":
    app.run(debug=True)
