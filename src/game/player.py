"""
Player model for Pokemon TCG Pocket.
"""
import random
from typing import List, Optional, cast

from ..models.cards import Card, PokemonCard, SupporterCard, ItemCard, ToolCard
from ..models.enums import StatusCondition, PokemonType

class Player:
    """Represents a player in the game."""
    
    def __init__(self, name: str):
        """Initialize a player."""
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
        """Draw a card from the deck."""
        if self.deck:
            drawn = self.deck.pop(0)
            self.hand.append(drawn)
            return drawn
        return None

    def draw_cards(self, count: int) -> List[Card]:
        """Draw multiple cards from the deck."""
        drawn = []
        for _ in range(count):
            card = self.draw_card()
            if card:
                drawn.append(card)
        return drawn

    def play_pokemon_to_bench(self, card: PokemonCard, turn: int) -> bool:
        """Play a Pokemon card to the bench."""
        if len(self.bench) < 3 and card in self.hand:
            card.turn_played = turn
            self.bench.append(card)
            self.hand.remove(card)
            return True
        return False

    def evolve_pokemon(self, evolution: PokemonCard, target: PokemonCard, turn: int) -> bool:
        """Evolve a Pokemon with an evolution card."""
        if (evolution.can_evolve_from == target.name and 
            target.can_evolve(turn) and not target.evolved_this_turn):
            # Keep the tool and attached energy
            evolution.attached_tool = target.attached_tool
            evolution.attached_energy = dict(getattr(target, 'attached_energy', {}))
            evolution.status = target.status
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
        """Choose a Pokemon from the bench to be active."""
        if not self.active and self.bench:
            self.active = self.bench.pop(0)

    def attach_energy(self, pokemon: PokemonCard, energy_type: PokemonType) -> bool:
        """Attach energy to a Pokemon."""
        if self.energy > 0:
            if not hasattr(pokemon, 'attached_energy'):
                pokemon.attached_energy = {}
            pokemon.attached_energy[energy_type] = pokemon.attached_energy.get(energy_type, 0) + 1
            self.energy -= 1
            print(f"Attached {energy_type.name} energy to {pokemon.name}.")
            return True
        return False

    def can_pay_cost(self, pokemon: PokemonCard, cost_types: list) -> bool:
        """Check if the cost for an attack or retreat can be paid."""
        if not hasattr(pokemon, 'attached_energy'):
            return False
        attached = dict(pokemon.attached_energy)
        for c in cost_types:
            if c == 'Colorless':
                # Use any available energy
                if sum(attached.values()) == 0:
                    return False
                # Remove one energy of any type
                for t in list(attached.keys()):
                    if attached[t] > 0:
                        attached[t] -= 1
                        break
            else:
                t = PokemonType[c.upper()] if c.upper() in PokemonType.__members__ else None
                if not t or attached.get(t, 0) == 0:
                    return False
                attached[t] -= 1
        return True

    def pay_cost(self, pokemon: PokemonCard, cost_types: list) -> bool:
        """Pay the cost for an attack or retreat."""
        if not hasattr(pokemon, 'attached_energy'):
            return False
        attached = pokemon.attached_energy
        for c in cost_types:
            if c == 'Colorless':
                for t in list(attached.keys()):
                    if attached[t] > 0:
                        attached[t] -= 1
                        break
            else:
                t = PokemonType[c.upper()] if c.upper() in PokemonType.__members__ else None
                if not t or attached.get(t, 0) == 0:
                    return False
                attached[t] -= 1
        return True

    def can_attack_with(self, pokemon: PokemonCard, attack_idx: int) -> bool:
        """Check if a Pokemon can attack."""
        if not pokemon or not hasattr(pokemon, 'attached_energy'):
            return False
        if attack_idx >= len(pokemon.attacks):
            return False
        return self.can_pay_cost(pokemon, pokemon.attacks[attack_idx].cost_types)

    def can_retreat(self, pokemon: PokemonCard, retreat_cost: int, retreat_types: list) -> bool:
        """Check if a Pokemon can retreat."""
        # For now, treat retreat cost as colorless
        if not hasattr(pokemon, 'attached_energy'):
            return False
        total_energy = sum(pokemon.attached_energy.values())
        return total_energy >= retreat_cost

    def retreat(self, pokemon_to_active: PokemonCard) -> bool:
        """Retreat the active Pokemon to the bench."""
        if (not self.retreated_this_turn and self.active and self.can_retreat(self.active, getattr(self.active, 'retreat_cost', 1), ['Colorless'])
            and pokemon_to_active in self.bench):
            # Pay retreat cost (remove energy)
            attached = self.active.attached_energy
            cost = getattr(self.active, 'retreat_cost', 1)
            for _ in range(cost):
                for t in list(attached.keys()):
                    if attached[t] > 0:
                        attached[t] -= 1
                        break
            idx = self.bench.index(pokemon_to_active)
            self.bench[idx] = self.active
            self.active = pokemon_to_active
            self.retreated_this_turn = True
            print(f"{self.name} retreated to {self.active.name}.")
            return True
        return False

    def play_supporter(self, card: SupporterCard) -> bool:
        """Play a Supporter card."""
        if not self.supporter_used and card in self.hand:
            print(f"{self.name} uses Supporter: {card.name}")
            card.effect(self)  # Apply effect
            self.hand.remove(card)
            self.discard_pile.append(card)
            self.supporter_used = True
            return True
        return False

    def play_item(self, card: ItemCard, target: Optional[PokemonCard] = None) -> bool:
        """Play an Item card."""
        if card in self.hand:
            print(f"{self.name} uses Item: {card.name}")
            card.effect(self, target)  # Apply effect
            self.hand.remove(card)
            self.discard_pile.append(card)
            return True
        return False

    def attach_tool(self, tool: ToolCard, pokemon: PokemonCard) -> bool:
        """Attach a Tool card to a Pokemon."""
        if tool in self.hand:
            if pokemon.attached_tool:
                self.discard_pile.append(pokemon.attached_tool)
            pokemon.attached_tool = tool
            self.hand.remove(tool)
            return True
        return False

    def replace_knocked_out(self) -> None:
        """Replace a knocked out active Pokemon."""
        if not self.active or self.active.is_knocked_out():
            if self.active:
                self.discard_pile.append(self.active)
            self.active = None
            if self.bench:
                self.active = self.bench.pop(0)

    def update_status_conditions(self) -> None:
        """Update status conditions for all Pokemon."""
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
        """Check if the active Pokemon can attack."""
        return (self.active is not None and 
                self.active.status not in [StatusCondition.SLEEP, StatusCondition.PARALYSIS] and 
                any(self.energy >= attack.energy_cost for attack in self.active.attacks))

    def attack(self, attack_index: int, opponent: 'Player') -> bool:
        """Use an attack on the opponent's active Pokemon."""
        if not self.active or not self.can_attack_with(self.active, attack_index) or not opponent.active:
            return False

        if not self.active or not self.active.attacks:
            return False
        
        attack = self.active.attacks[attack_index]
        print(f"{self.name}'s {self.active.name} uses {attack.name}!")

        # Calculate base damage
        damage = attack.damage
        # Check for coin flip bonus damage (set by effect)
        bonus = getattr(self.active, '_bonus_damage', 0)
        if bonus:
            damage += bonus
            if hasattr(self.active, '_bonus_damage'):
                delattr(self.active, '_bonus_damage')  # Remove after use
        if opponent.active.weakness == self.active.pokemon_type:
            damage += 20

        # TODO: Check for active item/tool/supporter effects that prevent or reduce damage
        # (Add hooks here in the future)

        # Handle confusion
        if self.active.status == StatusCondition.CONFUSION:
            if random.random() < 0.5:  # 50% chance
                print(f"{self.active.name} hurt itself in confusion!")
                self.active.hp -= 30
                return True

        # Deal damage (unless prevented/reduced by effects)
        opponent.active.hp -= damage
        print(f"{opponent.active.name} takes {damage} damage! (HP now {opponent.active.hp}/{opponent.active.max_hp})")

        # Apply attack effects if any
        if attack.effect:
            attack.effect(self, opponent)

        # Check for knockout
        if opponent.active.is_knocked_out():
            print(f"{opponent.active.name} is knocked out!")
            self.points += 2 if opponent.active.is_ex else 1
            opponent.active = None

        return True
