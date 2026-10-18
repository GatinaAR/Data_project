import streamlit as st
import sqlite3
import pandas as pd

# Настройка страницы
st.set_page_config(page_title="Медиа-Пульс", layout="wide")
st.title("📰 Медиа-Пульс: Аналитика новостей")

# Подключение к базе
conn = sqlite3.connect('news.db')

# Загружаем все новости
df = pd.read_sql("SELECT * FROM articles", conn)

# --- БОКОВАЯ ПАНЕЛЬ С ФИЛЬТРАМИ ---
st.sidebar.header("Фильтры и поиск")

# 1. ПОИСК (Операция Read)
search_query = st.sidebar.text_input("🔍 Поиск по заголовку", "")

# Фильтр по источнику
sources = ["Все"] + list(df['source'].dropna().unique())
selected_source = st.sidebar.selectbox("Источник", sources)

# Фильтр по категории
categories = ["Все"] + list(df['category'].dropna().unique())
selected_category = st.sidebar.selectbox("Категория", categories)

# Фильтр по дате
date_range = st.sidebar.date_input("Диапазон дат", [])

# Применяем фильтры
filtered_df = df.copy()

# Применяем поиск
if search_query:
    filtered_df = filtered_df[filtered_df['title'].str.contains(search_query, case=False, na=False)]

if selected_source != "Все":
    filtered_df = filtered_df[filtered_df['source'] == selected_source]
if selected_category != "Все":
    filtered_df = filtered_df[filtered_df['category'] == selected_category]
    
if len(date_range) == 2:
    filtered_df['published_date'] = pd.to_datetime(filtered_df['published_date'], errors='coerce')
    filtered_df = filtered_df[
        (filtered_df['published_date'].dt.date >= date_range[0]) &
        (filtered_df['published_date'].dt.date <= date_range[1])
    ]

# --- ДОБАВЛЕНИЕ НОВОСТИ (Операция Create) ---
with st.expander("➕ Добавить новую новость"):
    with st.form("add_news_form"):
        new_source = st.text_input("Источник (например, РИА Новости)")
        new_title = st.text_input("Заголовок")
        new_link = st.text_input("Ссылка (URL)")
        submit = st.form_submit_button("Добавить в базу")
        
        if submit:
            if new_title and new_source:
                cursor = conn.cursor()
                try:
                    cursor.execute(
                        "INSERT INTO articles (source, title, link, published_date, category) VALUES (?, ?, ?, datetime('now'), 'Без категории')",
                        (new_source, new_title, new_link)
                    )
                    conn.commit()
                    st.success("Новость успешно добавлена! Обновите страницу.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Ошибка при добавлении: {e}")
            else:
                st.warning("Заполните хотя бы источник и заголовок.")

# --- ОСНОВНАЯ ЧАСТЬ ---
st.subheader(f"Найдено новостей: {len(filtered_df)}")

# Переименовываем столбцы для красивого вывода
display_df = filtered_df[['id', 'source', 'title', 'published_date', 'category']].copy()
display_df.columns = ['ID', 'Источник', 'Заголовок', 'Дата публикации', 'Категория']

# Показываем таблицу
st.dataframe(display_df, use_container_width=True, hide_index=True)

# Кнопка удаления (Операция Delete)
if st.button("🗑 Удалить первую новость из списка"):
    if len(filtered_df) > 0:
        first_id = int(filtered_df.iloc[0]['id'])
        cursor = conn.cursor()
        cursor.execute("DELETE FROM articles WHERE id = ?", (first_id,))
        conn.commit()
        st.success(f"Новость с ID {first_id} удалена. Обновите страницу.")
        st.rerun()

# --- ГРАФИКИ ---
st.subheader("📊 Аналитика")

col1, col2 = st.columns(2)

with col1:
    st.write("**Новости по источникам**")
    source_counts = filtered_df['source'].value_counts()
    st.bar_chart(source_counts)

with col2:
    st.write("**Активность по часам**")
    filtered_df['hour'] = pd.to_datetime(filtered_df['published_date'], errors='coerce').dt.hour
    hourly_counts = filtered_df.groupby('hour').size()
    hourly_counts = hourly_counts.reindex(range(24), fill_value=0)
    st.bar_chart(hourly_counts)

conn.close()