import sqlite3
conn = sqlite3.connect('news.db')
conn.execute("UPDATE articles SET category_attempts = 0, category_status = 'pending' WHERE category_status = 'pending'")
conn.commit()
conn.close()
print("✅ Счетчики ошибок сброшены!")