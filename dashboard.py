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
st.sidebar.header("Фильтры")

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

# --- ОСНОВНАЯ ЧАСТЬ ---
st.subheader(f"Найдено новостей: {len(filtered_df)}")

# Показываем таблицу
st.dataframe(filtered_df[['id', 'source', 'title', 'published_date', 'category']], use_container_width=True)

# Кнопка удаления
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
    st.write("**Активность по дням**")
    filtered_df['date_only'] = pd.to_datetime(filtered_df['published_date'], errors='coerce').dt.date
    daily_counts = filtered_df.groupby('date_only').size()
    st.line_chart(daily_counts)

conn.close()