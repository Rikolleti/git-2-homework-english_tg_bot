import random
import configparser
import db
import telebot
from telebot import types
from telebot.handler_backends import State, StatesGroup
from telebot.storage import StateMemoryStorage

state_storage = StateMemoryStorage()

config = configparser.ConfigParser()
config.read('settings.ini')
token_tg = config['Telegram']['token_tg'].strip()

TOKEN = token_tg
bot = telebot.TeleBot(TOKEN, state_storage=state_storage)

class Command:
    START = 'Начать 🚀'
    ADD_WORD = 'Добавить слово ➕'
    DELETE_WORD = 'Удалить слово🔙'
    NEXT = 'Дальше ⏭'
    HELP = 'Помощь️'

class MyStates(StatesGroup):
    target_word = State()
    russian_word = State()
    other_words = State()

def from_db(user_id):
    words = db.show_words(user_id)
    return words

def count(user_id):
    count_words = db.count_words(user_id)
    return count_words

def delete_word_from_db(russian_word, user_id):
    res = db.delete_word(russian_word, user_id)
    return res

def insert_words(target_word,russian_word,other_word,user_id):
    res = db.insert_words_from_user(target_word,russian_word,other_word,user_id)
    return res

# HELP
@bot.message_handler(func=lambda message: message.text == Command.HELP)
def help_command(message):
    help_text = """
    🤖 **Помощь по боту:**

    - *Добавить слово ➕*: Добавьте новое слово в ваш словарь.
    - *Удалить слово 🔙*: Удалите слово из вашего словаря.
    - *Дальше ⏭*: Перейдите к следующему слову.
    - *Помощь ℹ️*: Показывает это сообщение.

    Используйте команду /start, чтобы начать заново.
    """
    bot.send_message(message.chat.id, help_text, parse_mode="Markdown")

# ВЫВОД СЛОВ
@bot.message_handler(commands=['cards', 'start'])
def create_cards(message):
    user = message.from_user
    greeting = (
        f"🌟 Привет, {user.first_name}! 🌟\n\n"
        f"Рад видеть тебя здесь! 🎉\n"
        f"Я — твой персональный помощник в изучении английского языка. 📚\n\n"
        f"С моей помощью ты сможешь:\n"
        f"✅ Учить новые слова\n"
        f"✅ Практиковать их в увлекательной форме\n\n"
        f"Готов начать? Тогда жми на кнопку 'Начать' ниже! 👇"
    )
    markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    start_btn = types.KeyboardButton(Command.START)
    markup.add(start_btn)
    bot.send_message(message.chat.id, greeting, reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == Command.START)
def start(message):
    user = message.from_user
    show_card(message, user.id, 0)

@bot.message_handler(func=lambda message: message.text == Command.NEXT)
def next_cards(message):
    user = message.from_user
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        current_index = data.get('current_index', 0) + 1
    show_card(message, user.id, current_index)

def show_card(message, user_id, current_index):
    words = from_db(user_id)
    if not words:
        bot.send_message(message.chat.id, "У вас нет доступных слов.")
        return
    if current_index < len(words):
        word = words[current_index]
        target_word = word['target_word']
        russian_word = word['russian_word']
        other_words = word['other_words']

        markup = types.ReplyKeyboardMarkup(row_width=2)
        target_word_btns = [types.KeyboardButton(target_word)]
        other_words_list = other_words.split(", ")
        other_words_btns = [types.KeyboardButton(word) for word in other_words_list]
        buttons = target_word_btns + other_words_btns
        random.shuffle(buttons)

        next_btn = types.KeyboardButton(Command.NEXT)
        add_word_btn = types.KeyboardButton(Command.ADD_WORD)
        delete_word_btn = types.KeyboardButton(Command.DELETE_WORD)
        help_btn = types.KeyboardButton(Command.HELP)

        buttons.extend([next_btn, add_word_btn, delete_word_btn, help_btn])
        markup.add(*buttons)

        choose = f"Выбери перевод слова:\n🇷🇺 {russian_word}"
        bot.send_message(message.chat.id, choose, reply_markup=markup)
        bot.set_state(message.from_user.id, MyStates.target_word, message.chat.id)
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data['target_word'] = target_word
            data['russian_word'] = russian_word
            data['current_index'] = current_index
    else:
        bot.send_message(message.chat.id, "Ты выучил все слова !", reply_markup=telebot.types.ReplyKeyboardRemove())

# ДОБАВЛЕНИЕ СЛОВ
@bot.message_handler(func=lambda message: message.text == Command.ADD_WORD)
def add_word(message):
    bot.send_message(message.chat.id, "Введите слово на английском:")
    bot.register_next_step_handler(message, process_target_word)

def process_target_word(message):
    target_word = message.text
    bot.send_message(message.chat.id, "Введите перевод на русский:")
    bot.register_next_step_handler(message, process_russian_word, target_word)

def process_russian_word(message, target_word):
    russian_word = message.text
    bot.send_message(message.chat.id, "Введите 3 некорретных варианта перевода на английском через запятую:")
    bot.register_next_step_handler(message, process_other_words, target_word, russian_word)

def process_other_words(message, target_word, russian_word):
    other_words = message.text
    user_id = message.from_user.id
    insert_words(target_word, russian_word, other_words, user_id)
    bot.send_message(message.chat.id, "Слово успешно добавлено!")
    from_db(user_id)
    res = count(user_id)
    bot.send_message(message.chat.id, f"Общее количество слов для обучения: {res} 🤩")


# УДАЛЕНИЕ СЛОВ
@bot.message_handler(func=lambda message: message.text == Command.DELETE_WORD)
def delete_word(message):
    bot.send_message(message.chat.id, "Введите слово на русском, которое хотите удалить:")
    bot.register_next_step_handler(message, process_delete_word)

def process_delete_word(message):
    russian_word = message.text
    user_id = message.from_user.id
    res = delete_word_from_db(russian_word, user_id)
    success_output = f"Слово '{russian_word}' удалено."
    failed_output = f"Слово '{russian_word}' отсутствует в базе или не связано с вашим аккаунтом."
    if res:
        bot.send_message(message.chat.id, success_output)
    else:
        bot.send_message(message.chat.id, failed_output)
    from_db(user_id)

# ПРОВЕРКА НА КОРРЕКТНОСТЬ ОТВЕТА
@bot.message_handler(func=lambda message: True)
def message_reply(message):
    success_messages = [
        'Отлично, ты молодец! 😍',
        'Так держать! 😍',
        'Супер! Ты справляешься! 🎉',
        'Великолепно! Продолжай в том же духе! 💪'
    ]

    failed_messages = [
        'Ошибка, попробуй еще раз. 😊',
        'Не переживай, ты почти у цели! 💪',
        'Попробуй еще раз, у тебя обязательно получится! 😉',
        'Ошибка — это часть обучения, попробуй снова! 🌟'
    ]

    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        target_word = data.get('target_word')
    if message.text == target_word:
        bot.send_message(message.chat.id, random.choice(success_messages))
        next_cards(message)
    else:
        bot.send_message(message.chat.id, random.choice(failed_messages))

################MAIN################
if __name__ == '__main__':
    print("Bot is running")
    bot.polling(none_stop=True)