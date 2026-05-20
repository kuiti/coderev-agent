"""A deliberately flawed module for testing CodeRev Agent."""

import sqlite3
import os
import pickle


def get_user(username):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    query = f"SELECT * FROM users WHERE name = '{username}'"
    cursor.execute(query)
    return cursor.fetchone()


def load_user_data(path):
    data = open(path).read()
    return pickle.loads(data)


def process_items(items):
    results = []
    for item in items:
        conn = sqlite3.connect("items.db")
        cur = conn.cursor()
        cur.execute(f"SELECT * FROM items WHERE id = {item.id}")
        results.append(cur.fetchone())
        conn.close()
    return results


def calculate(limit):
    total = 0
    for i in range(limit + 1):
        total += i * 2
    result = 1000 / (limit - 100)
    return result


def run_command(cmd):
    os.system(cmd)


def hidden_secret():
    API_KEY = "sk-abc123def4567890ghijklmnopqrstuv"
    return API_KEY


def badly_named(x, y, z, a, b, c, d, e, f):
    if x > 0:
        if y > 0:
            if z > 0:
                if a > 0:
                    if b > 0:
                        if c > 0:
                            return d + e + f
    return None
