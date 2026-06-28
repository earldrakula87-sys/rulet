import random
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler
from telegram.utils.types import ContextTypes
import asyncio

TOKEN = '8787088034:AAEtTxeN-t9CaNKtdlWqBwRinr1CBC-5uHw'  # заменить на ваш токен Telegram-бота

# Константы
RouletteNumbers = [str(i) for i in range(10)]  # цифры от 0 до 9
EmojiWin = '🎉'  # эмодзи праздника

# Функция для генерации случайного числа
def generate_random_number():
    return random.choice(RouletteNumbers)

# Функция для обработки команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    buttons = [
        InlineKeyboardButton(text='0', callback_data='0'),
        InlineKeyboardButton(text='1', callback_data='1'),
        InlineKeyboardButton(text='2', callback_data='2'),
        InlineKeyboardButton(text='3', callback_data='3'),
        InlineKeyboardButton(text='4', callback_data='4'),
        InlineKeyboardButton(text='5', callback_data='5'),
        InlineKeyboardButton(text='6', callback_data='6'),
        InlineKeyboardButton(text='7', callback_data='7'),
        InlineKeyboardButton(text='8', callback_data='8'),
        InlineKeyboardButton(text='9', callback_data='9')
    ]
    reply_markup = InlineKeyboardMarkup([[button] for button in buttons])
    await context.bot.send_message(chat_id=update.effective_chat.id, text='Выберите цифру:', reply_markup=reply_markup)

# Функция для обработки нажатия на кнопку
async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.callback_query.data
    random_number = generate_random_number()
    if user_input == random_number:
        await context.bot.send_message(chat_id=update.effective_chat.id, text='Вы выиграли! ' + EmojiWin)
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f'К сожалению, вы не угадали. Correct answer: {random_number}')

# Создаем бота
application = Application.builder().token(TOKEN).build()

start_handler = CommandHandler('start', start)
callback_handler = CallbackQueryHandler(callback_handler)

application.add_handler(start_handler)
application.add_handler(callback_handler)

async def main():
    await application.run_polling()

if __name__ == '__main__':
    asyncio.run(main())
