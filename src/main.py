"""
Main entry point for Pokemon TCG Pocket game.
"""
from src.game.engine import GameEngine
from src.game.player import Player
import random

def choose_starting_pokemon(player):
    print(f"\n{player.name}, choose your starting Active Pokémon:")
    basics = [card for card in player.hand if hasattr(card, 'can_evolve_from') and not card.can_evolve_from]
    for idx, card in enumerate(basics):
        print(f"  [{idx}] {card.name} (HP: {card.hp})")
    while True:
        choice = input(f"Select Active Pokémon (0-{len(basics)-1}): ")
        try:
            idx = int(choice)
            if 0 <= idx < len(basics):
                chosen = basics[idx]
                player.active = chosen
                player.hand.remove(chosen)
                print(f"{player.name} chose {chosen.name} as Active Pokémon!")
                break
        except Exception:
            pass
        print("Invalid choice. Try again.")
    # Optionally put up to 3 on bench
    print(f"\n{player.name}, choose up to 3 Pokémon for your Bench (press Enter to finish):")
    while len(player.bench) < 3:
        basics = [card for card in player.hand if hasattr(card, 'can_evolve_from') and not card.can_evolve_from]
        if not basics:
            break
        for idx, card in enumerate(basics):
            print(f"  [{idx}] {card.name} (HP: {card.hp})")
        choices = input(f"Select Pokémon to add to Bench (comma-separated indices, Enter to finish): ")
        if choices == '':
            break
        try:
            indices = [int(x.strip()) for x in choices.split(',') if x.strip().isdigit()]
            for idx in sorted(set(indices), reverse=True):
                if 0 <= idx < len(basics) and len(player.bench) < 3:
                    chosen = basics[idx]
                    player.bench.append(chosen)
                    player.hand.remove(chosen)
                    print(f"Added {chosen.name} to Bench.")
        except Exception:
            print("Invalid choice. Try again.")

def ensure_basic_in_hand(player):
    # Mulligan until at least one basic Pokémon is in hand
    while True:
        basics = [card for card in player.hand if hasattr(card, 'can_evolve_from') and not card.can_evolve_from]
        if basics:
            break
        print(f"{player.name} has no Basic Pokémon in hand! Mulligan...")
        player.deck.extend(player.hand)
        player.hand.clear()
        random.shuffle(player.deck)
        for _ in range(5):
            player.draw_card()

def main():
    """Run the main game loop."""
    print("Welcome to Pokemon TCG Pocket!")
    print("==============================")
    
    # Set up players
    player1_name = input("Enter name for Player 1: ") or "Player 1"
    player2_name = input("Enter name for Player 2: ") or "Player 2"
    
    player1 = Player(player1_name)
    player2 = Player(player2_name)
    
    # Initialize game
    game = GameEngine(player1, player2)
    game.setup_game()
    # Ensure both players have at least one basic Pokémon in hand
    ensure_basic_in_hand(player1)
    ensure_basic_in_hand(player2)
    # Let each player choose their starting Pokémon
    choose_starting_pokemon(player1)
    choose_starting_pokemon(player2)
    
    # Main game loop
    while not game.is_game_over():
        game.play_turn()
        input("Press Enter to continue...")  # Pause between turns
        
    # Game over
    winner = game.get_winner()
    if winner:
        print(f"\nCongratulations! {winner} wins the game!")
    
if __name__ == "__main__":
    main()
