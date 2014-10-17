# -*- coding: utf-8 -*-

"""
Dota Calculator 0.1

This script provides tools for calculation of different Dota 2 hero stats
given different items.
"""

import math
import operator
import json
import yaml


class Item(yaml.YAMLObject):

    yaml_tag = u'!Item'


class Hero(object):
    """This class represents a single Dota 2 hero."""

    def __init__(self, stats):
        self.name = stats['name']
        self.primary_attr = stats['primary_attribute']
        self.base_str = stats['base_str']
        self.str_gain = stats['str_gain']
        self.base_agi = stats['base_agi']
        self.agi_gain = stats['agi_gain']
        self.base_int = stats['base_int']
        self.int_gain = stats['int_gain']
        self.damage_min = stats['damage_min']
        self.damage_max = stats['damage_max']
        self.base_damage = int((self.damage_min + self.damage_max) / 2)
        self.base_armor = stats['armor']
        self.base_speed = stats['speed']
        self.bat = stats['bat']
        self.spell_resistance = stats['spell_resistance'] \
            if 'spell_resistance' in stats else 25
        self.hp_regen = stats['hp_regen'] \
            if 'hp_regen' in stats else 0.25
        self._items = []
        self._level = 1
        self._attr_levels = 0

    def __repr__(self):
        return '%s(name=%r, primary_attribute=%r, base_str=%r, ' \
               'str_gain=%r, base_agi=%r, agi_gain=%r, base_int=%r, ' \
               'int_gain=%r, damage_min=%r, damage_max=%r, armor=%r, ' \
               'speed=%r, bat=%r, spell_resistance=%r, hp_regen=%r)' % \
            (self.__class__.__name__, self.name, self.primary_attr,
             self.base_str, self.str_gain, self.base_agi,
             self.agi_gain, self.base_int, self.int_gain,
             self.damage_min, self.damage_max, self.base_armor,
             self.base_speed, self.bat, self.spell_resistance, self.hp_regen)

    @property
    def level(self):
        """Get hero level."""
        return self._level

    @level.setter
    def level(self, level):
        self._level = level
        self._attr_levels = self._min_possible_attr_levels()

    @property
    def attr_levels(self):
        """Get how much skill points are put into attributes."""
        return self._attr_levels

    @attr_levels.setter
    def attr_levels(self, attr_levels):
        if attr_levels > self._max_possible_attr_levels():
            attr_levels = self._max_possible_attr_levels()
        if attr_levels < self._min_possible_attr_levels():
            attr_levels = self._min_possible_attr_levels()
        self._attr_levels = attr_levels

    def _max_possible_attr_levels(self):
        return min(round(self._level / 2), 10)

    def _min_possible_attr_levels(self):
        return self._level == 15 and 1 or max(self._level - 15, 0)

    def _from_items(self, stat):
        """Calculate stat bonus additively.

        This is used for majority of stats that stack by simple
        addition of the components.
        """
        return sum(getattr(item, stat) for item in self._items
                   if hasattr(item, stat))

    def _from_items_mul(self, stat):
        """Calculate stat bonus multiplicatively.

        This is used for evasion and magic resistance that stack
        multiplicatively rather than by simple addition.
        """
        if self._items:
            return reduce(operator.mul, [1 - getattr(item, stat)
                                         for item in self._items
                                         if hasattr(item, stat)], 1)
        else:
            return 1

    def _from_items_max(self, stat):
        """Get maximum stat bonus.

        This is used for movement speed. If a hero is carrying
        multiple different sources of movement speed (e.g. boots)
        only the highest bonus is applied.
        """
        # FIXME: potential bug when _items is empty
        stats = [getattr(item, stat) for item in self._items
                 if hasattr(item, stat)]
        if stats:
            return max(stats)
        else:
            return 0

    def gained_str(self):
        """Return strength gained with hero's strength gain."""
        return (self._level - 1) * self.str_gain + \
            self._attr_levels * 2 + \
            self._from_items('strength')

    def total_str(self):
        """Return total hero's strength."""
        return self.base_str + self.gained_str()

    def gained_agi(self):
        """Return agility gained with hero's agility gain."""
        return (self._level - 1) * self.agi_gain + \
            self._attr_levels * 2 + \
            self._from_items('agility')

    def total_agi(self):
        """Return total hero's agility."""
        return self.base_agi + self.gained_agi()

    def gained_int(self):
        """Return intelligence gained with hero's intelligence gain."""
        return (self._level - 1) * self.int_gain + \
            self._attr_levels * 2 + \
            self._from_items('intelligence')

    def total_int(self):
        """Return total hero's intelligence."""
        return self.base_int + self.gained_int()

    def damage(self):
        """Return hero's right click damage."""
        damage_source = {'STR': self.gained_str,
                         'AGI': self.gained_agi,
                         'INT': self.gained_int}
        gained_attr = damage_source[self.primary_attr]
        return math.floor(self.base_damage + gained_attr() +
                          self._from_items('damage'))

    def hp(self):
        """Return hero's total HP from strength and HP bonuses from items."""
        hp = 150 + math.floor(self.total_str()) * 19 + \
            self._from_items('health')
        return hp

    def mana(self):
        """Return hero's total mana from int and mana bonuses from items."""
        mana = math.floor(self.total_int()) * 13 + \
            self._from_items('mana')
        return mana

    def mana_regen(self):
        """Return hero's mana regen from int and item bonuses."""
        mana_regen = self.total_int() * 0.04 + \
            self._from_items('mana_regen_raw')
        mana_regen_multiplier = 1 + self._from_items('mana_regen')
        # TODO: handle basi-based aura mana regen
        return mana_regen * mana_regen_multiplier

    def armor(self):
        """Return hero's armor from agility and item bonuses."""
        armor = self.base_armor + self.total_agi() * 0.14 + \
            self._from_items('armor')
        return armor

    def ehp(self):
        """Return hero's effective HP.

        Effective HP basically shows how much physical damage can a hero
        tank given a certain amount of armor.
        """
        return self.hp() * (self.armor() * 0.06 + 1)

    def movement_speed(self):
        """Return hero's movement speed.

        Note: this doesn't take into account that multiple percentage
        based sources of bonus movement speed (e.g. multiple yashas,
        multiple drums, etc.) don't stack.
        """
        movement_speed = self.base_speed + \
            self._from_items_max('movement_speed')
        ms_multiplier = 1 + self._from_items('movement_speed_multiplier')
        # TODO: add handling of Drums ms bonus
        return min(movement_speed * ms_multiplier, 522)

    def ias(self):
        """Return hero's increased attack speed.

        By itself this number isn't gonna tell much, but it is used
        in calculations for number of attacks per second and actual
        attack speed.
        """
        return min(math.floor(self.total_agi()) +
                   self._from_items('attack_speed'), 400)

    def attack_speed(self):
        """Return hero's real attack speed.

        Essentially this is what attack speed means: it tells
        how much time does it take to perform one autoattack.
        """
        return self.bat / (1 + self.ias() / 100)

    def attacks_per_second(self):
        """Return hero's number of attacks per second."""
        return (1 + self.ias() / 100) / self.bat

    def spell_resistance(self):
        """Return hero's spell resistance.

        As of now, this doesn't take into account inherent hero
        abilities like Spell Shield and Null Field. Only base
        spell resistance (which as of 6.82 is 25%% for all heroes except
        Visage and Meepo) and spell resistance from items are taken
        into account.
        """
        return 1 - (1 - self.spell_resistance) * \
            self._from_items_mul('spell_resistance')

    def evasion(self):
        """Return hero's evasion.

        As of now, this doesn't take into account inherent hero
        abilities like Blur. Only evasion from items is taken
        into account.
        """
        return 1 - self._from_items_mul('evasion')

    def crit_chance(self):
        """Return hero's chance to crit.

        Not implemented yet.
        """
        pass

    def give(self, item):
        """Give an item to the hero."""
        if len(self._items) < 6:
            self._items.append(item)
        else:
            raise Exception("Inventory is full")

    def inventory(self):
        """Return hero's items."""
        return [item.name for item in self._items]

    def clear_inventory(self):
        """Clear hero's items."""
        del self._items[:]


with open('heroes.json', 'r') as f:
    heroes = [Hero(hero) for hero in json.load(f)]
items = [item for item in yaml.load_all(file('items.yml', 'r'))]


def load_hero(name):
    for hero in heroes:
        if hero.name == name:
            return hero
    return None


def load_item(name):
    for item in items:
        if item.name == name:
            return item
    return None


def get_hero_names():
    return [hero.name for hero in heroes]


def get_item_names():
    return [item.name for item in items]


def main():
    pass


if __name__ == '__main__':
    main()
