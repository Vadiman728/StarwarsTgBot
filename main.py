import asyncio
import logging
from aiogram import F
import aiosqlite
from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command
from aiogram import types
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

from questions import quiz_data
from database import create_table, update_quiz_index


# Включаем логирование, чтобы не пропустить важные сообщения
logging.basicConfig(level=logging.INFO)

# Замените "YOUR_BOT_TOKEN" на токен, который вы получили от BotFather
API_TOKEN = '6863327666:AAH2ZDIhqBWZirALbGGi95qwq_89FncZ9nw'

# Объект бота
bot = Bot(token=API_TOKEN)
# Диспетчер
dp = Dispatcher()


# Хэндлер на команду /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    # создаем сборщика клавиатур типа Reply
    builder = ReplyKeyboardBuilder()
    # добавляем в сборщик одну кнопку
    builder.add(types.KeyboardButton(text="Начать испытание"))
    await message.answer("Я хочу поиграть с тобой в одну игру...")
    await asyncio.sleep(2)
    await message.answer("В Квиз по звездным войнам \U0001F60E ")
    await asyncio.sleep(2)
    await message.answer("Если ты не испугался, пиши /quiz ", reply_markup=builder.as_markup(resize_keyboard=True))

# Хэндлер на команду /quiz
@dp.message(F.text=="Начать испытание")
@dp.message(Command("quiz"))
async def cmd_quiz(message: types.Message):
    # Логика начала квиза
    await message.answer("Проверил свой световой меч? Разогрел двигатель тысячелетнего сокола? тогда погнали. Да прибудет с тобой сила ")
    await new_quiz(message)

async def get_quiz_index(user_id):
    # Подключаемся к базе данных
    async with aiosqlite.connect('quiz_bot.db') as db:
        # Получаем запись для заданного пользователя
        async with db.execute("SELECT question_index FROM quiz_state WHERE user_id = (?)", (user_id,))as cursor:
            results = await cursor.fetchone()
            if results is not None:
                return results[0]
            else:
                return 0

async def get_score_index(user_id):
    # Подключаемся к базе данных
    async with aiosqlite.connect('quiz_bot.db') as db:
        # Получаем запись для заданного пользователя
        async with db.execute("SELECT score FROM quiz_state WHERE user_id = (?)", (user_id,))as cursor:
            score = await cursor.fetchone()
            if score is not None:
                return score[0]
            else:
                return 0
async def new_quiz(message):
    # получаем Id пользователя, отправившего сообщение
    user_id = message.from_user.id
    # сбрасываем значение текущего индекса вопроса квиза в 0
    current_question_index = 0
    current_score_index = 0
    await update_quiz_index(user_id, current_question_index, current_score_index)
    #запрашиваем новый вопрос для квиза
    await get_question(message, user_id)

async def get_question(message, user_id):
    # Запрашиваем из базы текущий индекс для вопроса
    current_question_index = await get_quiz_index(user_id)
    # Получаем индекс правильного ответа для текущего вопроса
    correct_index = quiz_data[current_question_index]['correct_option']
    # Получаем список вариантов ответа для текущего вопроса
    opts = quiz_data[current_question_index]['options']
    # Функция генерации кнопок для текущего вопроса квиза
    # В качестве аргументов передаем варианты ответов и значение правильного ответа (не индекс!)
    kb = generate_options_keyboard(opts, opts[correct_index])
    # Отправляем в чат сообщение с вопросом, прикрепляем сгенерированные кнопки
    await message.answer(f"{quiz_data[current_question_index]['question']}", reply_markup=kb)

@dp.message(Command('raiting'))
async def show_raiting(message: types.Message):
    async with aiosqlite.connect('quiz_bot.db') as db:
        # Выполняем SQL-запрос для получения топ-3 пользователей по самому высокому значению score
        async with db.execute("SELECT score, user_id FROM quiz_state GROUP BY score ORDER BY MAX(score) DESC LIMIT 3")as cursor:
            result = await cursor.fetchall()
    if result == None:
        await message.answer('Рейтинг пуст')
    else:
        raiting_message = []
        for i in range(0,len(result)):
            a = f'Пользователь силы с id {result[i][1]} занимает {i+1} место ({result[i][0]} очков)'
            raiting_message.append(a)
        await message.answer('\n'.join(raiting_message))




def generate_options_keyboard(answer_options, right_answer):
    # Создаем сборщика клавиатур типа Inline
    builder = InlineKeyboardBuilder()

    # В цикле создаем 4 Inline кнопки, а точнее Callback- кнопки
    for option in answer_options:
        builder.add(types.InlineKeyboardButton(
            # Текст на кнопках соответствует вариантам ответов
            text=option,
            # Присваиваем данные для колбэк запроса.
            # Если ответ верный сформируется колбэк-запрос с данными 'right_answer'
            # Если ответ неверный сформируется колбэк-запрос с данными 'wrong_answer'
            callback_data="right_answer" if option == right_answer else "wrong_answer")
        )

    # Выводим по одной кнопке в столбик
    builder.adjust(1)
    return builder.as_markup()

@dp.callback_query(F.data == "right_answer")
async def right_answer(callback: types.CallbackQuery):
    # редактируем текущее сообщение с целью убрать кнопки (reply_markup = None)
    await callback.bot.edit_message_reply_markup(
        chat_id=callback.from_user.id,
        message_id=callback.message.message_id,
        reply_markup=None
    )
    #Получение текущего вопроса для данного пользователя
    current_question_index = await get_quiz_index(callback.from_user.id)
    current_score_index = await get_score_index(callback.from_user.id)
    #Отправляем в чат сообщение, что ответ верный
    await callback.message.answer("А ты мощный пользователь силы... Что ж, едем дальше")
    # Обновляем номера текущего вопроса в БД
    current_question_index = current_question_index + 1
    current_score_index =current_score_index + 1
    await update_quiz_index(callback.from_user.id, current_question_index, current_score_index)
    # Проверяем достигнут ли конец квиза
    current_question_index = await get_quiz_index(callback.from_user.id)
    if current_question_index < len(quiz_data):
        # Следующий вопрос
        await get_question(callback.message, callback.from_user.id)
    else:
        # Уведомление об окончании квиза
        await callback.message.answer('Это был последний вопрос. Ты здорово постарался')

@dp.callback_query(F.data == "wrong_answer")
async def wrong_answer(callback: types.CallbackQuery):
    # Редактируем текущее сообщение с целью убрать кнопки (reply_markup= None)
    await callback.bot.edit_message_reply_markup(
        chat_id=callback.from_user.id,
        message_id= callback.message.message_id,
        reply_markup= None
    )
    # Получение текущего вопроса для данного пользователя
    current_question_index = await get_quiz_index(callback.from_user.id)
    current_score_index = await get_score_index(callback.from_user.id)
    correct_option = quiz_data[current_question_index]['correct_option']
    # Отправляем в чат сообщение об ошибке с указанием верного ответа
    await callback.message.answer(f"К сожалению ты ошибся. Правильный ответ: {quiz_data[current_question_index]['options'][correct_option]}")
    # Обновление номера текущего вопроса в базе данных
    current_question_index += 1
    current_score_index = current_score_index
    await update_quiz_index(callback.from_user.id, current_question_index,current_score_index)

    # Проверяем достигнут ли конец квиза
    if current_question_index < len(quiz_data):
        # Следующий вопрос
        await get_question(callback.message, callback.from_user.id)
    else:
        # Уведомление об окончании квиза
        await callback.message.answer('Это был последний вопрос. Ты здорово постарался')

# Запуск процесса поллинга новых апдейтов
async def main():
    await create_table()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())