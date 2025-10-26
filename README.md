# SmartBank---Modular-Banking-Backend-System

OBJECTIVE -  to build a secure scalable backend system that supports core banking operations such as account management, transactions, loan processing and fraud detection. 

# Use Case : 3. Money Transfer

# Trigger : customer initiates a transfer
**Flow:**
**1.** Validate sender balance

**2.** Validate daily limits

**3.** Update both accounts

**4.** Log transaction

**Edge cases:**

**1.** Insufficient funds

**2.** Exceeding daily limit.

# System Architecture

**Layers:**
1. **FastAPI Backend** — Exposes secure REST APIs.  
2. **MySQL Database** — Stores customers, accounts, transfers, and logs.  
3. **Frontend (HTML)** — Simple form for initiating transfers.  

# Architecture diagram

|                         Customer (Frontend)                   |
|---------------------------------------------------------------|
| - Initiates transfer via HTML form           |
| - Sends POST /transfers request (JSON)                        |
                              
+---------------------------------------------------------------+
|                      FastAPI Backend Server                   |
|---------------------------------------------------------------|
| [1] Receive Request                                            |
|      → Validate input                                          |
|                                                                |
| [2] Business Validation Layer                                  |
|      → Check Customer exists                                                    
|      → Check sender & receiver accounts exist and ACTIVE       |
|      → Validate balance and daily limits                       |
|                                                                |
| [3] Database Transaction Layer (Atomic)                        |
|      ┌────────────────────────────────────────────────────────┐
|       BEGIN TRANSACTION                                       |
|       SELECT ... FOR UPDATE on both accounts                  |
|       Deduct from sender balance                              |
|       Add to receiver balance                                 |
|       Insert record into `transfers` table                    |
|       Update `account_daily_usage` table                      |
|       COMMIT                                                  |
|      └────────────────────────────────────────────────────────┘
|                                                                |
| [4] Logging & Audit                                            |
|      → Insert record into 'audit logs' table                   |
|                                                                |
| [5] Response Handling                                          |
|      → Return success/failure JSON to client                   |
| [6] Validate from receiver's end                               |
|      → Validation from receivers end for received amount       |


                          

|                         MySQL Database                        |
|---------------------------------------------------------------|
| Tables:                                                       |
|  - accounts                                                   |
|  - transfers                                                  |
|  - account_daily_usage                                        |
|  - audit_logs                                                 |


# API Endpoints:

| Endpoint                   | Method | Description                          |
| -------------------------- | ------ | ------------------------------------ |
| `/customers/{id}/accounts` | GET    | List customer’s accounts             |
| `/transfers`               | POST   | Initiate a money transfer            |
| `/transfers/{id}`          | GET    | Retrieve transfer status             |
| `/accounts/{id}/limits`    | GET    | Check remaining daily limit          |


# Handling Edge Cases:
- **Insufficient funds** → Reject transfer with HTTP `402` status code.  
- **Exceeding daily limit** → Reject transfer with HTTP `429` status code.  

# Runnning the Server
Command: uvicorn main:app --reload
The API will be available at - http://localhost:8000

Testing 
Postman Collection: Included under /docs/core-banking.postman_collection.json

cURL Example:
