import os
from dotenv import load_dotenv

production_path = r'.env.prod'
load_dotenv(production_path, override=True)

def get_db_connection_string():
    ENV = os.getenv("ENV")
    SERVER_URL = os.getenv("SERVER_URL")
    DB_USERNAME = os.getenv("DB_USERNAME")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    DB_SERVER = os.getenv("DB_SERVER")
    DB_PORT = os.getenv("DB_PORT")
    DB_DATABASE = os.getenv("DB_DATABASE")
    DB_CONNECTION_STRING = None

    if ENV == "development":
        DB_CONNECTION_STRING = (
            f'postgresql://{DB_USERNAME}:{DB_PASSWORD}@'
            f'{DB_SERVER}:{DB_PORT}/{DB_DATABASE}'
        )
    else:
        DB_CONNECTION_STRING = (
            f'postgresql://{DB_USERNAME}:{DB_PASSWORD}@'
            f'{DB_SERVER}:{DB_PORT}/{DB_DATABASE}'
        )
    return DB_CONNECTION_STRING 