import os
import json


def read_from_db():
    try:
        with open(os.getenv('SCALR_DB'), 'r') as db:
            data = json.load(db)
        return data
    except FileNotFoundError:
        return {}


def write_into_db(data):
    with open(os.getenv('SCALR_DB'), 'w') as db:
        json.dump(data, db)
