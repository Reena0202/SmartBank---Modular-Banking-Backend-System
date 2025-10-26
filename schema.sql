-- Create Database
USE MY_PROJECTS;

Drop tables if they exist
DROP TABLE IF EXISTS audit_logs;
DROP TABLE IF EXISTS account_daily_usage;
DROP TABLE IF EXISTS transfers;
DROP TABLE IF EXISTS accounts;

-- Table: accounts
CREATE TABLE accounts (
  id CHAR(36) PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  balance DECIMAL(20,2) NOT NULL DEFAULT 0.00,
  daily_limit DECIMAL(20,2) NOT NULL DEFAULT 100000.00,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table: transfers
CREATE TABLE transfers (
  id CHAR(36) PRIMARY KEY,
  from_account_id CHAR(36) NOT NULL,
  to_account_id CHAR(36) NOT NULL,
  amount DECIMAL(20,2) NOT NULL,
  currency CHAR(3) DEFAULT 'INR',
  status ENUM('COMPLETED','FAILED') DEFAULT 'COMPLETED',
  reason VARCHAR(255) DEFAULT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (from_account_id) REFERENCES accounts(id),
  FOREIGN KEY (to_account_id) REFERENCES accounts(id)
);

-- Table: account_daily_usage
CREATE TABLE account_daily_usage (
  id CHAR(36) PRIMARY KEY,
  account_id CHAR(36) NOT NULL,
  date DATE NOT NULL,
  total_transferred DECIMAL(20,2) NOT NULL DEFAULT 0.00,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY (account_id, date),
  FOREIGN KEY (account_id) REFERENCES accounts(id)
);

-- Table: audit_logs
CREATE TABLE audit_logs (
  id CHAR(36) PRIMARY KEY,
  action VARCHAR(100) NOT NULL,
  details TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Sample Accounts
INSERT INTO accounts (id, name, balance, daily_limit) VALUES
(UUID(), 'Reena', 5000.00, 10000.00),
(UUID(), 'Rahul', 3000.00, 10000.00),
(UUID(), 'Anita', 7000.00, 15000.00);

-- Verify
SELECT * FROM accounts;
