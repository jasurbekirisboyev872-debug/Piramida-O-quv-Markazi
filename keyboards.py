from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)


# =========================================================
# SUBJECT ICONS
# =========================================================

def get_subject_icon(name: str) -> str:
    n = name.lower()
    if "ona tili" in n:
        return "🇺🇿"
    elif "rus tili" in n:
        return "🇷🇺"
    elif "ingliz" in n:
        return "🇬🇧"
    elif "matematika" in n:
        return "📐"
    elif "kimyo" in n:
        return "🧪"
    elif "biologiya" in n:
        return "🧬"
    elif "fizika" in n:
        return "⚡"
    elif "tarix" in n or "tarih" in n:
        return "🏛️"
    elif "huquq" in n:
        return "⚖️"
    elif "informatika" in n or "it" in n or "dasturlash" in n:
        return "💻"
    elif "geografiya" in n:
        return "🌍"
    elif "adabiyot" in n:
        return "📜"
    elif "mantiq" in n:
        return "🧠"
    return "📚"


# =========================================================
# USER MENU
# =========================================================

from database import get_cached_subjects

def main_menu(subjects=None):

    if not subjects:
        subjects = get_cached_subjects()

    keyboard = []

    # Barcha fanlarni menyuda 2 tadan qilib joylashtirish
    if subjects:
        row = []
        for subject in subjects:
            name = subject[1]
            icon = get_subject_icon(name)
            row.append(KeyboardButton(text=f"{icon} {name}"))
            if len(row) == 2:
                keyboard.append(row)
                row = []
        if row:
            keyboard.append(row)

    # Asosiy bo'limlar
    keyboard.append([
        KeyboardButton(text="🕐 Dars jadvali"),
        KeyboardButton(text="👨‍🏫 O'qituvchilar")
    ])
    keyboard.append([
        KeyboardButton(text="📍 Manzil"),
        KeyboardButton(text="📞 Bog'lanish")
    ])
    keyboard.append([
        KeyboardButton(text="ℹ️ Markaz haqida"),
        KeyboardButton(text="👑 Admin panel")
    ])

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True
    )


# =========================================================
# CANCEL KEYBOARD
# =========================================================

def cancel_keyboard():

    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="❌ Bekor qilish")]
        ],
        resize_keyboard=True
    )


# =========================================================
# MAP INLINE KEYBOARD
# =========================================================

def map_inline_keyboard(url):

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🗺 Google Maps'da ochish",
                    url=url
                )
            ]
        ]
    )


# =========================================================
# CONTACT INLINE KEYBOARD
# =========================================================

def contact_inline_keyboard(phone="+998-97-162-84-00", username="Isroilova_Ozoda"):

    clean_user = username.replace("@", "").strip() if username else "Isroilova_Ozoda"

    buttons = [
        [
            InlineKeyboardButton(
                text="✈️ Admin bilan bog'lanish",
                url=f"https://t.me/{clean_user}"
            )
        ]
    ]

    return InlineKeyboardMarkup(
        inline_keyboard=buttons
    )


def subject_detail_keyboard(phone="+998-97-162-84-00", username="Isroilova_Ozoda"):

    clean_user = username.replace("@", "").strip() if username else "Isroilova_Ozoda"

    buttons = [
        [
            InlineKeyboardButton(
                text="✈️ Kursga yozilish (Admin)",
                url=f"https://t.me/{clean_user}"
            )
        ]
    ]

    return InlineKeyboardMarkup(
        inline_keyboard=buttons
    )


# =========================================================
# ADMIN MENU
# =========================================================

def admin_menu():

    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="📊 Statistika"),
                KeyboardButton(text="📚 Fanlarni boshqarish")
            ],
            [
                KeyboardButton(text="➕ Fan qo'shish"),
                KeyboardButton(text="📢 Xabar yuborish")
            ],
            [
                KeyboardButton(text="📚 ⚙️ Sozlamalar")
            ],
            [
                KeyboardButton(text="⬅️ Asosiy menyu"),
                KeyboardButton(text="🚪 Chiqish")
            ]
        ],
        resize_keyboard=True
    )


# =========================================================
# SUBJECTS
# =========================================================

def subjects_keyboard(subjects):

    buttons = []

    for subject in subjects:

        subject_id = subject[0]
        name = subject[1]
        icon = get_subject_icon(name)

        buttons.append([
            InlineKeyboardButton(
                text=f"{icon} {name}",
                callback_data=f"subject:{subject_id}"
            )
        ])

    return InlineKeyboardMarkup(
        inline_keyboard=buttons
    )


def admin_subjects_keyboard(subjects):

    buttons = []

    for subject in subjects:

        subject_id = subject[0]
        name = subject[1]
        icon = get_subject_icon(name)

        buttons.append([
            InlineKeyboardButton(
                text=f"{icon} ✏️ {name}",
                callback_data=f"edit:{subject_id}"
            ),
            InlineKeyboardButton(
                text="🗑",
                callback_data=f"delete:{subject_id}"
            )
        ])

    return InlineKeyboardMarkup(
        inline_keyboard=buttons
    )


# =========================================================
# SETTINGS
# =========================================================

def settings_keyboard():

    return InlineKeyboardMarkup(
        inline_keyboard=[

            [
                InlineKeyboardButton(
                    text="🏫 Markaz nomi",
                    callback_data="setting:center_name"
                )
            ],

            [
                InlineKeyboardButton(
                    text="📍 Manzil",
                    callback_data="setting:address"
                )
            ],

            [
                InlineKeyboardButton(
                    text="🗺 Xarita linki",
                    callback_data="setting:map_url"
                )
            ],

            [
                InlineKeyboardButton(
                    text="📞 Telefon",
                    callback_data="setting:phone"
                )
            ],

            [
                InlineKeyboardButton(
                    text="👩‍💼 Admin ismi",
                    callback_data="setting:admin_name"
                )
            ],

            [
                InlineKeyboardButton(
                    text="✈️ Admin Telegram",
                    callback_data="setting:admin_username"
                )
            ],

            [
                InlineKeyboardButton(
                    text="ℹ️ Markaz haqida",
                    callback_data="setting:description"
                )
            ]
        ]
    )