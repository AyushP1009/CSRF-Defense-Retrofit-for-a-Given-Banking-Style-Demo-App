import sqlite3

DB_NAME = "bank.db"


def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("DROP TABLE IF EXISTS transactions")
    cur.execute("DROP TABLE IF EXISTS users")

    cur.execute("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            balance REAL NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender TEXT NOT NULL,
            receiver TEXT NOT NULL,
            amount REAL NOT NULL,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cur.execute("INSERT INTO users (username, password, balance) VALUES ('alice', 'password123', 1000)")
    cur.execute("INSERT INTO users (username, password, balance) VALUES ('bob', 'password123', 1000)")
    cur.execute("INSERT INTO users (username, password, balance) VALUES ('attacker', 'password123', 100)")

    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_db()
    print("Database created with demo users.")