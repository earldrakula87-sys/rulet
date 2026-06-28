TOKEN = '8787088034:AAEtTxeN-t9CaNKtdlWqBwRinr1CBC-5uHw'  # заменить на ваш токен Telegram-бота

import random
import logging
from telegram import Application, Update, Context
from telegram.ext import CommandHandler, CallbackQueryHandler

# Константы
RouletteNumbers = [str(i) for i in range(10)]  # цифры от 0 до 9
EmojiWin = '🎉'  # эмодзи праздника

# Функция для генерации случайного числа
def generate_random_number():
    return random.choice(RouletteNumbers)

# Функция для обработки команды /start
async def start(update: Update, context: Context):
    await context.bot.send_message(chat_id=update.effective_chat.id, text='Давайте сыграем в рулетку!')
    buttons = []
    for number in RouletteNumbers:
        button = {'text': number, 'callback_data': number}
        buttons.append(button)
    reply_markup = {'inline_keyboard': [[button] for button in buttons]}
    await context.bot.send_message(chat_id=update.effective_chat.id, text='Выберите цифру:', reply_markup=reply_markup)

# Функция для обработки нажатия на кнопку
async def callback_handler(update: Update, context: Context):
    user_input = update.callback_query.data
    random_number = generate_random_number()
    if user_input == random_number:
        await context.bot.send_message(chat_id=update.effective_chat.id, text='Вы выиграли! ' + EmojiWin)
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f'К сожалению, вы не угадали. Correct answer: {random_number}')

# Создаем бота
application = Application(token=TOKEN)

start_handler = application.on_command('start', start)
callback_handler = application.on_callback_query(callback_handler)

async def main():
    await application.run_polling()

if __name__ == '__main__':
    asyncio.run(main())
