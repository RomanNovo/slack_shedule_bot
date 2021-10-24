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
            team_id TEXT,
            message_ts REAL,
            getters TEXT,
            done INTEGER DEFAULT 0,
            time INTEGER
        )
    ''')
    dbCursor.close()

def checkDbSchema():
    queryResult = BaseConnect.execute('''
        SELECT name FROM sqlite_master WHERE type='table' AND name='SheduledMessage';
    ''')
    tables = queryResult.fetchall()
    if not tables :
        initDbSchema()  
    else:
        print("db initialized")

def storeTask(task: dict):
    task["getters"] = json.dumps(task["getters"])
    queryResult = BaseConnect.execute(f'''
        INSERT INTO SheduledMessage (channel,team_id,message_ts,getters,time)
            VALUES("{task["channel"]}","{task["team_id"]}","{task["message_ts"]}",'{task["getters"]}',"{task["time"]}");
    ''')
    BaseConnect.commit()
    print("db save " )
    return queryResult

def getTaskOlderTs(ts):
    queryResult = BaseConnect.execute(f'''
        select * from SheduledMessage where time < {ts} and done != 1;
    ''')
    BaseConnect.commit()
    tasks = queryResult.fetchall()
    newTasks = []
    for task in tasks:
        task = dict(task)
        task['getters'] = json.loads(task['getters'])
        newTasks.append(task)    
    return newTasks

def markTaskAsDone(taskId):
    queryResult = BaseConnect.execute(f'''
        UPDATE SheduledMessage SET done = 1 where id = {taskId};
    ''')
    BaseConnect.commit()

    return queryResult   