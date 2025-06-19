"""
Game engine for Pokemon TCG Pocket.
"""
import random
import copy
from typing import List, Optional, Sequence
from src.cards.card_loader import load_cards_from_json
import os

from src.models.cards import Card, PokemonCard, Attack, SupporterCard, ItemCard, ToolCard
from src.models.enums import PokemonType, StatusCondition
from src.game.player import Player

class GameEngine:
    """Main game engine that handles game flow and rules."""
    
    def __init__(self, player1: Player, player2: Player):
        """Initialize the game engine."""
        self.players = [player1, player2]
        self.turn = 0
        self.setup_phase = True
        self.setup_complete = [False, False]  # Track if each player has chosen their active Pokemon
        # Decide who goes first with a coin flip
        self.first_player = random.choice([0, 1])

    def setup_game(self) -> None:
        """Set up the game state for both players using a real deck from cards.json."""
        # Load cards from JSON
        card_json_path = os.path.join(os.path.dirname(__file__), '..', 'cards', 'cards.json')
        all_cards = load_cards_from_json(card_json_path)
        # For now, just use the first 20 legal Pokemon cards as the deck
        deck = [card for card in all_cards if hasattr(card, 'attacks')][:20]
        for player in self.players:
            # Ensure each card in the deck is a unique object
            player.deck = [copy.deepcopy(card) for card in deck]
            random.shuffle(player.deck)
            for _ in range(5):
                player.draw_card()
            # Force Grass energy only
            player.energy_type = PokemonType.GRASS
            player.next_energy_type = PokemonType.GRASS

    def generate_deck(self) -> List[Card]:
        """Generate a legal 20-card deck."""
        deck: List[Card] = []
          # Basic Pokemon
        pikachu = PokemonCard("Pikachu", "BAS-025", 60, PokemonType.ELECTRIC)
        pikachu.attacks = [
            Attack("Thunder Shock", 20, 1),
            Attack("Thunderbolt", 50, 2)
        ]
        pikachu.weakness = PokemonType.FIGHTING
        
        raichu_ex = PokemonCard("Raichu-EX", "BAS-026", 180, PokemonType.ELECTRIC, is_ex=True)
        raichu_ex.attacks = [
            Attack("Thunder Wave", 30, 1, ["Electric"],  # Add cost_types explicitly
                  lambda self, opp: (setattr(opp.active, 'status', StatusCondition.PARALYSIS), None)[-1]),
            Attack("Lightning Strike", 120, 3, ["Electric", "Electric", "Electric"])
        ]
        raichu_ex.weakness = PokemonType.FIGHTING
        raichu_ex.can_evolve_from = "Pikachu"
        
        # Create deck
        deck.extend([pikachu] * 4)  # 4 basic Pokemon
        deck.extend([raichu_ex] * 2)  # 2 evolution Pokemon-EX
        
        # Trainer cards
        potion = ItemCard("Potion", 
                         lambda self, target: None if target is None else
                         (setattr(target, 'hp', min(target.hp + 30, target.max_hp)), None)[-1])
        switch = ItemCard("Switch", 
                         lambda self, target: (self.retreat(target), None)[-1] 
                         if target is not None else None)
        power_belt = ToolCard("Power Belt", 
                            lambda pokemon: (setattr(pokemon, 'attack_damage', 
                                                   getattr(pokemon, 'attack_damage', 0) + 10), None)[-1])
        deck.extend([potion, switch, power_belt])
        
        # Supporter cards
        supporter_cards = [
            SupporterCard("Professor's Research", 
                         lambda player: (player.discard_pile.extend(player.hand), 
                                      player.hand.clear(),
                                      player.draw_cards(7), None)[-1]),
            SupporterCard("Lillie", 
                         lambda player: (player.draw_cards(3), None)[-1])
        ]
        deck.extend(supporter_cards * 2)  # 2 copies each
        
        # Fill remaining slots with random trainers
        while len(deck) < 20:
            deck.append(random.choice(supporter_cards))
        
        return deck[:20]  # Ensure exactly 20 cards

    def display_hand(self, player: Player):
        print(f"\n{player.name}'s hand:")
        for idx, card in enumerate(player.hand):
            print(f"  [{idx}] {card.name} ({type(card).__name__})")

    def display_board(self, player: Player):
        print(f"\n{player.name}'s board:")
        def energy_str(poke):
            if not poke or not hasattr(poke, 'attached_energy') or not poke.attached_energy:
                return ""
            return " | Energies: " + ", ".join(f"{t.name}:{n}" for t, n in poke.attached_energy.items() if n > 0)
        if player.active:
            print(f"  Active: {player.active.name} (HP: {player.active.hp}){energy_str(player.active)}")
        else:
            print(f"  Active: None")
        print("  Bench:")
        for idx, poke in enumerate(player.bench):
            print(f"    [{idx}] {poke.name} (HP: {poke.hp}){energy_str(poke)}")

    def display_full_board(self):
        """Display both players' full board state, including hand, active, bench, energies, and tools."""
        for player in self.players:
            print(f"\n=== {player.name}'s Board ===")
            # Hand (show card names only)
            print(f"Hand ({len(player.hand)}): " + ', '.join(card.name for card in player.hand))
            # Active Pokémon
            def poke_details(poke):
                if not poke:
                    return "None"
                energies = [(t.name, n) for t, n in getattr(poke, 'attached_energy', {}).items() if n > 0]
                if energies:
                    energy_str = " | Energies: " + ', '.join(f"{t}:{n}" for t, n in energies)
                else:
                    energy_str = " | Energies: None"
                tool_str = f" | Tool: {poke.attached_tool.name}" if poke.attached_tool else ""
                status_str = f" | Status: {poke.status.name}" if poke.status and poke.status.name != 'NONE' else ""
                return f"{poke.name} (HP: {poke.hp}/{poke.max_hp}){energy_str}{tool_str}{status_str}"
            print(f"Active: {poke_details(player.active)}")
            # Bench
            if player.bench:
                print("Bench:")
                for idx, poke in enumerate(player.bench):
                    print(f"  [{idx}] {poke_details(poke)}")
            else:
                print("Bench: (empty)")
            # (Optional) Discard pile
            # print(f"Discard pile ({len(player.discard_pile)}): " + ', '.join(card.name for card in player.discard_pile))
            print("---------------------------")

    def prompt_choice(self, prompt: str, options: list) -> Optional[int]:
        if not options:
            return None
        while True:
            try:
                choice = input(f"{prompt} (0-{len(options)-1}, or Enter to skip): ")
                if choice == '':
                    return None
                idx = int(choice)
                if 0 <= idx < len(options):
                    return idx
            except Exception:
                pass
            print("Invalid input. Try again.")

    def play_turn(self) -> None:
        """Execute a single turn of the game with all main steps."""
        current_player = self.players[self.turn % 2]
        opponent = self.players[(self.turn + 1) % 2]
        print(f"\nTurn {self.turn + 1}: {current_player.name}'s turn")

        # Show both players' full board state before the turn
        self.display_full_board()

        # 1. Draw card (skip for first player's first turn)
        if self.turn != self.first_player:
            current_player.draw_card()

        # 2. Gain 1 Grass Energy (skip for first player's first turn only)
        # Only skip if this is the very first turn and it's the first player
        if not (self.turn == self.first_player == 0):
            current_player.energy += 1
            current_player.energy_type = PokemonType.GRASS
            current_player.next_energy_type = PokemonType.GRASS
            print(f"Gained 1 GRASS energy. Next turn: GRASS")

        # Show hand and board
        self.display_hand(current_player)
        self.display_board(current_player)

        # Energy attachment step
        if current_player.energy > 0 and current_player.energy_type is not None:
            pokes = [poke for poke in [current_player.active] + current_player.bench if poke]
            print(f"\nYou have {current_player.energy} energy token(s) to attach.")
            while current_player.energy > 0:
                p_idx = self.prompt_choice("Choose a Pokémon to attach energy to", pokes)
                if p_idx is None:
                    break
                current_player.attach_energy(pokes[p_idx], current_player.energy_type)

        # 3. Activate Evolutions (prompt for each possible evolution)
        # Prevent evolution on both players' first turns
        if self.turn >= 2:
            evo_options = [(i, card) for i, card in enumerate(current_player.hand) if isinstance(card, PokemonCard) and card.can_evolve_from]
            for idx, evo_card in evo_options:
                targets = [poke for poke in [current_player.active] + current_player.bench if poke and poke.name == evo_card.can_evolve_from and poke.can_evolve(self.turn)]
                if targets:
                    print(f"Evolution available: {evo_card.name} can evolve {evo_card.can_evolve_from}.")
                    t_idx = self.prompt_choice(f"Choose which to evolve into {evo_card.name}", targets)
                    if t_idx is not None:
                        current_player.evolve_pokemon(evo_card, targets[t_idx], self.turn)
                        print(f"{current_player.name} evolved {targets[t_idx].name} into {evo_card.name}!")
        else:
            print("Evolution is not allowed on either player's first turn.")

        # 4. Play Basic Pokémon to Bench (multi-select, comma-separated indices)
        while len(current_player.bench) < 3:
            basics = [card for card in current_player.hand if isinstance(card, PokemonCard) and not card.can_evolve_from]
            if not basics:
                break
            self.display_hand(current_player)
            print(f"You may add up to {3 - len(current_player.bench)} Pokémon to your Bench this turn.")
            choices = input(f"Select Pokémon to add to Bench (comma-separated indices, Enter to finish): ")
            if choices == '':
                break
            try:
                indices = [int(x.strip()) for x in choices.split(',') if x.strip().isdigit()]
                for idx in sorted(set(indices), reverse=True):
                    if 0 <= idx < len(basics) and len(current_player.bench) < 3:
                        card = basics[idx]
                        if current_player.play_pokemon_to_bench(card, self.turn):
                            print(f"{current_player.name} played {card.name} to the bench.")
            except Exception:
                print("Invalid choice. Try again.")

        # 5. Use Pokémon Abilities (not implemented, placeholder)
        # TODO: Implement ability activation

        # 6. Play Trainers (prompt for each type)
        # Supporter
        supporters = [(i, card) for i, card in enumerate(current_player.hand) if isinstance(card, SupporterCard) and not current_player.supporter_used]
        if supporters:
            self.display_hand(current_player)
            s_idx = self.prompt_choice("Choose a Supporter to play", [card for _, card in supporters])
            if s_idx is not None:
                card = supporters[s_idx][1]
                current_player.play_supporter(card)
                print(f"{current_player.name} played supporter {card.name}.")
        # Items
        while True:
            items = [(i, card) for i, card in enumerate(current_player.hand) if isinstance(card, ItemCard)]
            if not items:
                break
            self.display_hand(current_player)
            i_idx = self.prompt_choice("Choose an Item to play", [card for _, card in items])
            if i_idx is None:
                break
            card = items[i_idx][1]
            current_player.play_item(card)
            print(f"{current_player.name} played item {card.name}.")
        # Tools
        while True:
            tools = [(i, card) for i, card in enumerate(current_player.hand) if isinstance(card, ToolCard)]
            if not tools:
                break
            self.display_hand(current_player)
            t_idx = self.prompt_choice("Choose a Tool to attach", [card for _, card in tools])
            if t_idx is None:
                break
            card = tools[t_idx][1]
            pokes = [poke for poke in [current_player.active] + current_player.bench if poke and not poke.attached_tool]
            if not pokes:
                print("No Pokémon available to attach a tool.")
                break
            p_idx = self.prompt_choice("Choose a Pokémon to attach the tool to", pokes)
            if p_idx is not None:
                current_player.attach_tool(card, pokes[p_idx])
                print(f"{current_player.name} attached tool {card.name} to {pokes[p_idx].name}.")

        # 7. Retreat (prompt to retreat, only if enough energy attached)
        if current_player.active and current_player.bench and not current_player.retreated_this_turn:
            cost = getattr(current_player.active, 'retreat_cost', 1)
            can_retreat = current_player.can_retreat(current_player.active, cost, ['Colorless']*cost)
            if can_retreat:
                print(f"Active: {current_player.active.name}, Bench: {[poke.name for poke in current_player.bench]}")
                r = input(f"Do you want to retreat your active Pokémon? (Cost: {cost} energy, y/N): ").strip().lower()
                if r == 'y':
                    p_idx = self.prompt_choice("Choose a Pokémon from the bench to switch with", current_player.bench)
                    if p_idx is not None:
                        current_player.retreat(current_player.bench[p_idx])

        # 8. Attack (prompt for attack, only if enough energy attached)
        if current_player.active and current_player.active.attacks:
            available_attacks = [i for i, atk in enumerate(current_player.active.attacks) if current_player.can_attack_with(current_player.active, i)]
            if available_attacks:
                print(f"Available attacks for {current_player.active.name}:")
                for i in available_attacks:
                    atk = current_player.active.attacks[i]
                    print(f"  [{i}] {atk.name} (Damage: {atk.damage}, Cost: {atk.cost_types})")
                a_idx = self.prompt_choice("Choose an attack to use", [current_player.active.attacks[i] for i in available_attacks])
                if a_idx is not None:
                    real_idx = available_attacks[a_idx]
                    # Only check for energy, do not remove it unless attack effect says so
                    # current_player.pay_cost(current_player.active, current_player.active.attacks[real_idx].cost_types)  # REMOVE THIS LINE
                    current_player.attack(real_idx, opponent)
                    print(f"{current_player.name}'s {current_player.active.name} used {current_player.active.attacks[real_idx].name}!")
            else:
                print("No attacks available (not enough energy attached).")

        # 9. Status/after-attack triggers
        self.handle_status_effects(current_player)
        opponent.replace_knocked_out()

        # 10. End turn
        current_player.supporter_used = False
        current_player.retreated_this_turn = False
        for pokemon in ([current_player.active] + current_player.bench):
            if pokemon:
                pokemon.evolved_this_turn = False
        current_player.choose_active()  # Auto-promote if needed
        self.turn += 1

        # Show both players' full board state at the end of the turn
        self.display_full_board()

    def handle_status_effects(self, player: Player) -> None:
        """Handle status conditions at the start of turn."""
        if player.active:
            if player.active.status == StatusCondition.SLEEP:
                if random.choice([True, False]):  # Coin flip
                    player.active.status = StatusCondition.NONE
                    print(f"{player.active.name} woke up!")
                else:
                    print(f"{player.active.name} is still asleep")
            
            elif player.active.status == StatusCondition.BURN:
                player.active.hp -= 20
                if random.choice([True, False]):  # Coin flip
                    player.active.status = StatusCondition.NONE
                    print(f"{player.active.name} is no longer burned")
            
            elif player.active.status == StatusCondition.POISON:
                player.active.hp -= 10
                print(f"{player.active.name} took 10 damage from poison")
            
            elif player.active.status == StatusCondition.PARALYSIS:
                player.active.status = StatusCondition.NONE
                print(f"{player.active.name} is no longer paralyzed")

    def is_game_over(self) -> bool:
        """Check if the game is over."""
        return any(p.points >= 3 for p in self.players)

    def get_winner(self) -> Optional[str]:
        """Get the name of the winning player, if any."""
        for p in self.players:
            if p.points >= 3:
                return p.name
        return None

    @property
    def player1(self) -> Player:
        """Get player 1."""
        return self.players[0]
        
    @property
    def player2(self) -> Player:
        """Get player 2."""
        return self.players[1]
        
    @property
    def current_turn(self) -> int:
        """Get the current turn number."""
        return self.turn
        
    @property
    def current_player(self) -> Player:
        """Get the current player."""
        return self.players[(self.turn + self.first_player) % 2]

    def get_valid_active_choices(self, player: Player) -> List[PokemonCard]:
        """Get list of valid Pokemon that can be played as active."""
        return [card for card in player.hand 
                if isinstance(card, PokemonCard) and not card.can_evolve_from]

    def choose_active_pokemon(self, player: Player, card_index: int) -> bool:
        """Choose a Pokemon from hand as active. Returns True if successful."""
        if not self.setup_phase:
            return False
            
        valid_choices = self.get_valid_active_choices(player)
        if not (0 <= card_index < len(valid_choices)):
            return False
            
        chosen_card = valid_choices[card_index]
        player.hand.remove(chosen_card)
        player.active = chosen_card
        
        # Mark this player's setup as complete
        player_idx = self.players.index(player)
        self.setup_complete[player_idx] = True
        
        # Check if setup phase is complete
        if all(self.setup_complete):
            self.setup_phase = False
            
        return True

    @property
    def needs_setup(self) -> bool:
        """Check if any player still needs to choose their active Pokemon."""
        return any(not complete for complete in self.setup_complete)
