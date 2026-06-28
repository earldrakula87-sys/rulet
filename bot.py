import logging
from telegram import Update, InlineKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes
import random
import asyncio

# =======================================================================
# КОНФИГУРАЦИЯ И НАСТРОЙКИ
# =======================================================================

# !!! ЗАМЕНИТЕ 'ВАШ_ТОКЕН' на реальный токен вашего бота !!!
TOKEN = '8787088034:AAEtTxeN-t9CaNKtdlWqBwRinr1CBC-5uHw' 

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Игровые константы
STARTING_BALANCE = 100
COST_PER_GUESS = 10
WIN_PAYOUT = 100
MIN_BALANCE_TO_PLAY = COST_PER_GUESS # Мы можем сделать ставку, только если баланс >= 10

# Словарь для хранения состояний пользователей (используем chat_data контекста)
GAME_STATE_KEY = 'user_state'

# =======================================================================
# ГЕНЕРАТОР ИНЛАЙН-КНОПОК
# =======================================================================

def create_number_grid() -> InlineKeyboardMarkup:
    """Генерирует сетку из 10 кнопок (0-9) для выбора числа."""
    keyboard = []
    # Создаем 2 ряда по 5 кнопок
    for i in range(0, 10, 5):
        row = [KeyboardButton(str(j)) for j in range(i, i + 5)]
        keyboard.append(row)
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

# =======================================================================
# УТИЛИТЫ И ОБНОВЛЕНИЕ UI (Основной функционал)
# =======================================================================

async def display_game_status(query: Update.None, balance: int, is_playing: bool, current_message: str) -> str:
    """
    Формирует и отправляет обновленный статус игры в то же сообщение.
    Этот метод предотвращает спам сообщений.
    """
    if query and query.message:
        # Получаем объект сообщения, чтобы его отредактировать
        message = query.message
    else:
        # Если вызывается из функции, не связанной с Query (например, первый запуск)
        return current_message

    # Оформление баланса Markdown
    balance_markdown = f"💰 Ваш текущий баланс: *{balance}* очков."

    if not is_playing:
        status_text = "🔴 ИГРА ПРЕРВАНА! Ваши очки слишком низкие.\nПожалуйста, используйте /start, чтобы обнулить баланс и начать заново. ✨"
        color_emoji = "🛑"
    else:
        # Проверка на минимальные средства для ставки
        if balance < MIN_BALANCE_TO_PLAY:
            status_text = f"⚠️ Пожалуйста, ждите пополнения! Минимальная стоимость ставки — {COST_PER_GUESS} очков.\nВаш текущий баланс ({balance}) слишком мал для продолжения игры."
            color_emoji = "🟡"
        else:
            status_text = f"✨ Готовы сделать ставку? Введите число от 0 до 9. Удачи! 🍀\n*{color_emoji}* {balance_markdown}"

    # Формирование финального текста сообщения
    new_text = (
        f"╔═════════════════════════╗\n"
        f"💰 *Рулетка с числами*\n"
        f"╚═════════════════════════╝\n\n"
        f"{status_text}\n\n"
    )

    # Редактирование сообщения, чтобы обновить статус без спама
    try:
        await message.edit_text(parse_mode='Markdown', text=new_text)
        return new_text # Возвращаем текст для отладки/документирования
    except Exception as e:
        logger.warning(f"Не удалось отредактировать сообщение (возможно, оно уже устарело): {e}")
        # В случае ошибки редактирования, просто возвращаем сформированный текст
        return new_text


# =======================================================================
# ОБРАБИТЕЛИ КОМАНДЫ И СОБЫТИЙ
# =======================================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /start. Инициализирует игровое состояние."""
    await update.message.reply_text("Добро пожаловать в Рулетку с числами! 🎰", parse_mode='Markdown')

    # 1. Установка начального состояния пользователя
    context.chat_data[GAME_STATE_KEY] = {
        'balance': STARTING_BALANCE,
        'is_playing': True,
    }
    user_state = context.chat_data[GAME_STATE_KEY]

    # 2. Отображение первоначального UI
    await display_game_status(update, user_state['balance'], user_state['is_playing'])


async def handle_guess(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает клик по любой кнопке (угадывание числа)."""
    query = update.callback_query

    # 1. Предотвращает зависание кнопок
    await query.answer() 
    user_state = context.chat_data.get(GAME_STATE_KEY)

    if not user_state or not user_state['is_playing']:
        await query.edit_message_text("❌ Игра неактивна. Пожалуйста, начните с команды /start.")
        return

    # 2. Получаем введенное число (из текста нажатой кнопки)
    guessed_number_str = query.data
    try:
        guessed_number = int(guessed_number_str)
    except ValueError:
        await query.edit_message_text("❌ Пожалуйста, выберите корректное число.")
        return

    current_balance = user_state['balance']
    
    # 3. Проверка возможности ставки (Валидация состояния)
    if current_balance < COST_PER_GUESS:
        await query.edit_message_text("⛔ Недостаточно средств! Ваш баланс ниже стоимости ставки.")
        return

    # --- ИГРОВАЯ ЛОГИКА ---
    
    # Списываем стоимость ставки
    new_balance = current_balance - COST_PER_GUESS
    
    # Генерируем случайный выигрышный номер
    winning_number = random.randint(0, 9)

    # Проверка результата
    if guessed_number == winning_number:
        # Выигрыш!
        new_balance += WIN_PAYOUT
        result_text = (
            f"🎉 *ПОБЕДА!* 🎉\n"
            f"🌟 Ваше число `{guessed_number}` совпало с выигрышным номером {winning_number}!\n"
            f"Вы выиграли {WIN_PAYOUT} очков!"
        )
    else:
        # Проигрыш!
        result_text = (
            f"😔 *ПОРАЖЕНИЕ...* 💔\n"
            f"😢 Вы выбрали `{guessed_number}`, но выигрышное число было {winning_number}."
        )

    # Обновляем состояние пользователя
    user_state['balance'] = new_balance

    # 4. Проверка конца игры после хода
    is_still_playing = user_state['balance'] >= COST_PER_GUESS and user_state['balance'] > 0
    user_state['is_playing'] = is_still_playing

    # Формирование финального сообщения и редактирование UI
    final_message = (
        f"{result_text}\n\n"
        f"===============================\n"
        f"{' ' * 2}Ваш ход завершен. Статус обновлен ниже."
    )

    # Обновление баланса и статуса в одном сообщении
    await display_game_status(query, new_balance, is_still_playing)


# =======================================================================
# ГЛАВНАЯ ФУНКЦИЯ ЗАПУСКА
# =======================================================================

def main() -> None:
    """Запуск бота."""
    if TOKEN == '8787088034:AAEtTxeN-t9CaNKtdlWqBwRinr1CBC-5uHw':
        print("\n[ERROR] Пожалуйста, замените 'ВАШ_ТОКЕН' на ваш реальный токен в коде.")
        return

    # Создание Application Builder
    application = Application.builder().token(TOKEN).build()

    # Регистрируем обработчики:
    # 1. Команда /start
    application.add_handler(CommandHandler("start", start))

    # 2. Обработчик кнопок (CallbackQueryHandler) для всех кликов по сетке
    # Мы обрабатываем все сообщения, которые приходят от нажатия инлайн-кнопки.
    application.add_handler(CallbackQueryHandler(handle_guess))

    logger.info("Бот запущен и ожидает пользователей...")
    
    # Запуск бота (блокирующий вызов)
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
