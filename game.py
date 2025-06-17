import random
from enum import Enum, auto
from dataclasses import dataclass, field
from typing import List, Optional, Callable, Union, TypeVar, Sequence

# --- Enums ---

class CardType(Enum):
    POKEMON = auto()
    POKEMON_EX = auto()
    SUPPORTER = auto()
    ITEM = auto()
    TOOL = auto()

class StatusCondition(Enum):
    NONE = auto()
    POISON = auto()
    BURN = auto()
    SLEEP = auto()
    PARALYSIS = auto()
    CONFUSION = auto()

class PokemonType(Enum):
    NORMAL = auto()
    FIRE = auto()
    WATER = auto()
    ELECTRIC = auto()
    GRASS = auto()
    FIGHTING = auto()
    PSYCHIC = auto()
    DARKNESS = auto()
    METAL = auto()
    DRAGON = auto()

# --- Card Classes ---

@dataclass
class Attack:
    name: str
    damage: int
    energy_cost: int
    effect: Optional[Callable[['Player', 'Player'], None]] = None

@dataclass
class Ability:
    name: str
    effect: Callable[['Player'], None]

@dataclass
class Card:
    name: str
    card_type: CardType

@dataclass
class PokemonCard(Card):
    hp: int
    max_hp: int
    pokemon_type: PokemonType
    is_ex: bool = False
    status: StatusCondition = StatusCondition.NONE
    weakness: Optional[PokemonType] = None
    attached_tool: Optional['ToolCard'] = None
    attacks: List[Attack] = field(default_factory=list)
    ability: Optional[Ability] = None
    turn_played: int = -1
    evolved_this_turn: bool = False
    can_evolve_from: Optional[str] = None

    def __init__(self, name: str, hp: int, pokemon_type: PokemonType, is_ex: bool = False):
        super().__init__(name, CardType.POKEMON_EX if is_ex else CardType.POKEMON)
        self.hp = hp
        self.max_hp = hp
        self.pokemon_type = pokemon_type
        self.is_ex = is_ex
        self.status = StatusCondition.NONE
        self.weakness = None
        self.attached_tool = None
        self.attacks = []
        self.ability = None
        self.turn_played = -1
        self.evolved_this_turn = False
        self.can_evolve_from = None
        
    def is_knocked_out(self) -> bool:
        return self.hp <= 0
        
    def can_evolve(self, current_turn: int) -> bool:
        return (current_turn > self.turn_played) and not self.evolved_this_turn

@dataclass
class SupporterCard(Card):
    effect: Callable[['Player'], None]

    def __init__(self, name: str, effect: Callable[['Player'], None]):
        super().__init__(name, CardType.SUPPORTER)
        self.effect = effect

@dataclass
class ItemCard(Card):
    effect: Callable[['Player', Optional[PokemonCard]], None]

    def __init__(self, name: str, effect: Callable[['Player', Optional[PokemonCard]], None]):
        super().__init__(name, CardType.ITEM)
        self.effect = effect

@dataclass
class ToolCard(Card):
    effect: Callable[[PokemonCard], None]

    def __init__(self, name: str, effect: Callable[[PokemonCard], None]):
        super().__init__(name, CardType.TOOL)
        self.effect = effect

# --- Player Class ---

class Player:
    def __init__(self, name: str):
        self.name = name
        self.deck: List[Card] = []
        self.hand: List[Card] = []
        self.bench: List[PokemonCard] = []
        self.active: Optional[PokemonCard] = None
        self.energy: int = 0
        self.energy_type: Optional[PokemonType] = None
        self.next_energy_type: Optional[PokemonType] = None
        self.points: int = 0
        self.supporter_used: bool = False
        self.retreated_this_turn: bool = False
        self.discard_pile: List[Card] = []
        
    def draw_card(self) -> Optional[Card]:
        if self.deck:
            drawn = self.deck.pop(0)
            self.hand.append(drawn)
            return drawn
        return None

    def draw_cards(self, count: int) -> List[Card]:
        drawn = []
        for _ in range(count):
            card = self.draw_card()
            if card:
                drawn.append(card)
        return drawn

    def play_pokemon_to_bench(self, card: PokemonCard, turn: int) -> bool:
        if len(self.bench) < 3 and card in self.hand:
            card.turn_played = turn
            self.bench.append(card)
            self.hand.remove(card)
            return True
        return False

    def evolve_pokemon(self, evolution: PokemonCard, target: PokemonCard, turn: int) -> bool:
        if (evolution.can_evolve_from == target.name and 
            target.can_evolve(turn) and not target.evolved_this_turn):
            # Keep the tool if any
            evolution.attached_tool = target.attached_tool
            evolution.turn_played = turn
            evolution.evolved_this_turn = True
            
            # Replace the target with evolution
            if target == self.active:
                self.active = evolution
            else:
                idx = self.bench.index(target)
                self.bench[idx] = evolution
                
            self.hand.remove(evolution)
            self.discard_pile.append(target)
            return True
        return False

    def choose_active(self) -> None:
        if not self.active and self.bench:
            self.active = self.bench.pop(0)

    def retreat(self, pokemon_to_active: PokemonCard) -> bool:
        if (not self.retreated_this_turn and self.energy >= 1 and 
            pokemon_to_active in self.bench and self.active):
            self.energy -= 1
            idx = self.bench.index(pokemon_to_active)
            self.bench[idx] = self.active
            self.active = pokemon_to_active
            self.retreated_this_turn = True
            return True
        return False

    def play_supporter(self, card: SupporterCard) -> bool:
        if not self.supporter_used and card in self.hand:
            print(f"{self.name} uses Supporter: {card.name}")
            card.effect(self)  # Apply effect
            self.hand.remove(card)
            self.discard_pile.append(card)
            self.supporter_used = True
            return True
        return False

    def play_item(self, card: ItemCard, target: Optional[PokemonCard] = None) -> bool:
        if card in self.hand:
            print(f"{self.name} uses Item: {card.name}")
            card.effect(self, target)  # Apply effect
            self.hand.remove(card)
            self.discard_pile.append(card)
            return True
        return False

    def attach_tool(self, tool: ToolCard, pokemon: PokemonCard) -> bool:
        if tool in self.hand:
            if pokemon.attached_tool:
                self.discard_pile.append(pokemon.attached_tool)
            pokemon.attached_tool = tool
            self.hand.remove(tool)
            return True
        return False

    def replace_knocked_out(self) -> None:
        if not self.active or self.active.is_knocked_out():
            if self.active:
                self.discard_pile.append(self.active)
            self.active = None
            if self.bench:
                self.active = self.bench.pop(0)

    def update_status_conditions(self) -> None:
        for pokemon in [self.active] + self.bench:
            if not pokemon:
                continue
                
            if pokemon.status == StatusCondition.POISON:
                pokemon.hp -= 10
            elif pokemon.status == StatusCondition.BURN:
                pokemon.hp -= 20
                if random.choice([True, False]):  # Coin flip
                    pokemon.status = StatusCondition.NONE
            elif pokemon.status == StatusCondition.PARALYSIS:
                pokemon.status = StatusCondition.NONE
            elif pokemon.status == StatusCondition.SLEEP:
                if random.choice([True, False]):  # Coin flip
                    pokemon.status = StatusCondition.NONE

    def can_attack(self) -> bool:
        return (self.active is not None and 
                self.active.status not in [StatusCondition.SLEEP, StatusCondition.PARALYSIS] and 
                any(self.energy >= attack.energy_cost for attack in self.active.attacks))

    def attack(self, attack_index: int, opponent: 'Player') -> bool:
        if not self.can_attack() or not opponent.active:
            return False

        if not self.active or not self.active.attacks:
            return False
        attack = self.active.attacks[attack_index]
        if self.energy < attack.energy_cost:
            return False
            
        print(f"{self.name}'s {self.active.name} uses {attack.name}!")
        
        damage = attack.damage
        if opponent.active.weakness == self.active.pokemon_type:
            damage += 20
            
        # Handle confusion
        if self.active.status == StatusCondition.CONFUSION:
            if random.choice([True, False]):  # Coin flip
                print(f"{self.active.name} hurt itself in confusion!")
                self.active.hp -= 30
                self.energy -= attack.energy_cost
                return True
                
        # Deal damage
        opponent.active.hp -= damage
        print(f"{opponent.active.name} takes {damage} damage!")
        
        # Apply attack effects if any
        if attack.effect:
            attack.effect(self, opponent)
            
        self.energy -= attack.energy_cost
        
        # Check for knockout
        if opponent.active.is_knocked_out():
            print(f"{opponent.active.name} is knocked out!")
            self.points += 2 if opponent.active.is_ex else 1
            opponent.active = None
            
        return True

# --- Game Engine ---

class GameEngine:
    def __init__(self, player1: Player, player2: Player):
        self.players = [player1, player2]
        self.turn = 0
        # Decide who goes first with a coin flip
        self.first_player = random.choice([0, 1])

    def setup_game(self) -> None:
        # Generate decks with fixed size of 20 cards
        for player in self.players:
            player.deck = self.generate_deck()
            if len(player.deck) != 20:
                raise ValueError("Deck must contain exactly 20 cards")
            random.shuffle(player.deck)
            
            # Draw opening hand
            for _ in range(5):
                player.draw_card()
                
            # Set up initial energy type
            player_types = {card.pokemon_type for card in player.deck 
                          if isinstance(card, PokemonCard)}
            if len(player_types) == 1:
                player.energy_type = list(player_types)[0]
            else:
                player.energy_type = random.choice(list(player_types))
            player.next_energy_type = random.choice(list(player_types))

    def generate_deck(self) -> List[Card]:
        """Generate a legal 20-card deck"""
        deck: List[Card] = []
        
        # Basic Pokemon
        pikachu = PokemonCard("Pikachu", 60, PokemonType.ELECTRIC)
        pikachu.attacks = [
            Attack("Thunder Shock", 20, 1),
            Attack("Thunderbolt", 50, 2)
        ]
        pikachu.weakness = PokemonType.FIGHTING
        
        raichu_ex = PokemonCard("Raichu-EX", 180, PokemonType.ELECTRIC, is_ex=True)
        raichu_ex.attacks = [
            Attack("Thunder Wave", 30, 1, 
                  lambda self, opp: setattr(opp.active, 'status', StatusCondition.PARALYSIS)),
            Attack("Lightning Strike", 120, 3)
        ]
        raichu_ex.weakness = PokemonType.FIGHTING
        raichu_ex.can_evolve_from = "Pikachu"
        
        # Create deck
        deck.extend([pikachu] * 4)  # 4 basic Pokemon
        deck.extend([raichu_ex] * 2)  # 2 evolution Pokemon-EX
        
        # Trainer cards
        deck.extend([
            ItemCard("Potion", 
                    lambda self, target: setattr(target, 'hp', min(target.hp + 30, target.max_hp)) if target is not None else None),
            ItemCard("Switch", 
                    lambda self, target: (self.retreat(target), None)[-1] if target is not None else None),
            ToolCard("Power Belt", 
                    lambda pokemon: setattr(pokemon, 'attack_damage', 
                                         getattr(pokemon, 'attack_damage', 0) + 10))
        ])
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

    def play_turn(self) -> None:
        current_player = self.players[self.turn % 2]
        opponent = self.players[(self.turn + 1) % 2]
        print(f"\nTurn {self.turn + 1}: {current_player.name}'s turn")

        # Reset turn-based flags
        current_player.supporter_used = False
        current_player.retreated_this_turn = False
        
        # Draw card (skip for first player's first turn)
        if self.turn != self.first_player:
            current_player.draw_card()
        
        # Get energy (skip for first player's first turn)
        if self.turn != self.first_player:
            current_player.energy += 1
            current_player.energy_type = current_player.next_energy_type
            # Update next turn's energy type
            player_types = {card.pokemon_type for card in current_player.deck 
                          if isinstance(card, PokemonCard)}
            if player_types:  # Check if there are any Pokemon types left
                current_player.next_energy_type = random.choice(list(player_types))
                if current_player.energy_type:
                    print(f"Gained 1 {current_player.energy_type.name} energy. "
                          f"Next turn: {current_player.next_energy_type.name}")
        
        # Reset evolution flags for all Pokemon
        for pokemon in ([current_player.active] + current_player.bench):
            if pokemon:
                pokemon.evolved_this_turn = False
        
        # Main phase actions
        self.handle_status_effects(current_player)
        current_player.choose_active()  # Auto-promote if needed
          # Battle phase
        if current_player.can_attack() and current_player.active and current_player.active.attacks:
            # For now, always use the first available attack
            for i, attack in enumerate(current_player.active.attacks):
                if current_player.energy >= attack.energy_cost:
                    current_player.attack(i, opponent)
                    break
        
        opponent.replace_knocked_out()
        self.turn += 1

    def handle_status_effects(self, player: Player) -> None:
        """Handle status conditions at the start of turn"""
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
        return any(p.points >= 3 for p in self.players)

    def get_winner(self) -> Optional[str]:
        for p in self.players:
            if p.points >= 3:
                return p.name
        return None

if __name__ == "__main__":
    # Example game setup and play
    player1 = Player("Player 1")
    player2 = Player("Player 2")
    game = GameEngine(player1, player2)
    game.setup_game()
    
    while not game.is_game_over():
        game.play_turn()
        
    winner = game.get_winner()
    if winner:
        print(f"\n{winner} wins the game!")
