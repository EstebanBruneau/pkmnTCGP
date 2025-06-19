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
    card_id: str
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

    def __init__(self, name: str, card_id: str, hp: int, pokemon_type: PokemonType, is_ex: bool = False):
        """Initialize a Pokemon card."""
        super().__init__(name, CardType.POKEMON_EX if is_ex else CardType.POKEMON)
        self.card_id = card_id
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
        
    def get_stage(self) -> str:
        """Get the evolutionary stage of the Pokemon."""
        if not self.can_evolve_from:
            return "Basic"
        elif "-ex" in self.card_id.lower():
            return "EX"
        else:
            return "Stage 1" if "-" not in self.can_evolve_from else "Stage 2"
            
    def get_full_info(self) -> str:
        """Get a formatted string with complete Pokemon information."""
        sections = []
        
        # Basic Information Section
        basic_info = [
            "╔══════════════ Basic Information ══════════════╗",
            f"║ ID: {self.card_id:<41}║",
            f"║ Name: {self.name:<39}║",
            f"║ Card Type: {self.card_type.name:<34}║",
            f"║ Stage: {self.get_stage():<37}║",
            f"║ Pokemon Type: {self.pokemon_type.name:<31}║"
        ]
        if self.is_ex:
            basic_info.append("║ ⭐ Pokemon-EX                              ║")
        basic_info.append("╚═════════════════════════════════════════╝")
        sections.append("\n".join(basic_info))
        
        # Health and Status Section
        health_info = [
            "╔═══════════════ Health Stats ═══════════════╗",
            f"║ Current HP: {self.hp}/{self.max_hp:<31}║"
        ]
        if self.status != StatusCondition.NONE:
            health_info.append(f"║ Status: {self.status.name:<36}║")
        health_info.append("╚═════════════════════════════════════════╝")
        sections.append("\n".join(health_info))
            
        # Evolution Information
        if self.can_evolve_from:
            evo_info = [
                "╔═════════════ Evolution Info ══════════════╗",
                f"║ Evolves from: {self.can_evolve_from:<30}║"
            ]
            if self.evolved_this_turn:
                evo_info.append("║ Note: Evolved this turn                    ║")
            evo_info.append(f"║ Turn played: {self.turn_played if self.turn_played >= 0 else 'Not yet played':<31}║")
            evo_info.append("╚═════════════════════════════════════════╝")
            sections.append("\n".join(evo_info))
            
        # Combat Stats
        combat_info = [
            "╔══════════════ Combat Stats ══════════════╗"
        ]
        if self.weakness:
            combat_info.append(f"║ Weakness: {self.weakness.name:<34}║")
        combat_info.append(f"║ Retreat Cost: {self.retreat_cost} energy{' ' * (27 - len(str(self.retreat_cost)))}║")
        combat_info.append("╚═════════════════════════════════════════╝")
        sections.append("\n".join(combat_info))
        
        # Energy Section
        if self.attached_energy:
            energy_info = [
                "╔════════════ Attached Energy ═════════════╗"
            ]
            for energy_type, count in self.attached_energy.items():
                energy_info.append(f"║ {energy_type.name}: {count:<36}║")
            energy_info.append("╚═════════════════════════════════════════╝")
            sections.append("\n".join(energy_info))
            
        # Ability Section
        if self.ability:
            ability_info = [
                "╔═════════════════ Ability ══════════════════╗",
                f"║ Name: {self.ability.name:<37}║"
            ]
            if hasattr(self.ability.effect, '__doc__') and self.ability.effect.__doc__:
                doc = self.ability.effect.__doc__
                # Split long ability descriptions into multiple lines
                while doc:
                    line = doc[:37]
                    doc = doc[37:]
                    ability_info.append(f"║ {line:<41}║")
            ability_info.append("╚═════════════════════════════════════════╝")
            sections.append("\n".join(ability_info))
            
        # Attacks Section
        if self.attacks:
            for i, attack in enumerate(self.attacks, 1):
                attack_info = [
                    "╔═════════════════ Attack ═══════════════════╗",
                    f"║ {attack.name:<41}║",
                    "╠═════════════════════════════════════════╣",
                    f"║ Energy Cost: [{', '.join(attack.cost_types)}]" + " " * (41 - len(f"Energy Cost: [{', '.join(attack.cost_types)}]")) + "║",
                    f"║ Base Damage: {attack.damage}" + " " * (41 - len(f"Base Damage: {attack.damage}")) + "║"
                ]
                if attack.effect:
                    if hasattr(attack.effect, '__doc__') and attack.effect.__doc__:
                        doc = attack.effect.__doc__
                        attack_info.append("║ Effect:" + " " * 34 + "║")
                        # Split long effect descriptions into multiple lines
                        while doc:
                            line = doc[:37]
                            doc = doc[37:]
                            attack_info.append(f"║ {line:<41}║")
                attack_info.append("╚═════════════════════════════════════════╝")
                sections.append("\n".join(attack_info))
            
        # Tool Card Section
        if self.attached_tool:
            tool_info = [
                "╔════════════ Attached Tool ══════════════╗",
                f"║ Name: {self.attached_tool.name:<37}║"
            ]
            if hasattr(self.attached_tool.effect, '__doc__') and self.attached_tool.effect.__doc__:
                doc = self.attached_tool.effect.__doc__
                while doc:
                    line = doc[:37]
                    doc = doc[37:]
                    tool_info.append(f"║ {line:<41}║")
            tool_info.append("╚═════════════════════════════════════════╝")
            sections.append("\n".join(tool_info))
                
        return "\n\n".join(sections)

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
