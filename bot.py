import logging
from typing import Optional
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton # Импортируем Button
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import random
import asyncio

# =======================================================================
# КОНФИГУРАЦИЯ И НАСТРОЙКИ
# =======================================================================

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
# ГЕНЕРАТОР КЛАВИАТУР (КНОПОК)
# =======================================================================

def create_number_grid() -> InlineKeyboardMarkup:
    """Генерирует сетку из 10 кнопок (0-9)."""
    keyboard = []
    for i in range(0, 10, 5):
        row = [KeyboardButton(str(j)) for j in range(i, i + 5)]
        keyboard.append(row)
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def create_action_keyboard() -> InlineKeyboardMarkup:
    """Генерирует универсальную клавиатуру для действий."""
    # Используем callback_data для передачи действия боту при клике
    buttons = [
        [InlineKeyboardButton("🔁 Повторить ход", callback_data="ACTION_PLAY_AGAIN")],
        [InlineKeyboardButton("ℹ️ Правила / Старт", callback_data="COMMAND_START")] 
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# =======================================================================
# УТИЛИТЫ И ОБНОВЛЕНИЕ UI (Основной функционал)
# =======================================================================

async def display_game_status(query: Optional[Update], balance: int, is_playing: bool, initial_message: str) -> str:
    """
    Формирует и отправляет обновленный статус игры в то же сообщение.
    Сохраняет сетку чисел и добавляет универсальные кнопки действий.
    """
    # Проверка контекста: нужно ли редактировать сообщение?
    if query and hasattr(query, 'message') and query.message:
        message = query.message
    else:
        return initial_message 

    balance_markdown = f"💰 Ваш текущий баланс: *{balance}* очков."

    # Логика текста статуса (как и раньше)
    if not is_playing:
        status_text = "🔴 ИГРА ПРЕРВАНА! Ваши очки слишком низкие.\nПожалуйста, используйте /start, чтобы обнулить баланс и начать заново. ✨"
        color_emoji = "🛑"
    else:
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

    # 1. Сборка клавиатуры (Сетка + Действия)
    main_keyboard = create_number_grid() # Основные кнопки
    action_keyboard = create_action_keyboard() # Новые универсальные кнопки
    
    # Комбинирование двух раскладок в одну
    full_markup = InlineKeyboardMarkup(inline_keyboard=list(main_keyboard.inline_keyboard) + action_keyboard.inline_keyboard)


    # 2. Редактирование сообщения
    try:
        await message.edit_text(parse_mode='Markdown', text=new_text, reply_markup=full_markup)
        return new_text
    except Exception as e:
        logger.warning(f"Не удалось отредактировать сообщение (возможно, оно уже устарело или права доступа): {e}")
        # Если редактирование не сработало, мы просто возвращаем текст, а кнопки будут добавлены автоматически при первой отправке.
        return new_text 

# =======================================================================
# ОБРАБИТЕЛИ КОМАНДЫ И СОБЫТИЙ (HANDLERS)
# =======================================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /start. Инициализирует игровое состояние."""
    await update.message.reply_text("🎲 Добро пожаловать в Рулетку с числами! 🎰\nНажмите на число для ставки.", parse_mode='Markdown')

    # Сохранение состояния
    context.chat_data[GAME_STATE_KEY] = {
        'balance': STARTING_BALANCE,
        'is_playing': True,
    }
    user_state = context.chat_data[GAME_STATE_KEY]

    # Отображение первоначального UI (с кнопками)
    await display_game_status(update, user_state['balance'], user_state['is_playing'], "Добро пожаловать в игру!")


async def handle_guess(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает клик по любой кнопке (угадывание числа)."""
    query = update.callback_query

    # 1. Подтверждение нажатия кнопки
    await query.answer() 
    user_state = context.chat_data.get(GAME_STATE_KEY)

    if not user_state or not user_state['is_playing']:
        await query.edit_message_text("❌ Игра неактивна. Пожалуйста, используйте /start, чтобы обнулить баланс и начать заново.")
        return

    # 2. Определяем, это ставка или действие (по callback_data)
    if not hasattr(query.data, '__contains__'): # Простая проверка на то, что данные - число
        try:
            guessed_number = int(query.data)
            is_game_move = True
        except ValueError:
            # Это не ставка, а клик по одной из новых кнопок действий. Игнорируем и выходим.
            return 

    else:
        # Если это действие (ACTION_PLAY_AGAIN или COMMAND_START)
        await query.edit_message_text("Нажмите /start для смены состояния игры.") # Просто уведомляем, что кнопки не работают здесь
        return


    # --- ИГРОВАЯ ЛОГИКА (только если это ставка) ---

    current_balance = user_state['balance']
    
    if current_balance < COST_PER_GUESS:
        await query.edit_message_text("⛔ Недостаточно средств! Ваш баланс ниже стоимости ставки.")
        return

    # Списываем стоимость ставки
    new_balance = current_balance - COST_PER_GUESS
    winning_number = random.randint(0, 9)
    result_text = ""

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

    # Формирование финального сообщения (теперь оно содержит результат + статус)
    final_message_prefix = (
        f"{result_text}\n\n"
        f"===============================\n"
        f"📈 Ваш ход завершен."
    )

    # 4. Обновление UI: показываем результат, а затем - статус баланса и сетку кнопок с действиями
    await display_game_status(query, new_balance, is_still_playing, final_message_prefix)


# =======================================================================
# ГЛАВНАЯ ФУНКЦИЯ ЗАПУСКА
# =======================================================================

def main() -> None:
    """Запуск бота."""
    if TOKEN == 'ВАШ_ТОКЕН':
        print("\n[FATAL ERROR] 🛑 Пожалуйста, замените 'ВАШ_ТОКЕН' на ваш реальный токен в коде.")
        return

    application = Application.builder().token(TOKEN).build()

    # Команды
    application.add_handler(CommandHandler("start", start))
    
    # Обработчики кликов по кнопкам (работает как для чисел, так и для действий)
    application.add_handler(CallbackQueryHandler(handle_guess))

    logger.info("✅ Бот успешно запущен и ожидает пользователей...")
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
