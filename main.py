import uvicorn
from starlette.responses import JSONResponse
from helper import *
from fastapi import Form
from fastapi import FastAPI, Query
from fastapi.staticfiles import StaticFiles
from fastapi.requests import Request
from fastapi.templating import Jinja2Templates

app = FastAPI(title="SmartBank Banking System")
app.mount("/frontend", StaticFiles(directory="frontend", html=True), name="frontend")
templates = Jinja2Templates(directory = "frontend")

class TransferRequest(BaseModel):
    from_account_id: str
    to_account_id: str
    amount: float
    currency: str = "INR"

@app.get("/")
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

''''@app.get("/accounts")
def get_accounts():
    accounts = list_accounts()
    return JSONResponse(content=accounts)'''


@app.post("/transfer")
def transfer_form(
    request: Request,
    from_account: str = Form(...),
    to_account: str = Form(...),
    amount: float = Form(...)
):
    try:
        # Lookup accounts by ID or Name
        from_acc = get_account(from_account)
        to_acc = get_account(to_account)

        # Validate existence
        if not from_acc:
            return templates.TemplateResponse("index.html", {"request": request, "message": f"Sender '{from_account}' not found", "message_type": "error"})
        if not to_acc:
            return templates.TemplateResponse("index.html", {"request": request, "message": f"Receiver '{to_account}' not found", "message_type": "error"})
        if from_acc["id"] == to_acc["id"]:
            return templates.TemplateResponse("index.html", {"request": request, "message": "Cannot transfer to the same account", "message_type": "error"})

        # Perform transfer using existing make_transfer()
        transfer_req = TransferRequest(
            from_account_id=from_acc["id"],
            to_account_id=to_acc["id"],
            amount=amount
        )
        result = make_transfer(transfer_req)

        return templates.TemplateResponse("index.html", {"request": request, "message": f"Success! Transfer ID: {result['transfer_id']}", "message_type": "success"})

    except Exception as e:
        return templates.TemplateResponse("index.html", {"request": request, "message": f"Error: {str(e)}", "message_type": "error"})


@app.get("/received-transfers")
def received_transfers(account_id: str = Query(...)):
    # Validate account exists
    account = get_account(account_id)
    if not account:
        return JSONResponse(content={"error": "Account not found"}, status_code=404)

    transfers = get_received_transfers(account_id)
    return JSONResponse(content={"account_id": account_id, "received_transfers": transfers})


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
