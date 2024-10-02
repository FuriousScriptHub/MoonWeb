from flask import Flask, render_template, request, jsonify, redirect, url_for
import json
import os
import sqlite3
import random
import string
from datetime import datetime, timedelta

app = Flask(__name__)

def get_db_connection():
    conn = sqlite3.connect('license_keys.db')
    conn.row_factory = sqlite3.Row
    return conn

def generate_key():
    """Generate a random license key."""
    return '-'.join([''.join(random.choices(string.ascii_uppercase + string.digits, k=4)) for _ in range(4)])

def save_keys_to_json():
    """Save all keys from the database to the JSON file."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM keys')
    rows = cursor.fetchall()

    data = {}
    for row in rows:
        data[row[0]] = {
            'user_id': row[1],
            'expiration': row[2]
        }

    with open('valid_keys.json', 'w') as f:
        json.dump(data, f)

def add_license_key(user_id, duration):
    """Add a new license key with an expiration date."""
    key = generate_key()
    expiration_date = datetime.now()

    if duration == '1d':
        expiration_date += timedelta(days=1)
    elif duration == '1w':
        expiration_date += timedelta(weeks=1)
    elif duration == '1m':
        expiration_date += timedelta(weeks=4)
    elif duration == 'lifetime':
        expiration_date = None

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO keys (key, user_id, expiration)
    VALUES (?, ?, ?)
    ''', (key, user_id, expiration_date.isoformat() if expiration_date else None))
    conn.commit()

    save_keys_to_json()
    return key

@app.route('/')
def index():
    """Display all license keys and the key generation form."""
    conn = get_db_connection()
    keys = conn.execute('SELECT * FROM keys').fetchall()
    conn.close()
    return render_template('index.html', keys=keys)

@app.route('/generate_key', methods=['POST'])
def generate_key_route():
    """Generate a new license key."""
    user_id = request.form.get('user_id')
    duration = request.form.get('duration')

    if user_id is None or duration is None:
        return jsonify({'status': 'error', 'message': 'user_id and duration are required'}), 400

    new_key = add_license_key(user_id, duration)
    return redirect(url_for('index'))  # Redirect back to the index page

@app.route('/delete/<key>', methods=['POST'])
def delete_key(key):
    """Delete a license key from the database and JSON file."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM keys WHERE key = ?', (key,))
    conn.commit()
    conn.close()

    # After deletion, update the JSON file
    save_keys_to_json()

    return redirect(url_for('index'))  # Redirect back to the index page

if __name__ == '__main__':
    app.run(debug=True)