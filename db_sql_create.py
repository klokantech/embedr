import sqlite3

conn = sqlite3.connect('data/sql/db.db')
c = conn.cursor()
c.execute("CREATE VIRTUAL TABLE Items USING fts4(id VARCHAR(256) PRIMARY KEY, title, creator, source, institution, institution_link, license, description, url, image_meta, timestamp)")
c.execute("CREATE TABLE Tasks (task_id , batch_id, item_id, status, url)")
conn.commit()
conn.close()
