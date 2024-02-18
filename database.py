import aiosqlite

async def create_table():
    # создаем соединение с базой данных (если она не существует- она будет создана)
    async with aiosqlite.connect('quiz_bot.db') as db:
        await db.execute('''CREATE TABLE IF NOT EXISTS quiz_state (user_id INTEGER PRIMARY KEY, question_index INTEGER, score INTEGER)''')
        # Сохраняем изменения
        await db.commit()

async def update_quiz_index(user_id, index_question, index_score):
    print('Call update quiz index', index_question)
    # Создаем соединение с базой данных (если она не существует, она будет создана)
    async with aiosqlite.connect('quiz_bot.db') as db:
        # Вставляем новую запись или заменяем ее, если с данным user_id уже существует
        await db.execute('INSERT OR REPLACE INTO quiz_state (user_id, question_index, score) VALUES (?, ?, ?)', (user_id, index_question, index_score))
        # Сохраняем изменения
        await db.commit()
