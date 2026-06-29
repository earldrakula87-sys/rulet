import random
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

API_TOKEN = '8787088034:AAEtTxeN-t9CaNKtdlWqBwRinr1CBC-5uHw'  # Замените на токен своего бота

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Инициализация бота и диспетчера
bot = Bot(token=API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Состояния игры
class States(StatesGroup):
    waiting_for_number = State()
    waiting_for_confirmation = State()

# Игровая сессия (в оперативной памяти)
class PlayerProfile:
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.balance = 100
        self.guess_count = 0
        self.won_games = 0

profiles = {}

def get_profile(user_id: int) -> PlayerProfile:
    if user_id not in profiles:
        profiles[user_id] = PlayerProfile(user_id)
    return profiles[user_id]

def get_rank(balance: int) -> str:
    if balance < 50:
        return "Новичок ⚙️"
    elif balance >= 50 and balance < 200:
        return "Хакер 🧠"
    else:
        return "Кибер-Аристократ 👑"

# Главное Reply-меню ввода цифр
def get_digits_keyboard():
    return types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text=str(i)) for i in range(0, 3)],
            [types.KeyboardButton(text=str(i)) for i in range(3, 6)],
            [types.KeyboardButton(text=str(i)) for i in range(6, 9)],
            [types.KeyboardButton(text='9')]
        ],
        resize_keyboard=True
    )

# Команда /start
@dp.message(CommandStart())
async def send_welcome(message: Message, state: FSMContext) -> None:
    profile = get_profile(message.from_user.id)
    await state.set_state(States.waiting_for_number)
    
    await message.reply(
        "⚡ <b>Добро пожаловать в Кибер-Угадайку: Числа Судьбы!</b> ⚡\n"
        "──────────────────────\n"
        "🤖 Система инициализирована.\n"
        f"💎 Ваш баланс: <code>{profile.balance}</code> кристаллов.\n"
        f"🏆 Ваш ранг: <b>{get_rank(profile.balance)}</b>\n"
        "──────────────────────\n"
        "🎲 Выберите число от 0 до 9 на клавиатуре ниже:",
        parse_mode="HTML",
        reply_markup=get_digits_keyboard()
    )

# Обработка нажатия на цифру (только в состоянии waiting_for_number)
@dp.message(States.waiting_for_number, F.text.in_([str(i) for i in range(10)]))
async def handle_number_selection(message: Message, state: FSMContext) -> None:
    number = int(message.text)
    profile = get_profile(message.from_user.id)
    
    if profile.balance < 10:
        await message.reply(
            "⚠️ <b>Доступ заблокирован!</b>\n"
            "Недостаточно средств для генерации попытки. Требуется: 10 💎\n"
            f"Ваш текущий баланс: {profile.balance} 💎\n"
            "Используйте команду /start для сброса или дождитесь бонуса.",
            parse_mode="HTML"
        )
        return

    await state.update_data(selected_number=number)
    await state.set_state(States.waiting_for_confirmation)
    
    confirmation_keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text='Подтвердить выбор ⚡', callback_data='confirm_choice')],
            [types.InlineKeyboardButton(text='Изменить число 🔄', callback_data='change_number')]
        ]
    )
    
    await message.reply(
        f"🤖 Вы зафиксировали матрицу на числе: <b>{number}</b>\n"
        "──────────────────────\n"
        "💸 Стоимость генерации раунда: <code>10</code> 💎\n"
        "Вы готовы запустить квантовое сканирование?",
        parse_mode="HTML",
        reply_markup=confirmation_keyboard
    )

# Обработка инлайн-кнопки "Изменить число 🔄"
@dp.callback_query(States.waiting_for_confirmation, F.data == 'change_number')
async def handle_change_number(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(States.waiting_for_number)
    await callback.message.edit_text(
        "🔄 Квантовый откат выполнен.\n"
        "Матрица сброшена. Пожалуйста, выберите новое число от 0 до 9 на клавиатуре ниже:",
        parse_mode="HTML"
    )
    await callback.answer()

# Обработка инлайн-кнопки "Подтвердить выбор ⚡"
@dp.callback_query(States.waiting_for_confirmation, F.data == 'confirm_choice')
async def handle_confirm_choice(callback: CallbackQuery, state: FSMContext) -> None:
    profile = get_profile(callback.from_user.id)
    
    # Списание ставки
    if profile.balance < 10:
        await callback.message.edit_text("⚠️ Недостаточно средств для подтверждения раунда! Ставка: 10 💎")
        await state.set_state(States.waiting_for_number)
        await callback.answer()
        return
        
    profile.balance -= 10
    profile.guess_count += 1
    
    data = await state.get_data()
    selected_number = data.get('selected_number')
    
    # Честный рандом от 0 до 9 вместо деления ID
    bot_number = random.randint(0, 9)

    inline_keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text="Мой Профиль 📊", callback_data='view_profile')],
            [types.InlineKeyboardButton(text="Сыграть еще раз 🎮", callback_data='play_again')]
        ]
    )

    if selected_number == bot_number:
        profile.balance += 50
        profile.won_games += 1
        await callback.message.edit_text(
            f"🎉 <b>ПОЗДРАВЛЯЕМ! Квантовое совпадение!</b> 🎉\n"
            f"──────────────────────\n"
            f"🤖 Бот загадал число: <code>{bot_number}</code>\n"
            f"🔮 Ваша интуиция: <code>{selected_number}</code>\n"
            f"──────────────────────\n"
            f"💎 <b>Ваша награда: +50 Кибер-Кристаллов!</b>\n"
            f"🏆 Ваш текущий ранг: <i>{get_rank(profile.balance)}</i>",
            parse_mode="HTML",
            reply_markup=inline_keyboard
        )
    else:
        await callback.message.edit_text(
            f"🚫 <b>Квантовый разрыв! Числа не совпали.</b>\n"
            f"──────────────────────\n"
            f"🤖 Бот загадал число: <code>{bot_number}</code>\n"
            f"❌ Ваш выбор: <code>{selected_number}</code>\n"
            f"──────────────────────\n"
            f"💸 Списано за попытку: -10 💎\n"
            f"💰 Текущий баланс: <code>{profile.balance}</code> 💎\n"
            f"🏆 Ваш текущий ранг: <i>{get_rank(profile.balance)}</i>",
            parse_mode="HTML",
            reply_markup=inline_keyboard
        )

    await state.set_state(States.waiting_for_number)
    await callback.answer()

# Просмотр профиля игрока через инлайн-меню
@dp.callback_query(F.data == 'view_profile')
async def handle_view_profile(callback: CallbackQuery, state: FSMContext):
    profile = get_profile(callback.from_user.id)
    
    inline_keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text="Сыграть еще раз 🎮", callback_data='play_again')]
        ]
    )
    
    await callback.message.edit_text(
        text=f"📊 <b>ВАШ ЦИФРОВОЙ ПРОФИЛЬ:</b>\n"
             f"──────────────────────\n"
             f"💎 Баланс кристаллов: <code>{profile.balance}</code>\n"
             f"🎲 Всего симуляций: <code>{profile.guess_count}</code>\n"
             f"🏆 Успешных взломов: <code>{profile.won_games}</code>\n"
             f"──────────────────────\n"
             f"🎖️ Текущий Ранг: <b>{get_rank(profile.balance)}</b>",
        parse_mode="HTML",
        reply_markup=inline_keyboard
    )
    await callback.answer()

# Кнопка быстрой перезагрузки игры / сыграть еще раз
@dp.callback_query(F.data == 'play_again')
async def handle_play_again(callback: CallbackQuery, state: FSMContext) -> None:
    profile = get_profile(callback.from_user.id)
    await state.set_state(States.waiting_for_number)
    
    await callback.message.answer(
        "🎮 <b>Новый раунд активирован!</b>\n"
        f"Ваш баланс: <code>{profile.balance}</code> 💎. Выберите новое число:",
        parse_mode="HTML",
        reply_markup=get_digits_keyboard()
    )
    await callback.answer()

if __name__ == '__main__':
    dp.run_polling(bot)
