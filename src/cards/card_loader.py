import json
from typing import List
from ..models.cards import PokemonCard, Attack, SupporterCard, ItemCard, ToolCard, Card
from ..models.enums import PokemonType

# Map string to PokemonType
POKEMON_TYPE_MAP = {
    'Grass': PokemonType.GRASS,
    'Fire': PokemonType.FIRE,
    'Water': PokemonType.WATER,
    'Electric': PokemonType.ELECTRIC,
    'Fighting': PokemonType.FIGHTING,
    'Psychic': PokemonType.PSYCHIC,
    'Darkness': PokemonType.DARKNESS,
    'Metal': PokemonType.METAL,
    'Dragon': PokemonType.DRAGON,
    'Colorless': PokemonType.NORMAL,
}

def parse_attack(attack_json) -> Attack:
    name = attack_json.get('name', 'Unknown')
    damage = attack_json.get('damage', '0')
    try:
        damage_val = int(''.join(filter(str.isdigit, damage)))
    except Exception:
        damage_val = 0
    cost = attack_json.get('cost', [])
    energy_cost = len(cost)
    cost_types = cost  # e.g. ["Grass", "Colorless"]
    effect_text = attack_json.get('effect', '').strip()
    effect_fn = None
    # Venusaur - Mega Drain: Heal 30 damage from this Pokémon.
    if name == "Mega Drain" and effect_text.startswith("Heal 30 damage"):
        def mega_drain_effect(self_player, opp_player):
            poke = self_player.active
            if poke:
                healed = min(30, poke.max_hp - poke.hp)
                poke.hp += healed
                print(f"{poke.name} healed {healed} HP with Mega Drain!")
        effect_fn = mega_drain_effect
    # Venusaur ex - Giant Bloom: Heal 30 damage from this Pokémon.
    elif name == "Giant Bloom" and effect_text.startswith("Heal 30 damage"):
        def giant_bloom_effect(self_player, opp_player):
            poke = self_player.active
            if poke:
                healed = min(30, poke.max_hp - poke.hp)
                poke.hp += healed
                print(f"{poke.name} healed {healed} HP with Giant Bloom!")
        effect_fn = giant_bloom_effect
    # Caterpie - Find a: Put 1 random [G] Pokémon from your deck into your hand.
    elif name == "Find a" and "random [G] Pokémon" in effect_text:
        import random
        def find_a_effect(self_player, opp_player):
            grass_pokemon = [card for card in self_player.deck if hasattr(card, 'pokemon_type') and getattr(card, 'pokemon_type', None) and getattr(card, 'pokemon_type').name == 'GRASS']
            if grass_pokemon:
                chosen = random.choice(grass_pokemon)
                self_player.deck.remove(chosen)
                self_player.hand.append(chosen)
                print(f"Caterpie's Find a: Put {chosen.name} into your hand from your deck.")
            else:
                print("Caterpie's Find a: No [G] Pokémon found in deck.")
        effect_fn = find_a_effect
    # Vileplume - Soothing Scent: Your opponent's Active Pokémon is now Asleep.
    elif name == "Soothing Scent" and "Asleep" in effect_text:
        from ..models.enums import StatusCondition
        def soothing_scent_effect(self_player, opp_player):
            if opp_player.active:
                opp_player.active.status = StatusCondition.SLEEP
                print(f"Vileplume's Soothing Scent: {opp_player.active.name} is now Asleep!")
        effect_fn = soothing_scent_effect
    # Venomoth - Poison Powder: Your opponent's Active Pokémon is now Poisoned.
    elif name == "Poison Powder" and "Poisoned" in effect_text:
        from ..models.enums import StatusCondition
        def poison_powder_effect(self_player, opp_player):
            if opp_player.active:
                opp_player.active.status = StatusCondition.POISON
                print(f"Venomoth's Poison Powder: {opp_player.active.name} is now Poisoned!")
        effect_fn = poison_powder_effect
    # Exeggutor - Stomp: Flip a coin. If heads, this attack does 30 more damage.
    elif name == "Stomp" and "30 more damage" in effect_text:
        import random
        def stomp_effect(self_player, opp_player):
            if random.choice([True, False]):
                print("Exeggutor's Stomp: Coin flip heads! +30 damage!")
                if self_player.active:
                    self_player.active._bonus_damage = 30
            else:
                print("Exeggutor's Stomp: Coin flip tails. No bonus damage.")
                if self_player.active:
                    self_player.active._bonus_damage = 0
        effect_fn = stomp_effect
    # Exeggutor ex - Tropical Swing: Flip a coin. If heads, this attack does 40 more damage.
    elif name == "Tropical Swing" and "40 more damage" in effect_text:
        import random
        def tropical_swing_effect(self_player, opp_player):
            if random.choice([True, False]):
                print("Exeggutor ex's Tropical Swing: Coin flip heads! +40 damage!")
                if self_player.active:
                    self_player.active._bonus_damage = 40
            else:
                print("Exeggutor ex's Tropical Swing: Coin flip tails. No bonus damage.")
                if self_player.active:
                    self_player.active._bonus_damage = 0
        effect_fn = tropical_swing_effect
    # Tangela - Absorb: Heal 10 damage from this Pokémon.
    elif name == "Absorb" and effect_text.startswith("Heal 10 damage"):
        def absorb_effect(self_player, opp_player):
            poke = self_player.active
            if poke:
                healed = min(10, poke.max_hp - poke.hp)
                poke.hp += healed
                print(f"{poke.name} healed {healed} HP with Absorb!")
        effect_fn = absorb_effect
    # Pinsir - Double Horn: Flip 2 coins. This attack does 50 damage for each heads.
    elif name == "Double Horn" and "50 damage for each heads" in effect_text:
        import random
        def double_horn_effect(self_player, opp_player):
            heads = sum(random.choice([True, False]) for _ in range(2))
            bonus = 50 * heads
            print(f"Pinsir's Double Horn: {heads} heads, +{bonus} damage!")
            if self_player.active:
                self_player.active._bonus_damage = bonus
        effect_fn = double_horn_effect
    # Petilil - Blot: Heal 10 damage from this Pokémon.
    elif name == "Blot" and effect_text.startswith("Heal 10 damage"):
        def blot_effect(self_player, opp_player):
            poke = self_player.active
            if poke:
                healed = min(10, poke.max_hp - poke.hp)
                poke.hp += healed
                print(f"{poke.name} healed {healed} HP with Blot!")
        effect_fn = blot_effect
    # Lilligant - Leaf Supply: Take a [G] Energy from your Energy Zone and attach it to 1 of your Benched [G] Pokémon.
    elif name == "Leaf Supply" and "attach it to 1 of your Benched [G] Pokémon" in effect_text:
        def leaf_supply_effect(self_player, opp_player):
            # Only works if player has at least 1 energy in their pool and a benched Grass Pokémon
            if self_player.energy > 0:
                grass_bench = [poke for poke in self_player.bench if getattr(poke, 'pokemon_type', None) and poke.pokemon_type.name == 'GRASS']
                if grass_bench:
                    # Attach to the first benched Grass Pokémon
                    poke = grass_bench[0]
                    if not hasattr(poke, 'attached_energy'):
                        poke.attached_energy = {}
                    poke.attached_energy[PokemonType.GRASS] = poke.attached_energy.get(PokemonType.GRASS, 0) + 1
                    self_player.energy -= 1
                    print(f"Lilligant's Leaf Supply: Attached 1 [G] energy to {poke.name} on the bench.")
                else:
                    print("Lilligant's Leaf Supply: No benched [G] Pokémon to attach energy to.")
            else:
                print("Lilligant's Leaf Supply: No [G] energy in your Energy Zone.")
        effect_fn = leaf_supply_effect
    return Attack(name=name, damage=damage_val, energy_cost=energy_cost, cost_types=cost_types, effect=effect_fn)

def safe_int(val, default=0):
    try:
        return int(val)
    except Exception:
        return default

def load_cards_from_json(json_path: str) -> List[Card]:
    with open(json_path, encoding='utf-8') as f:
        data = json.load(f)
    cards: List[Card] = []
    for entry in data:
        card_type = entry.get('card_type', '')
        name = entry.get('name', 'Unknown')
        card_id = entry.get('id', 'UNKNOWN_ID')  # Using 'id' instead of 'card_id'
        hp = safe_int(entry.get('hp', '0'), 0)
        ex = entry.get('ex', 'No') == 'Yes'
        # Only handle Pokemon for now
        if 'Pokémon' in card_type:
            type_str = entry.get('type', 'Colorless')
            pokemon_type = POKEMON_TYPE_MAP.get(type_str, PokemonType.NORMAL)
            card = PokemonCard(name=name, card_id=card_id, hp=hp, pokemon_type=pokemon_type, is_ex=ex)
            
            # Set evolution data
            evolves_from = entry.get('evolves_from', None)
            if evolves_from:
                card.can_evolve_from = evolves_from
            
            # Set weakness
            weakness_str = entry.get('weakness', None)
            if weakness_str:
                card.weakness = POKEMON_TYPE_MAP.get(weakness_str, None)
                
            # Set retreat cost
            card.retreat_cost = safe_int(entry.get('retreat_cost', '1'), 1)
            
            # Set ability information
            ability_data = entry.get('ability', None)
            if ability_data:
                from .abilities import create_ability
                ability = create_ability(ability_data.get('name', ''), ability_data.get('effect', ''))
                if ability:
                    card.ability = ability
            
            # Parse attacks
            attacks_json = entry.get('attacks', [])
            for attack in attacks_json:
                attack_obj = parse_attack(attack)
                if attack_obj:
                    card.attacks.append(attack_obj)
                    
            cards.append(card)
        # TODO: Add Supporter, Item, Tool parsing
    return cards
