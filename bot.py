import random
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command, Text, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

API_TOKEN = '8787088034:AAEtTxeN-t9CaNKtdlWqBwRinr1CBC-5uHw'  # Замените на токен своего бота

# Инициализация бота и диспетчера
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Создание клавиатуры с кнопками от 0 до 9
keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="0"), KeyboardButton(text="1"), KeyboardButton(text="2")],
        [KeyboardButton(text="3"), KeyboardButton(text="4"), KeyboardButton(text="5")],
        [KeyboardButton(text="6"), KeyboardButton(text="7"), KeyboardButton(text="8"), KeyboardButton(text="9")]
    ],
    resize_keyboard=True
)

# Создание инлайн-клавиатуры с кнопками перезапуска и отображения баланса
inline_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton("Перезапустить", callback_data="restart")],
        [InlineKeyboardButton("Баланс", callback_data="balance")]
    ]
)

# Создание инлайн-клавиатуры с кнопками подтверждения выбора и изменения
confirmation_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton("Подтвердить", callback_data="confirm")],
        [InlineKeyboardButton("Изменить", callback_data="change")]
    ]
)

# Определение состояний FSM
class GameState(StatesGroup):
    waiting_for_number = State()
    waiting_for_confirmation = State()

# Обработчик команды /start или /help
@dp.message(Command("start", "help"))
async def send_welcome(message: types.Message, state: FSMContext):
    await message.reply(
        text="Привет! Добро пожаловать в игру. Выберите число от 0 до 9, чтобы попробовать угадать!\n"
             "Нажмите на кнопку с нужным числом.",
        reply_markup=keyboard
    )
    await state.set_state(GameState.waiting_for_number)

# Обработчик нажатий на кнопки с числами
@dp.message(F.text.in_(['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']))
async def handle_digit(message: types.Message, state: FSMContext):
    user_number = int(message.text)
    await message.reply(
        text=f"Вы выбрали число {user_number}. Подтвердите свой выбор или измените.",
        reply_markup=confirmation_keyboard
    )
    await state.set_state(GameState.waiting_for_confirmation)
    await state.update_data(user_number=user_number)

# Обработчик кнопки подтверждения выбора
@dp.callback_query(F.data == "confirm")
async def handle_confirm(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    user_number = data['user_number']
    bot_number = random.randint(0, 9)

    if user_number == bot_number:
        await callback.message.reply(f"🎉 Поздравляем! Вы угадали число {bot_number}!", reply_markup=inline_keyboard)
    else:
        await callback.message.reply(f"🚫 К сожалению, вы не угадали. Бот выбрал число {bot_number}.", reply_markup=inline_keyboard)
    
    # Сброс состояния после игры
    await state.set_state(GameState.waiting_for_number)

# Обработчик кнопки изменения выбора
@dp.callback_query(F.data == "change")
async def handle_change(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.reply(
        text="Выберите новое число от 0 до 9 для угадайки.",
        reply_markup=keyboard
    )
    # Оставляем состояние без изменения

# Обработчик кнопки перезапуска игры
@dp.callback_query(F.data == "restart")
async def handle_restart(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.reply(
        text="Игра перезапущена! Начальный баланс: 100\n"
             "Выберите число от 0 до 9 для угадайки.",
        reply_markup=keyboard
    )
    # Сброс состояния после игры
    await state.set_state(GameState.waiting_for_number)

# Обработчик кнопки отображения баланса (в данном примере просто отправка сообщения)
@dp.callback_query(F.data == "balance")
async def handle_balance(callback: types.CallbackQuery):
    # Здесь можно добавить логику для отображения баланса пользователя
    await callback.message.reply(
        text="Ваш текущий баланс: 100",
        reply_markup=inline_keyboard
    )

# Запуск бота
if __name__ == "__main__":
    dp.run_polling(bot)
