from os import getenv
import json
import sqlite3

BasePath = getenv("DB_STORE_PATH", "./data/lite.db")
BaseConnect = sqlite3.connect(BasePath,  check_same_thread=False)
BaseConnect.row_factory = sqlite3.Row

def initDbSchema():
    dbCursor = BaseConnect.cursor()
    dbCursor.execute('''
        CREATE TABLE IF NOT EXISTS SheduledMessage (
            id INTEGER NOT NULL PRIMARY KEY, 
            channel TEXT,
            message_ts REAL ,
            getters TEXT,
            done INTEGER DEFAULT 0,
            time INTEGER
        )
    ''')
    dbCursor.close()

initDbSchema()