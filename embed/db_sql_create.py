import sqlite3

conn = sqlite3.connect('data/sql/db.db')
c = conn.cursor()
c.execute("CREATE TABLE IF NOT EXISTS Batch (batch_id INTEGER PRIMARY KEY AUTOINCREMENT, batch_data TEXT)")
c.execute("CREATE TABLE IF NOT EXISTS Task (task_id INTEGER, batch_id INTEGER, item_id VARCHAR(256), status VARCHAR(16), url TEXT, message INTEGER)")
c.execute("CREATE INDEX test_index ON Task (batch_id, item_id)")

conn.commit()
conn.close()
