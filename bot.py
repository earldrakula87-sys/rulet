import random
import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

TOKEN = '8787088034:AAEtTxeN-t9CaNKtdlWqBwRinr1CBC-5uHw'  # заменить на ваш токен Telegram-бота

# Включаем логирование
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Константы
RouletteNumbers = [str(i) for i in range(10)]
EmojiWin = '🎉'
EmojiLose = '❌'
EmojiCoin = '🪙'

# Временная база данных для очков (в памяти процесса)
# Ключ — user_id, значение — количество очков
user_scores = {}

def generate_random_number():
    return random.choice(RouletteNumbers)

# Функция для построения клавиатуры в виде сетки
def build_grid_keyboard():
    keyboard = []
    current_row = []
    
    for number in RouletteNumbers:
        button = InlineKeyboardButton(text=number, callback_data=number)
        current_row.append(button)
        
        # Как только в ряду набралось 5 кнопок, добавляем ряд и создаем новый
        if len(current_row) == 5:
            keyboard.append(current_row)
            current_row = []
            
    return InlineKeyboardMarkup(keyboard)

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    # Если пользователя нет в базе, выдаем стартовые 100 очков
    if user_id not in user_scores:
        user_scores[user_id] = 100
        
    current_score = user_scores[user_id]
    reply_markup = build_grid_keyboard()
    
    text = (
        f"Добро пожаловать в рулетку!\n\n"
        f"{EmojiCoin} Ваш баланс: **{current_score} очков**.\n"
        f"Каждая игра стоит **10 очков**. За выигрыш вы получите **100 очков**!\n\n"
        f"Выберите цифру:"
    )
    
    await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")

# Обработка нажатия на кнопки
async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    user_input = query.data
    
    # Проверяем, есть ли пользователь в базе (на случай перезапуска бота)
    if user_id not in user_scores:
        user_scores[user_id] = 100
        
    # Проверяем баланс: хватает ли на ставку
    if user_scores[user_id] < 10:
        await query.message.reply_text(
            f"У вас закончились очки! {EmojiLose}\n"
            f"Введите /start, чтобы обновить баланс до 100 очков."
        )
        # Сбрасываем баланс для возможности играть снова
        user_scores[user_id] = 100
        return

    # Списываем плату за игру
    user_scores[user_id] -= 10
    random_number = generate_random_number()
    
    if user_input == random_number:
        user_scores[user_id] += 100  # Приз за победу
        result_text = f"{EmojiWin} Вы выиграли! +100 очков!"
    else:
        result_text = f"{EmojiLose} Не угадали. Выпало число: {random_number} (-10 очков)."
        
    # Показываем итог и актуальный баланс
    text = (
        f"{result_text}\n\n"
        f"{EmojiCoin} Ваш баланс: **{user_scores[user_id]} очков**.\n\n"
        f"Сыграем еще раз? Выберите цифру:"
    )
    
    # Меняем клавиатуру и текст прямо в старом сообщении, чтобы не спамить чат
    reply_markup = build_grid_keyboard()
    await query.message.edit_text(text, reply_markup=reply_markup, parse_mode="Markdown")

def main():
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler('start', start))
    application.add_handler(CallbackQueryHandler(button_click))

    application.add_handler(CommandHandler('start', start))
    application.run_polling()

if __name__ == '__main__':
    main()
