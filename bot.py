import random
import logging

# Константы
RouletteNumbers = [str(i) for i in range(10)]  # цифры от 0 до 9
EmojiWin = '🎉'  # эмодзи праздника

# Функция для генерации случайного числа
def generate_random_number():
    return random.choice(RouletteNumbers)

# Функция для обработки команды /start
def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text='Давайте сыграем в рулетку!')
    buttons = []
    for number in RouletteNumbers:
        button = {'text': number, 'callback_data': number}
        buttons.append(button)
    reply_markup = {'inline_keyboard': [[button] for button in buttons]}
    context.bot.send_message(chat_id=update.effective_chat.id, text='Выберите цифру:', reply_markup=reply_markup)

# Функция для обработки нажатия на кнопку
def callback_handler(update, context):
    user_input = update.callback_query.data
    random_number = generate_random_number()
    if user_input == random_number:
        context.bot.send_message(chat_id=update.effective_chat.id, text='Вы выиграли! ' + EmojiWin)
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text=f'К сожалению, вы не угадали. Correct answer: {random_number}')

# Создаем бота
TOKEN = '8787088034:AAEtTxeN-t9CaNKtdlWqBwRinr1CBC-5uHw'  # заменить на ваш токен Telegram-бота

def main():
    updater = Updater(TOKEN)

    dp = updater.dispatcher

    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(CallbackQueryHandler(callback_handler))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
