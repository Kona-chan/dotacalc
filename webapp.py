# -*- coding: utf-8 -*-

from flask import Flask, jsonify, render_template, request
from flask.json import dumps
import dotacalc

app = Flask(__name__)


@app.route('/_get_heroes')
def get_heroes():
    return dumps(dotacalc.get_hero_names())


@app.route('/_get_items')
def get_items():
    return dumps(dotacalc.get_item_names())


@app.route('/_calculate')
def calculate():
    hero_name = request.args.get('hero', '', type=str)
    hero_level = request.args.get('level', 16, type=int)
    hero = dotacalc.load_hero(hero_name)
    if hero:
        hero.level = hero_level
        hero.clear_inventory()
        items = request.args.getlist('items')
        for item in items:
            hero.give(dotacalc.load_item(item))
        return jsonify(
            hp=hero.hp(),
            mana=hero.mana(),
            mana_regen=hero.mana_regen(),
            damage=hero.damage(),
            armor=hero.armor(),
            movement_speed=hero.movement_speed(),
            attack_speed=hero.attack_speed(),
            attacks_per_second=hero.attacks_per_second(),
            spell_resistance=hero.spell_resistance(),
            evasion=hero.evasion()
        )
    else:
        return None


@app.route('/')
def index():
    return render_template('calc.html')


if __name__ == '__main__':
    app.run(debug=True)
