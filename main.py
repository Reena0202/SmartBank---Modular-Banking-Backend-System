from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
import uuid
from helper import *
from datetime import date
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.requests import Request
from fastapi.templating import Jinja2Templates

app = FastAPI(title="SmartBank Banking System")
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
templates = Jinja2Templates(directory = "frontend")

class TransferRequest(BaseModel):
    from_account_id: str
    to_account_id: str
    amount: float
    currency: str = "INR"

@app.get("/")
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/accounts")
def get_accounts():
    accounts = list_accounts()
    return JSONResponse(content=accounts)

@app.post("/transfers")
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

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
