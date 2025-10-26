import pymysql
import os
from dotenv import load_dotenv
from fastapi import HTTPException
import uuid
from datetime import date
from pydantic import BaseModel

class TransferRequest(BaseModel):
    from_account_id: str
    to_account_id: str
    amount: float
    currency: str = "INR"

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


def get_account(identifier: str):
    """
    Try to fetch account by ID first. If not found, try by name.
    Returns None if no account is found.
    """
    connect = get_db_connection()
    cursor = connect.cursor()

    # Try as ID
    cursor.execute("SELECT id, name, balance, daily_limit FROM accounts WHERE id=%s", (identifier,))
    row = cursor.fetchone()

    # If not found, try as name
    if not row:
        cursor.execute("SELECT id, name, balance, daily_limit FROM accounts WHERE name=%s", (identifier,))
        row = cursor.fetchone()

    cursor.close()
    connect.close()

    if row:
        return {"id": row[0], "name": row[1], "balance": float(row[2]), "daily_limit": float(row[3])}
    return None

def make_transfer(transfer: TransferRequest):
    connect = get_db_connection()
    cursor = connect.cursor()

    try:
        if transfer.from_account_id == transfer.to_account_id:
            raise HTTPException(status_code=400, detail="Cannot transfer to same account")

        # Lock sender & receiver rows
        cursor.execute(
            "SELECT id, balance, daily_limit FROM accounts WHERE id IN (%s, %s) FOR UPDATE",
            (transfer.from_account_id, transfer.to_account_id)
        )
        rows = cursor.fetchall()

        if len(rows) < 2:
            raise HTTPException(status_code=404, detail="Account not found")

        account_data = {r[0]: {"balance": float(r[1]), "limit": float(r[2])} for r in rows}
        sender = account_data[transfer.from_account_id]
        receiver = account_data[transfer.to_account_id]

        # --- Validate balance ---
        if sender["balance"] < transfer.amount:
            raise HTTPException(status_code=402, detail="Insufficient funds")

        # --- Get today's usage ---
        today = date.today()
        cursor.execute(
            "SELECT total_transferred FROM account_daily_usage WHERE account_id=%s AND date=%s",
            (transfer.from_account_id, today)
        )
        result = cursor.fetchone()
        used_today = float(result[0]) if result else 0.0

        # --- Check daily limit ---
        if used_today + transfer.amount > sender["limit"]:
            raise HTTPException(status_code=429, detail="Exceeds daily limit")

        # --- Perform transaction ---
        cursor.execute("UPDATE accounts SET balance = balance - %s WHERE id = %s",
                       (transfer.amount, transfer.from_account_id))
        cursor.execute("UPDATE accounts SET balance = balance + %s WHERE id = %s",
                       (transfer.amount, transfer.to_account_id))

        # --- Update daily usage ---
        if result:
            cursor.execute(
                "UPDATE account_daily_usage SET total_transferred = total_transferred + %s WHERE account_id=%s AND date=%s",
                (transfer.amount, transfer.from_account_id, today)
            )
        else:
            cursor.execute(
                "INSERT INTO account_daily_usage (id, account_id, date, total_transferred) VALUES (%s, %s, %s, %s)",
                (str(uuid.uuid4()), transfer.from_account_id, today, transfer.amount)
            )

        # --- Log transfer ---
        transfer_id = str(uuid.uuid4())
        cursor.execute(
            "INSERT INTO transfers (id, from_account_id, to_account_id, amount, currency, status) VALUES (%s, %s, %s, %s, %s, 'COMPLETED')",
            (transfer_id, transfer.from_account_id, transfer.to_account_id, transfer.amount, transfer.currency)
        )

        # --- Insert audit log ---
        log_id = str(uuid.uuid4())
        action = "MONEY_TRANSFER"
        details = f"Transfer {transfer.amount} {transfer.currency} from {transfer.from_account_id} to {transfer.to_account_id}"
        cursor.execute(
            "INSERT INTO audit_logs (id, action, details) VALUES (%s, %s, %s)",
            (log_id, action, details)
        )

        connect.commit()

        return {
            "status": "COMPLETED",
            "transfer_id": transfer_id,
            "message": f"Transferred {transfer.amount} {transfer.currency} successfully."
        }

    except HTTPException as e:
        connect.rollback()
        raise e
    except Exception as e:
        connect.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        connect.close()

def get_received_transfers(account_id: str):
    connect = get_db_connection()
    cursor = connect.cursor()
    try:
        cursor.execute(
            "SELECT id, from_account_id, amount, currency, status, created_at "
            "FROM transfers WHERE to_account_id=%s ORDER BY created_at DESC",
            (account_id,)
        )
        transfers = [
            {
                "id": r[0],
                "from_account_id": r[1],
                "amount": float(r[2]),
                "currency": r[3],
                "status": r[4],
                "created_at": str(r[5])
            }
            for r in cursor.fetchall()
        ]
        return transfers
    finally:
        cursor.close()
        connect.close()
