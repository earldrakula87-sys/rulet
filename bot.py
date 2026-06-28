import random
import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# Укажите здесь токен вашего бота, полученный от @BotFather
TOKEN = '8787088034:AAEtTxeN-t9CaNKtdlWqBwRinr1CBC-5uHw'

# Настройка стандартного логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Константы игры
START_BALANCE = 100
BET_COST = 10
WIN_PRIZE = 100
NUMBERS = [str(i) for i in range(10)]

# Визуальное оформление (эмодзи)
EMOJI_COIN = '🪙'
EMOJI_WIN = '🎉'
EMOJI_LOSE = '❌'
EMOJI_ALERT = '⚠️'

# Временная база данных в оперативной памяти (dict) для хранения баланса пользователей
# В реальном проекте здесь лучше использовать SQLite или PostgreSQL
user_balances = {}

def get_grid_keyboard() -> InlineKeyboardMarkup:
    """Генерирует инлайн-клавиатуру с числами от 0 до 9 в виде сетки 2 ряда по 5 кнопок."""
    keyboard = []
    row = []
    
    for number in NUMBERS:
        button = InlineKeyboardButton(text=number, callback_data=f"guess_{number}")
        row.append(button)
        # Как только набралось 5 кнопок, добавляем ряд в клавиатуру и очищаем список для следующего ряда
        if len(row) == 5:
            keyboard.append(row)
            row = []
            
    return InlineKeyboardMarkup(keyboard)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /start. Инициализирует или сбрасывает баланс."""
    user_id = update.effective_user.id
    
    # Выдаем или обновляем баланс до стартовых 100 очков
    user_balances[user_id] = START_BALANCE
    
    text = (
        f"🎰 *Добро пожаловать в Рулетку чисел!*\n\n"
        f"{EMOJI_COIN} Ваш стартовый баланс: *{START_BALANCE} очков*.\n"
        f" Стоимость одной игры: *{BET_COST} очков*.\n"
        f" Приз за угаданное число: *{WIN_PRIZE} очков*.\n\n"
        f"Угадайте, какое число от 0 до 9 выпадет. Сделайте вашу ставку:"
    )
    
    await update.message.reply_text(
        text=text,
        reply_markup=get_grid_keyboard(),
        parse_mode="Markdown"
    )

async def game_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик нажатий на инлайн-кнопки с числами."""
    query = update.callback_query
    user_id = query.from_user.id
    
    # Обязательно отвечаем на callback-запрос сразу, чтобы кнопка не «зависала» в режиме загрузки
    await query.answer()
    
    # Проверяем, есть ли пользователь в нашей базе данных (на случай перезапуска бота)
    if user_id not in user_balances:
        user_balances[user_id] = START_BALANCE

    current_balance = user_balances[user_id]
    
    # Проверка баланса: хватает ли очков на совершение ставки
    if current_balance < BET_COST:
        insufficient_funds_text = (
            f"{EMOJI_ALERT} *Игра остановлена!*\n\n"
            f"У вас осталось всего *{current_balance} очков*, а для ставки требуется *{BET_COST}*.\n"
            f"Используйте команду /start, чтобы обнулиться и получить снова {START_BALANCE} очков!"
        )
        await query.message.edit_text(text=insufficient_funds_text, parse_mode="Markdown")
        return

    # Списываем стоимость ставки из баланса игрока
    user_balances[user_id] -= BET_COST
    
    # Извлекаем выбранное пользователем число из callback_data (удаляем префикс 'guess_')
    user_guess = query.data.replace("guess_", "")
    
    # Генерируем случайное выигрышное число
    lucky_number = random.choice(NUMBERS)
    
    # Проверяем результат игры
    if user_guess == lucky_number:
        user_balances[user_id] += WIN_PRIZE
        result_message = f"{EMOJI_WIN} *Вы выиграли!* Вы угадали число *{lucky_number}*!"
    else:
        result_message = f"{EMOJI_LOSE} *Не угадали.* Загадано число: *{lucky_number}*. Вы выбрали: *{user_guess}*."
    
    new_balance = user_balances[user_id]
    
    # Формируем текст обновления в зависимости от остатка очков
    if new_balance >= BET_COST:
        next_step_text = f"\n\n{EMOJI_COIN} Ваш текущий баланс: *{new_balance} очков*.\nХотите сыграть еще раз? Выберите число:"
        reply_markup = get_grid_keyboard()
    else:
        next_step_text = (
            f"\n\n{EMOJI_ALERT} *Очки закончились!* Ваш баланс: *{new_balance} очков*.\n"
            f"Вы больше не можете делать ставки. Введите /start для перезапуска игры."
        )
        reply_markup = None  # Скрываем кнопки, так как играть дальше нельзя
        
    # Редактируем старое сообщение, предотвращая спам в чате
    await query.message.edit_text(
        text=f"{result_message}{next_step_text}",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

def main() -> None:
    """Запуск бота."""
    # Инициализация приложения через современный паттерн Builder
    application = Application.builder().token(TOKEN).build()

    # Регистрация обработчиков команд и нажатий кнопок
    application.add_handler(CommandHandler("start", start_command))
    # Фильтруем callback_data по префиксу 'guess_', чтобы обрабатывать только игровые кнопки
    application.add_handler(CallbackQueryHandler(game_callback_handler, pattern="^guess_"))

    # Запуск цикла получения обновлений (блокирующий метод, asyncio под капотом)
    logger.info("Бот успешно запущен и готов к игре!")
    application.run_polling()

if __name__ == '__main__':
    main()
