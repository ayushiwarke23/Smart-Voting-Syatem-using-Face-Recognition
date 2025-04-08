import sqlite3

def create_db():
    conn = sqlite3.connect("database.db")
    
    # Table for users
    conn.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        aadhar TEXT UNIQUE NOT NULL,
        mobile TEXT NOT NULL,
        face_encoding BLOB NOT NULL,
        voted INTEGER DEFAULT 0
    )""")

    # Table for votes
    conn.execute("""
    CREATE TABLE IF NOT EXISTS votes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        candidate TEXT NOT NULL
    )""")

    conn.execute("""
        CREATE TABLE IF NOT EXISTS candidates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            candidate_name TEXT NOT NULL,
            party_name TEXT NOT NULL,
            party_logo TEXT NOT NULL
        )
    """)

    # Pre-fill candidates with filenames (ensure these files exist in static/uploads/)
    existing = conn.execute("SELECT COUNT(*) FROM candidates").fetchone()[0]
    if existing == 0:
        conn.execute("INSERT INTO candidates (candidate_name, party_name, party_logo) VALUES (?, ?, ?)",
                     ("Ravi Kumar", "Progressive Alliance", "progressive.png"))
        conn.execute("INSERT INTO candidates (candidate_name, party_name, party_logo) VALUES (?, ?, ?)",
                     ("Sneha Shah", "National Unity", "unity.png"))
        conn.execute("INSERT INTO candidates (candidate_name, party_name, party_logo) VALUES (?, ?, ?)",
                     ("Arjun Mehta", "Green Future", "green.png"))

    conn.commit()
    conn.close()

if __name__ == '__main__':
    create_db()