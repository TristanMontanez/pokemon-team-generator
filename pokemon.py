from dataclasses import replace
import json
import sqlite3

from flask import Flask, render_template, g, request


app = Flask(__name__)
DATABASE = 'pokemon.sqlite3'
POKEMON_COLUMNS = ['id', 'name', 'picture']

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def add_pokemon(id, name, types, picture):
    if ";" in name:
        raise ValueError
    

    cur = get_db().execute(
        f'INSERT INTO pokemon (id, name, picture) VALUES ({id}, "{name}", "{picture}");'
    )

    for type_id in types:
        cur = get_db().execute(
            f'INSERT INTO pokemon_type (pokemon_id, type_id) VALUES ({id}, {type_id});'
        )

    cur.connection.commit() 
    cur.close()


def get_pokemon_types(pokemon_id: int):
    cur = get_db().execute(
        f'SELECT name FROM type WHERE id IN (SELECT type_id FROM pokemon_type WHERE pokemon_id={pokemon_id});'
    )
    pokemon_types = cur.fetchall()
    cur.close()

    type_list = []
    for pokemon_type in pokemon_types:
        type_list.append(pokemon_type[0])

    return type_list

def get_pokemon_team():
    cur = get_db().execute(
        'SELECT id, name, picture FROM pokemon ORDER BY RANDOM() LIMIT 6;'
    )
    pokemon_list = cur.fetchall()
    cur.close()

    pokemon_dict_list = []
    for pokemon in pokemon_list:
        pokemon_dict_list.append(dict(zip(POKEMON_COLUMNS, pokemon)))
    return pokemon_dict_list

@app.route('/')
def hello_world():
    team = get_pokemon_team()
    context = {'team': team}
    return render_template('index.html', **context)

@app.route('/generate')
def generate():
    team = get_pokemon_team()

    for pokemon in team:
        pokemon['type'] = get_pokemon_types(pokemon['id'])

    return team

@app.route('/reroll', methods=['POST'])
def reroll_pokemon():
    data = request.json
    replaced_id = data.get('ids').pop(int(data.get('replace')))
    replacement_id = replaced_id
    while(replaced_id == replacement_id):
        cur = get_db().execute(
            f'SELECT id, name, picture FROM pokemon ORDER BY RANDOM() LIMIT 1;'
        )
        replacement_pokemon = cur.fetchall()[0]
        replacement_id = replacement_pokemon[0]
        
    cur.close()
    response = dict(zip(POKEMON_COLUMNS, replacement_pokemon))
    response['type'] = get_pokemon_types(replacement_id)

    return response
