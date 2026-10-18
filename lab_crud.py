import sqlite3

def search_articles(keyword):
    """Поиск новостей по ключевому слову в заголовке"""
    conn = sqlite3.connect('news.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, source, title, category FROM articles WHERE title LIKE ?", ('%' + keyword + '%',))
    results = cursor.fetchall()
    conn.close()
    return results

def delete_article(article_id):
    """Удаление новости по ID"""
    conn = sqlite3.connect('news.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM articles WHERE id = ?", (article_id,))
    conn.commit()
    conn.close()
    print(f"Новость с ID {article_id} удалена.")

if __name__ == "__main__":
    print("--- Поиск по слову 'Казань' ---")
    results = search_articles("Казань")
    for row in results[:5]:
        print(row)

    if results:
        delete_article(results[0][0])
        print("Проверка: новость удалена.")