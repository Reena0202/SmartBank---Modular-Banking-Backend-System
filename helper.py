import pymysql
import os
from dotenv import load_dotenv

load_dotenv()

def get_db_connection():
    return pymysql.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "MY_PROJECTS"),
        autocommit=False
    )

def list_accounts():
    connect = get_db_connection()
    cursor = connect.cursor()
    cursor.execute("SELECT id, name, balance, daily_limit FROM accounts")
    accounts = [
        {"id": r[0], "name": r[1], "balance": float(r[2]), "daily_limit": float(r[3])}
        for r in cursor.fetchall()
    ]
    cursor.close()
    connect.close()
    return accounts