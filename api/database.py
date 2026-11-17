from pathlib import Path

import pyodbc
import yaml


CONFIG_PATH = Path(__file__).resolve().parent / "config.yaml"


def load_config() -> dict:
    with open(CONFIG_PATH, "r") as file:
        return yaml.safe_load(file)


def get_connection():
    config = load_config()
    db = config["database"]

    connection_string = (
        f"DRIVER={{{db['driver']}}};"
        f"SERVER={db['host']};"
        f"PORT={db['port']};"
        f"DATABASE={db['database']};"
        f"UID={db['user']};"
        f"PWD={db['password']};"
    )

    return pyodbc.connect(
        connection_string,
        autocommit=True,
    )


def get_db():
    connection = get_connection()

    try:
        yield connection
    finally:
        connection.close()