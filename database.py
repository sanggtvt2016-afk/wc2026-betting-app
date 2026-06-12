import sqlite3
import pandas as pd
from datetime import datetime

DB_NAME = "predictions.db"

def get_connection():
    return sqlite3.connect(DB_NAME, check_same_thread=False)

def init_db():
    conn = get_connection()
    c = conn.cursor()
    
    # Bảng người dùng
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    username TEXT PRIMARY KEY,
                    role TEXT,
                    points INTEGER DEFAULT 1000
                 )''')
    
    # Bảng sự kiện
    c.execute('''CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT,
                    options TEXT,
                    status TEXT DEFAULT 'open',
                    result TEXT,
                    created_at TEXT
                 )''')
                 
    # Bảng dự đoán
    c.execute('''CREATE TABLE IF NOT EXISTS predictions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT,
                    event_id INTEGER,
                    predicted_option TEXT,
                    bet_amount INTEGER,
                    status TEXT DEFAULT 'pending',
                    created_at TEXT
                 )''')
                 
    # Bảng lịch sử điểm (Transactions)
    c.execute('''CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT,
                    amount INTEGER,
                    reason TEXT,
                    created_at TEXT
                 )''')
                 
    # Tạo tài khoản admin mặc định nếu chưa có
    c.execute("INSERT OR IGNORE INTO users (username, role, points) VALUES ('admin', 'admin', 999999)")
    
    conn.commit()
    conn.close()

def get_user(username):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=?", (username,))
    return c.fetchone()

def create_user(username):
    conn = get_connection()
    c = conn.cursor()
    c.execute("INSERT INTO users (username, role, points) VALUES (?, 'player', 1000)", (username,))
    # Ghi log nhận điểm ban đầu
    c.execute("INSERT INTO transactions (username, amount, reason, created_at) VALUES (?, 1000, 'Khởi tạo tài khoản', ?)", 
              (username, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

def update_user_points(username, amount, reason):
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE users SET points = points + ? WHERE username = ?", (amount, username))
    c.execute("INSERT INTO transactions (username, amount, reason, created_at) VALUES (?, ?, ?, ?)", 
              (username, amount, reason, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()
