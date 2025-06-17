"""
Base card models for Pokemon TCG Pocket.
"""
from dataclasses import dataclass, field
from typing import Optional, Callable, List, TYPE_CHECKING

if TYPE_CHECKING:
    from ..game.player import Player

from .enums import CardType, StatusCondition, PokemonType

@dataclass
class Attack:
    """Represents a Pokemon's attack."""
    name: str
    damage: int
    energy_cost: int
    cost_types: List[str] = field(default_factory=list)  # e.g. ["Grass", "Colorless"]
    effect: Optional[Callable [['Player', 'Player'], None]] = None

@dataclass
class Ability:
    """Represents a Pokemon's ability."""
    name: str
    effect: Callable [['Player'], None]

@dataclass
class Card:
    """Base class for all cards."""
    name: str
    card_type: CardType

@dataclass
class PokemonCard(Card):
    """Represents a Pokemon card."""
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
    attached_energy: dict = field(default_factory=dict)  # {PokemonType: int}
    retreat_cost: int = 1

    def __init__(self, name: str, hp: int, pokemon_type: PokemonType, is_ex: bool = False):
        """Initialize a Pokemon card."""
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
        self.attached_energy = {}
        self.retreat_cost = 1
        
    def is_knocked_out(self) -> bool:
        """Check if the Pokemon is knocked out."""
        return self.hp <= 0
        
    def can_evolve(self, current_turn: int) -> bool:
        """Check if the Pokemon can evolve this turn."""
        return (current_turn > self.turn_played) and not self.evolved_this_turn

@dataclass
class SupporterCard(Card):
    """Represents a Supporter card."""
    effect: Callable [['Player'], None]

    def __init__(self, name: str, effect: Callable [['Player'], None]):
        """Initialize a Supporter card."""
        super().__init__(name, CardType.SUPPORTER)
        self.effect = effect

@dataclass
class ItemCard(Card):
    """Represents an Item card."""
    effect: Callable [['Player', Optional[PokemonCard]], None]

    def __init__(self, name: str, effect: Callable [['Player', Optional[PokemonCard]], None]):
        """Initialize an Item card."""
        super().__init__(name, CardType.ITEM)
        self.effect = effect

@dataclass
class ToolCard(Card):
    """Represents a Tool card that can be attached to Pokemon."""
    effect: Callable [[PokemonCard], None]

    def __init__(self, name: str, effect: Callable [[PokemonCard], None]):
        """Initialize a Tool card."""
        super().__init__(name, CardType.TOOL)
        self.effect = effect
