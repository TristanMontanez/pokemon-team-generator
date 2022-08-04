import sqlite3
from flask import Flask, render_template, g


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

def get_pokemon_team():
    cur = get_db().execute(
        'SELECT * FROM pokemon ORDER BY RANDOM() LIMIT 6'
    )
    pokemon_list = cur.fetchall()
    cur.close()

    pokemon_dict_list = []
    for pokemon in pokemon_list:
        pokemon_dict_list.append(dict(zip(POKEMON_COLUMNS, pokemon)))

    print(pokemon_dict_list)
    return pokemon_dict_list

@app.route('/')
def hello_world():
    team = get_pokemon_team()
    context = {'team': team}
    return render_template('index.html', **context)