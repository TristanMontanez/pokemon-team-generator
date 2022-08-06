from typing import List
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

def get_pokemon_team(pokemon_ids: List[int]):
    pokemon_dict_list = []
    for id in pokemon_ids:
        id = int(id)
            
        cur = get_db().execute(
            f'SELECT id, name, picture FROM pokemon WHERE id={id};'
        )
        pokemon = dict(zip(POKEMON_COLUMNS, cur.fetchall()[0]))
        pokemon['type'] = get_pokemon_types(id)
        pokemon_dict_list.append(pokemon)
    return pokemon_dict_list

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

def get_random_team():
    cur = get_db().execute(
        'SELECT id, name, picture FROM pokemon ORDER BY RANDOM() LIMIT 6;'
    )
    pokemon_list = cur.fetchall()
    cur.close()

    pokemon_dict_list = []
    for pokemon in pokemon_list:
        pokemon_dict = dict(zip(POKEMON_COLUMNS, pokemon))
        pokemon_dict['type'] = get_pokemon_types(pokemon_dict['id'])
        pokemon_dict_list.append(pokemon_dict)
    return pokemon_dict_list

def get_saved_team():
    # data = request.json

    cur = get_db().execute(
        f'SELECT pokemon_id FROM saved_pokemon'
    )
    pokemon_team = cur.fetchall()
    pokemon_ids = []
    for id in pokemon_team:
        pokemon_ids.append(id[0])

    return pokemon_ids

@app.route('/')
def hello_world():
    context = {'saved_team': get_pokemon_team(get_saved_team())}
    return render_template('index.html', **context)

@app.route('/generate')
def generate():
    return get_random_team()

@app.route('/reroll', methods=['POST'])
def reroll_pokemon():
    data = request.json
    get_pokemon_team(data.get('ids'))
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

@app.route('/save', methods=['POST'])
def save_pokemon():
    pokemon_ids = request.json.get('ids')
    cur = get_db().execute(
        f'DELETE FROM saved_pokemon'
    )
    for id in pokemon_ids:
        id = int(id)
        cur = get_db().execute(
            f'INSERT INTO saved_pokemon (pokemon_id) VALUES ({id})'
        )
        cur.connection.commit()
    cur.close()
    return {}

@app.route('/delete', methods=['DELETE'])
def delete_team():
    cur = get_db().execute(
        f'DELETE FROM saved_pokemon'
    )
    cur.connection.commit()
    cur.close()
    return {}
