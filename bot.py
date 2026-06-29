import random
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command, Text

API_TOKEN = 'YOUR_BOT_API_TOKEN'  # Замените на токен своего бота

# Инициализация бота и диспетчера
bot = Bot(token=8787088034:AAEtTxeN-t9CaNKtdlWqBwRinr1CBC-5uHw)
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

# Инициализация баланса пользователя (в реальном приложении лучше использовать базу данных)
balance = 100

# Обработчик команды /start или /help
@dp.message(Command("start", "help"))
async def send_welcome(message: types.Message):
    await message.reply(
        text="Привет! Добро пожаловать в игру. Выберите число от 0 до 9, чтобы попробовать угадать!\n"
             "Нажмите на кнопку с нужным числом.",
        reply_markup=keyboard
    )

# Обработчик нажатий на кнопки с числами
@dp.message(Text(lambda text: text.isdigit() and int(text) in range(10)))
async def handle_digit(message: types.Message):
    global selected_number
    user_number = int(message.text)
    selected_number = user_number

    await message.reply(
        text=f"Вы выбрали число {selected_number}. Подтвердите свой выбор или измените.",
        reply_markup=confirmation_keyboard
    )

# Обработчик кнопки подтверждения выбора
@dp.callback_query(Text("confirm"))
async def handle_confirm(callback: types.CallbackQuery):
    global balance
    user_number = selected_number
    bot_number = random.randint(0, 9)

    if user_number == bot_number:
        await callback.message.reply(f"🎉 Поздравляем! Вы угадали число {bot_number}!", reply_markup=inline_keyboard)
        balance += 10  # Увеличиваем баланс на 10
    else:
        await callback.message.reply(f"🚫 К сожалению, вы не угадали. Бот выбрал число {bot_number}.", reply_markup=inline_keyboard)

# Обработчик кнопки изменения выбора
@dp.callback_query(Text("change"))
async def handle_change(callback: types.CallbackQuery):
    await callback.message.reply(
        text="Выберите новое число от 0 до 9 для угадайки.",
        reply_markup=keyboard
    )

# Обработчик кнопки перезапуска игры
@dp.callback_query(Text("restart"))
async def handle_restart(callback: types.CallbackQuery):
    global balance, selected_number
    balance = 100  # Сброс баланса при новой игре
    selected_number = None
    await callback.message.reply(
        text="Игра перезапущена! Начальный баланс: 100\n"
             "Выберите число от 0 до 9 для угадайки.",
        reply_markup=keyboard
    )

# Обработчик кнопки отображения баланса
@dp.callback_query(Text("balance"))
async def handle_balance(callback: types.CallbackQuery):
    await callback.message.reply(
        text=f"Ваш текущий баланс: {balance}",
        reply_markup=inline_keyboard
    )

# Запуск бота
if __name__ == "__main__":
    dp.run_polling(bot)
