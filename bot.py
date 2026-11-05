import os
import telebot
from config import *
from logic import *

bot = telebot.TeleBot(TOKEN)
manager = DB_Map(DATABASE)
manager.create_user_table()


@bot.message_handler(commands=['start'])
def handle_start(message):
    bot.send_message(message.chat.id, "Привет! Я бот, который может показывать города на карте. Напиши /help для списка команд.")


@bot.message_handler(commands=['help'])
def handle_help(message):
    bot.send_message(
        message.chat.id,
        "Доступные команды:\n"
        "/show_city <город> — показать город на карте (на английском)\n"
        "/remember_city <город> — сохранить город в избранное\n"
        "/show_my_cities — показать все сохранённые города\n"
        "/all — показать все города из базы на карте"
    )


@bot.message_handler(commands=['show_city'])
def handle_show_city(message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        bot.send_message(message.chat.id, "Укажите город: /show_city Moscow")
        return

    city_name = parts[1].strip()
    coords = manager.get_coordinates(city_name)
    if not coords:
        bot.send_message(message.chat.id, f"Город «{city_name}» не найден. Убедись, что он написан на английском.")
        return

    bot.send_message(message.chat.id, f"Генерирую карту для «{city_name}»...")
    path = f"city_{message.chat.id}.png"
    try:
        manager.create_grapf(path, [city_name])
        with open(path, 'rb') as photo:
            bot.send_photo(message.chat.id, photo, caption=f"Город: {city_name}")
    except Exception as e:
        bot.send_message(message.chat.id, f"Ошибка при создании карты: {e}")
    finally:
        if os.path.exists(path):
            os.remove(path)


@bot.message_handler(commands=['remember_city'])
def handle_remember_city(message):
    user_id = message.chat.id
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        bot.send_message(message.chat.id, "Укажите город: /remember_city Moscow")
        return
    city_name = parts[1].strip()
    if manager.add_city(user_id, city_name):
        bot.send_message(message.chat.id, f'Город {city_name} успешно сохранен!')
    else:
        bot.send_message(message.chat.id, 'Такого города я не знаю. Убедись, что он написан на английском!')


@bot.message_handler(commands=['show_my_cities'])
def handle_show_visited_cities(message):
    cities = manager.select_cities(message.chat.id)
    if not cities:
        bot.send_message(message.chat.id, "У вас пока нет сохранённых городов. Используйте /remember_city <город>.")
        return

    bot.send_message(message.chat.id, f"Генерирую карту ваших городов ({len(cities)})...")
    path = f"my_cities_{message.chat.id}.png"
    try:
        manager.create_grapf(path, cities)
        with open(path, 'rb') as photo:
            bot.send_photo(message.chat.id, photo, caption="Ваши сохранённые города")
    except Exception as e:
        bot.send_message(message.chat.id, f"Ошибка при создании карты: {e}")
    finally:
        if os.path.exists(path):
            os.remove(path)


@bot.message_handler(commands=['all'])
def handle_all_cities(message):
    # Получаем все города из базы
    conn = __import__('sqlite3').connect(DATABASE)
    with conn:
        cursor = conn.cursor()
        cursor.execute("SELECT city FROM cities")
        all_cities = [row[0] for row in cursor.fetchall()]
    conn.close()

    if not all_cities:
        bot.send_message(message.chat.id, "В базе данных нет городов.")
        return

    bot.send_message(message.chat.id, f"Генерирую карту всех городов ({len(all_cities)})...")
    path = f"all_cities_{message.chat.id}.png"
    try:
        manager.create_grapf(path, all_cities)
        with open(path, 'rb') as photo:
            bot.send_photo(message.chat.id, photo, caption=f"Всего городов в базе: {len(all_cities)}")
    except Exception as e:
        bot.send_message(message.chat.id, f"Ошибка при создании карты: {e}")
    finally:
        if os.path.exists(path):
            os.remove(path)


if __name__ == "__main__":
    bot.polling(non_stop=True)