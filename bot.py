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

# Хранение баланса пользователей в ОЗУ (встроенный словарь Python)
user_balances = {}

def get_game_keyboard() -> InlineKeyboardMarkup:
    """Генерирует инлайн-клавиатуру с сеткой чисел 2х5 и кнопками управления."""
    keyboard = []
    row = []
    
    # Строим сетку чисел (2 ряда по 5 кнопок)
    for number in NUMBERS:
        button = InlineKeyboardButton(text=number, callback_data=f"guess_{number}")
        row.append(button)
        if len(row) == 5:
            keyboard.append(row)
            row = []
            
    # Добавляем нижний ряд с кнопками «Баланс» и «Перезапуск»
    control_row = [
        InlineKeyboardButton(text="💰 Баланс", callback_data="action_balance"),
        InlineKeyboardButton(text="🔄 Перезапуск", callback_data="action_restart")
    ]
    keyboard.append(control_row)
            
    return InlineKeyboardMarkup(keyboard)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /start. Инициализирует баланс игрока."""
    user_id = update.effective_user.id
    user_balances[user_id] = START_BALANCE
    
    text = (
        f"🎰 *Добро пожаловать в Рулетку чисел!*\n\n"
        f"{EMOJI_COIN} Ваш стартовый баланс: *{START_BALANCE} очков*.\n"
        f" Стоимость одной игры: *{BET_COST} очков*.\n"
        f" Приз за угаданное число: *{WIN_PRIZE} очков*.\n\n"
        f"Выберите число на панели ниже, чтобы сделать ставку:"
    )
    
    await update.message.reply_text(
        text=text,
        reply_markup=get_game_keyboard(),
        parse_mode="Markdown"
    )

async def game_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик нажатий на инлайн-кнопки (числа и управление)."""
    query = update.callback_query
    user_id = query.from_user.id
    action = query.data
    
    # Убираем анимацию загрузки на кнопке в интерфейсе Telegram
    await query.answer()
    
    # Проверка наличия пользователя в словаре
    if user_id not in user_balances:
        user_balances[user_id] = START_BALANCE

    current_balance = user_balances[user_id]

    # --- СЦЕНАРИЙ 1: Нажата кнопка «🔄 Перезапуск» ---
    if action == "action_restart":
        user_balances[user_id] = START_BALANCE
        restart_text = (
            f"🔄 *Игра перезапущена!*\n\n"
            f"Баланс обновлен до стартовых *{START_BALANCE} очков*.\n"
            f"Выберите число от 0 до 9 для новой ставки:"
        )
        await query.message.edit_text(text=restart_text, reply_markup=get_game_keyboard(), parse_mode="Markdown")
        return

    # --- СЦЕНАРИЙ 2: Нажата кнопка «💰 Баланс» ---
    if action == "action_balance":
        balance_text = (
            f"📊 *Информация о вашем аккаунте*\n\n"
            f"{EMOJI_COIN} Текущий баланс: *{current_balance} очков*.\n"
            f"Стоимость хода: *{BET_COST} очков*.\n\n"
            f"Вы можете продолжить игру, выбрав число ниже:"
        )
        await query.message.edit_text(text=balance_text, reply_markup=get_game_keyboard(), parse_mode="Markdown")
        return

    # --- СЦЕНАРИЙ 3: Нажата кнопка с числом (Игра) ---
    if action.startswith("guess_"):
        # Проверка баланса перед игрой
        if current_balance < BET_COST:
            insufficient_funds_text = (
                f"{EMOJI_ALERT} *Недостаточно очков для игры!*\n\n"
                f"Ваш баланс: *{current_balance} очков*, а для ставки нужно *{BET_COST}*.\n"
                f"Нажмите кнопку *🔄 Перезапуск* ниже, чтобы получить {START_BALANCE} очков!"
            )
            # Оставляем клавиатуру, чтобы пользователь мог нажать «Перезапуск»
            await query.message.edit_text(text=insufficient_funds_text, reply_markup=get_game_keyboard(), parse_mode="Markdown")
            return

        # Списание ставки
        user_balances[user_id] -= BET_COST
        user_guess = action.replace("guess_", "")
        lucky_number = random.choice(NUMBERS)
        
        # Логика выигрыша / проигрыша
        if user_guess == lucky_number:
            user_balances[user_id] += WIN_PRIZE
            result_message = f"{EMOJI_WIN} *Вы выиграли!* Число *{lucky_number}* угадано!"
        else:
            result_message = f"{EMOJI_LOSE} *Не угадали.* Выпало число: *{lucky_number}* (Вы ставили на *{user_guess}*)."
        
        new_balance = user_balances[user_id]
        
        # Текст продолжения игры
        if new_balance >= BET_COST:
            next_step_text = f"\n\n{EMOJI_COIN} Баланс: *{new_balance} очков*.\nСделайте следующую ставку:"
        else:
            next_step_text = (
                f"\n\n{EMOJI_ALERT} *Очки закончились!* Баланс: *{new_balance} очков*.\n"
                f"Вы больше не можете угадывать числа. Нажмите *🔄 Перезапуск* для сброса."
            )
            
        await query.message.edit_text(
            text=f"{result_message}{next_step_text}",
            reply_markup=get_game_keyboard(),
            parse_mode="Markdown"
        )

def main() -> None:
    """Запуск бота."""
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start_command))
    # Обрабатываем все callback-запросы одной функцией
    application.add_handler(CallbackQueryHandler(game_callback_handler))

    logger.info("Бот успешно запущен и готов к игре!")
    application.run_polling()

if __name__ == '__main__':
    main()
