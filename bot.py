import logging
from typing import Optional
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton 
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import random
import asyncio

# =======================================================================
# КОНФИГУРАЦИЯ И НАСТРОЙКИ
# =======================================================================

# !!! ОЧЕНЬ ВАЖНО: Замените 'ВАШ_ТОКЕН' на ваш реальный токен !!!
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
MIN_BALANCE_TO_PLAY = COST_PER_GUESS

GAME_STATE_KEY = 'user_state'

# =======================================================================
# ГЕНЕРАТОР КЛАВИАТУР (UI)
# =======================================================================

def create_number_grid() -> InlineKeyboardMarkup:
    """Генерирует сетку из 10 кнопок (0-9). Каждая кнопка должна передавать свое число как данные."""
    keyboard = []
    for i in range(0, 10, 5):
        # Мы используем str(j) как callback_data, чтобы бот мог это распознать.
        row = [InlineKeyboardButton(str(j), callback_data=str(j)) for j in range(i, i + 5)]
        keyboard.append(row)
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def create_action_keyboard() -> InlineKeyboardMarkup:
    """Генерирует универсальную клавиатуру для действий (Повторить / Старт)."""
    buttons = [
        # callback_data должен быть уникальным идентификатором действия.
        [InlineKeyboardButton("🔁 Повторить ход", callback_data="ACTION_PLAY_AGAIN")],
        [InlineKeyboardButton("ℹ️ Правила / Обнулить баланс (Начать заново)", callback_data="COMMAND_START")] 
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# =======================================================================
# УТИЛИТЫ И ОБНОВЛЕНИЕ UI
# =======================================================================

async def display_game_status(query: Optional[Update], balance: int, is_playing: bool, initial_message: str) -> None:
    """
    Формирует и редактирует статус игры в исходное сообщение.
    Принимает query для доступа к message.
    """
    # Если это не CallbackQuery (т.е. при первом сообщении), просто отправляем текст.
    if not query or not hasattr(query, 'message') or not query.message:
        await query.message.reply_text(initial_message, parse_mode='Markdown', reply_markup=create_number_grid())
        return

    # Получаем сообщение, которое нужно отредактировать
    message = query.message

    balance_markdown = f"💰 Ваш текущий баланс: *{balance}* очков."

    # Логика текста статуса 
    if not is_playing:
        status_text = (
            f"🔴 *ИГРА ПРЕРВАНА!* Ваши очки слишком низкие ({balance}).\n"
            "Пожалуйста, используйте /start, чтобы обнулить баланс и начать заново. ✨"
        )
    elif balance < MIN_BALANCE_TO_PLAY:
        status_text = (
            f"⚠️ Пожалуйста, ждите пополнения! Минимальная стоимость ставки — {COST_PER_GUESS} очков.\n"
            f"Ваш текущий баланс ({balance}) слишком мал для продолжения игры."
        )
    else:
        status_text = (
            f"✨ Готовы сделать ставку? Введите число от 0 до 9. Удачи! 🍀\n*{color_emoji}* {balance_markdown}"
        ).format(color_emoji="🌟")

    # Формирование финального текста сообщения
    new_text = (
        f"╔═════════════════════════╗\n"
        f"🎲 *Рулетка с числами*\n"
        f"╚═════════════════════════╝\n\n"
        f"{status_text}\n\n"
    )

    # 1. Сборка клавиатуры (Сетка + Действия)
    main_keyboard = create_number_grid() # Основные кнопки
    action_keyboard = create_action_keyboard() # Новые универсальные кнопки
    
    # Комбинирование двух раскладок в одну
    full_markup = InlineKeyboardMarkup(inline_keyboard=list(main_keyboard.inline_keyboard) + action_keyboard.inline_keyboard)

    # 2. Редактирование сообщения (Самый важный шаг UI)
    try:
        await message.edit_text(parse_mode='Markdown', text=new_text, reply_markup=full_markup)
    except Exception as e:
        logger.warning(f"Не удалось отредактировать сообщение (возможно, оно устарело): {e}")


# =======================================================================
# ОБРАБИТЕЛИ КОМАНДЫ И СОБЫТИЙ (HANDLERS)
# =======================================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /start. Инициализирует игровое состояние."""
    await update.message.reply_text("🎲 Добро пожаловать в Рулетку с числами! 🎰\nНажмите на число для ставки.", parse_mode='Markdown')

    # Сохранение состояния (если пользователь уже играл, мы его обнуляем)
    context.chat_data[GAME_STATE_KEY] = {
        'balance': STARTING_BALANCE,
        'is_playing': True,
    }
    user_state = context.chat_data[GAME_STATE_KEY]

    # Отображение первоначального UI (с кнопками)
    await display_game_status(update, user_state['balance'], user_state['is_playing'], "Начинайте игру! Выберите число от 0 до 9.")


async def handle_guess(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает клик по любой кнопке (угадывание числа или действие)."""
    query = update.callback_query

    # 1. Подтверждение нажатия кнопки, чтобы убрать "загрузку" индикатор
    await query.answer() 
    user_state = context.chat_data.get(GAME_STATE_KEY)
    if not user_state:
        await query.edit_message_text("⚠️ Кажется, ваше игровое состояние потеряно. Пожалуйста, используйте /start.")
        return

    # 2. Проверка, является ли нажатая кнопка чистой ставкой (число от 0 до 9)
    try:
        # Получаем data из кнопки и пытаемся преобразовать в число
        guessed_number = int(query.data)
        if not (0 <= guessed_number <= 9):
             raise ValueError("Число вне диапазона.") # Защита, если что-то пошло не так

    except ValueError:
        # Если преобразование в INT не удалось или число вне диапазона, это НЕ ставка.
        # Это может быть клик по кнопке действия ("Повторить ход") или другой элемент UI.
        await query.edit_message_text(
            "🛠️ Вы нажали кнопку действия. Пожалуйста, дождитесь результатов хода и затем нажмите 'Повторить ход' или /start."
        )
        return # Прекращаем выполнение функции, так как это не ставка

    # --- ЭТОТ БЛОК ВЫПОЛНЯЕТСЯ ТОЛЬКО ПРИ УСПЕШНОЙ СТАВКЕ (0-9) ---

    current_balance = user_state['balance']
    
    # 3. Проверка баланса перед ставкой
    if current_balance < COST_PER_GUESS:
        await query.edit_message_text("⛔ Недостаточно средств! Ваш баланс ниже стоимости ставки.")
        return

    # Списываем стоимость ставки
    new_balance = current_balance - COST_PER_GUESS
    winning_number = random.randint(0, 9)
    result_text: str = ""

    # 4. Игровая логика (угадывание vs выигрышный номер)
    if guessed_number == winning_number:
        new_balance += WIN_PAYOUT
        result_text = (
            f"🎉 *ПОБЕДА!* 🎉\n"
            f"🌟 Ваше число `{guessed_number}` совпало с выигрышным номером {winning_number}!\n"
            f"Вы выиграли {WIN_PAYOUT} очков!"
        )
    else:
        result_text = (
            f"😔 *ПОРАЖЕНИЕ...* 💔\n"
            f"😢 Вы выбрали `{guessed_number}`, но выигрышное число было {winning_number}."
        )

    # Обновление состояния пользователя
    user_state['balance'] = new_balance

    is_still_playing = user_state['balance'] >= COST_PER_GUESS and user_state['balance'] > 0
    user_state['is_playing'] = is_still_playing

    # 5. Обновление UI: показываем результат, а затем - статус баланса и сетку кнопок с действиями
    final_message_prefix = (
        f"{result_text}\n\n"
        f"===============================\n"
        f"📈 Ваш ход завершен."
    )

    await display_game_status(query, new_balance, is_still_playing, final_message_prefix)


# =======================================================================
# ГЛАВНАЯ ФУНКЦИЯ ЗАПУСКА
# =======================================================================

def main() -> None:
    """Запуск бота."""
    if TOKEN == 'ВАШ_ТОКЕН':
        print("\n[FATAL ERROR] 🛑 Пожалуйста, замените 'ВАШ_ТОКЕН' на ваш реальный токен в коде.")
        return

    # Создание Application Builder
    application = Application.builder().token(TOKEN).build()

    # Регистрация обработчиков:
    # Команда /start (для начала или сброса игры)
    application.add_handler(CommandHandler("start", start))

    # Обработчик кликов по кнопкам (Обрабатывает как числа 0-9, так и кнопки действий)
    application.add_handler(CallbackQueryHandler(handle_guess))

    logger.info("✅ Бот успешно запущен и ожидает пользователей...")
    
    # Запуск бота
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
