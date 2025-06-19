"""Module for handling Pokemon abilities."""
from typing import Optional
from ..models.cards import Ability

def create_ability(name: str, effect_text: str) -> Optional[Ability]:
    """Create an Ability object based on name and effect text."""
    if not name or not effect_text:
        return None
        
    # Default effect that just prints the ability description
    def default_effect(player):
        print(f"Activated {name}: {effect_text}")
    
    return Ability(name=name, effect=default_effect)
