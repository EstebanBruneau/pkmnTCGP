"""
Enums for the Pokemon TCG Pocket game.
"""
from enum import Enum, auto

class CardType(Enum):
    """Types of cards in the game."""
    POKEMON = auto()
    POKEMON_EX = auto()
    SUPPORTER = auto()
    ITEM = auto()
    TOOL = auto()

class StatusCondition(Enum):
    """Status conditions that can affect Pokemon."""
    NONE = auto()
    POISON = auto()
    BURN = auto()
    SLEEP = auto()
    PARALYSIS = auto()
    CONFUSION = auto()

class PokemonType(Enum):
    """Pokemon types."""
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
