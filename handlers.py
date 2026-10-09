import os
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.filters import CommandStart, Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from config import ADMIN_ID, ADMIN_PASSWORD

from database import (
    add_user,
    get_users_count,
    get_active_users,
    get_today_users,
    get_subjects,
    get_subject,
    add_subject,
    update_subject,
    delete_subject,
    get_all_user_ids,
    get_setting,
    set_setting
)

from keyboards import (
    main_menu,
    admin_menu,
    subjects_keyboard,
    admin_subjects_keyboard,
    settings_keyboard,
    cancel_keyboard,
    map_inline_keyboard,
    get_subject_icon,
    contact_inline_keyboard,
    subject_detail_keyboard
)


router = Router()


# =========================================================
# ADMIN CHECK & AUTHENTICATION
# =========================================================

# Parol kiritib tasdiqlangan adminlar ID lari
authenticated_admins = set()

def is_admin(user_id):
    return user_id in authenticated_admins


# =========================================================
# FSM STATES
# =========================================================

class AdminLoginState(StatesGroup):
    password = State()


class AddSubjectState(StatesGroup):

    name = State()
    teacher = State()
    days = State()
    time = State()
    price = State()
    small_group = State()


class EditSubjectState(StatesGroup):

    name = State()
    teacher = State()
    days = State()
    time = State()
    price = State()
    small_group = State()


class BroadcastState(StatesGroup):

    message = State()


class SettingState(StatesGroup):

    value = State()


# =========================================================
# HELPER FUNCTIONS
# =========================================================

def format_subject_card(target):
    # target: (id, name, teacher, time, small_group, days, price)
    _, name, teacher, time, small_group, days, price = target
    icon = get_subject_icon(name)

    text = f"""
╭───────────────────────
│ {icon} <b>{name.upper()} KURSI</b>
╰───────────────────────

👨‍🏫 <b>Ustoz:</b> {teacher}
"""
    if days:
        text += f"📅 <b>Dars kunlari:</b> {days}\n"
    text += f"🕐 <b>Dars vaqti:</b> {time}\n"
    if price:
        text += f"💰 <b>Kurs narxi:</b> {price}\n"
    if small_group:
        text += f"👥 <b>Qo'shimcha guruh:</b> {small_group}\n"

    text += """
───────────────────────
💡 <i>Kursga yozilish yoki ma'lumot olish uchun quyidagi tugmalardan foydalaning!</i>
"""
    return text


def clean_subject_query(text: str) -> str:
    if not text:
        return ""
    t = text.lower().strip()
    for e in ["🇺🇿", "🇷🇺", "🇬🇧", "📐", "🧪", "🧬", "⚡", "🏛️", "🏛", "⚖️", "⚖", "💻", "🌍", "📜", "📚", "📖", "⭐", "🔹", "🔸"]:
        t = t.replace(e, "")
    t = t.replace("‘", "'").replace("’", "'").replace("`", "'")
    return t.strip()


async def find_subject_matches(text: str):
    q = clean_subject_query(text)
    if not q:
        return []
    subjects = await get_subjects()

    # 1. Exact match
    for s in subjects:
        if clean_subject_query(s[1]) == q:
            return [s]

    # 2. Substring match
    matches = []
    for s in subjects:
        s_clean = clean_subject_query(s[1])
        if q in s_clean or s_clean in q:
            matches.append(s)

    return matches


def is_fanlar_command(message: Message) -> bool:
    if not message.text:
        return False
    t = clean_subject_query(message.text)
    return t in [
        "fanlar", "fan", "fanlarimiz", "o'quv fanlari", "fanlar royxati",
        "fanlar ro'yxati", "kurslar", "barcha fanlar"
    ] or message.text.strip().lower() in ["/fanlar", "/fan", "/kurslar"]


def is_schedule_message(message: Message) -> bool:
    if not message.text:
        return False
    t = message.text.lower().strip()
    return t == "🕐 dars jadvali" or "dars jadvali" in t or "jadval" in t or t in ["/jadval", "/schedule"]


def is_teachers_message(message: Message) -> bool:
    if not message.text:
        return False
    t = message.text.lower().strip()
    return t == "👨‍🏫 o'qituvchilar" or "o'qituvchilar" in t or "oqituvchilar" in t or "ustozlar" in t or t in ["/ustozlar", "/teachers"]


def is_address_message(message: Message) -> bool:
    if not message.text:
        return False
    t = message.text.lower().strip()
    return t == "📍 manzil" or "manzil" in t or "adres" in t or "qayerda" in t or t in ["/manzil", "/address"]


def is_about_message(message: Message) -> bool:
    if not message.text:
        return False
    t = message.text.lower().strip()
    return t == "ℹ️ markaz haqida" or "markaz haqida" in t or "haqida" in t or t in ["/about", "/haqida", "/info"]


def is_contact_message(message: Message) -> bool:
    if not message.text:
        return False
    t = message.text.lower().strip()
    return (
        t == "📞 bog'lanish" or
        "bog'lanish" in t or
        "boglanish" in t or
        "aloqa" in t or
        "telefon" in t or
        "kontakt" in t or
        t in ["/contact", "/aloqa", "/boglanish"]
    )


SYSTEM_MENU_BUTTONS = {
    "🕐 Dars jadvali", "👨‍🏫 O'qituvchilar", "📍 Manzil", "📞 Bog'lanish",
    "ℹ️ Markaz haqida", "👑 Admin panel", "📊 Statistika",
    "📚 Fanlarni boshqarish", "➕ Fan qo'shish", "📢 Xabar yuborish",
    "⚙️ Sozlamalar", "📚 ⚙️ Sozlamalar", "⬅️ Asosiy menyu", "🚪 Chiqish", "❌ Bekor qilish",
    "📚 Fanlar"
}


async def is_subject_message(message: Message) -> bool:
    if not message.text or message.text.startswith("/") or message.text in SYSTEM_MENU_BUTTONS:
        return False
    if (
        is_fanlar_command(message) or
        is_schedule_message(message) or
        is_teachers_message(message) or
        is_address_message(message) or
        is_about_message(message) or
        is_contact_message(message)
    ):
        return False
    matches = await find_subject_matches(message.text)
    return len(matches) > 0


# =========================================================
# START
# =========================================================

@router.message(CommandStart())
async def start_handler(message: Message, state: FSMContext = None):

    if state:
        await state.clear()

    user = message.from_user

    await add_user(
        user.id,
        user.username,
        user.first_name
    )

    subjects = await get_subjects()

    text = f"""
✨ <b>Assalomu alaykum, {user.first_name}!</b> 👋

🏛 <b>«PIRAMIDA» O'QUV MARKAZI</b>ning rasmiy botiga xush kelibsiz!

🎯 <i>Bizning maqsadimiz — sifatli ta'lim va sizning yuksak natijalaringiz!</i>

📚 <b>Bizning fanlarimiz va xizmatlar:</b>
Quyidagi menyu tugmalaridan birini tanlang 👇
"""

    await message.answer(
        text,
        reply_markup=main_menu(subjects=subjects),
        parse_mode="HTML"
    )


# =========================================================
# USER - SUBJECTS
# =========================================================

@router.message(is_fanlar_command)
@router.message(F.text == "📚 Fanlar")
@router.message(Command("fanlar"))
async def subjects_handler(message: Message):

    await add_user(
        message.from_user.id,
        message.from_user.username,
        message.from_user.first_name
    )

    subjects = await get_subjects()

    text = """
╭───────────────────────
│ 📚 <b>«PIRAMIDA» O'QUV MARKAZI FANLARI</b>
╰───────────────────────

🎯 Markazimizda o'qitiladigan barcha fanlar ro'yxati:

💡 <i>Dars vaqtlari, ustozlar va narxlar haqida to'liq ma'lumot olish uchun kerakli fanni tanlang 👇</i>
"""

    await message.answer(
        text,
        reply_markup=subjects_keyboard(subjects),
        parse_mode="HTML"
    )


@router.message(is_subject_message)
async def menu_subject_handler(message: Message):

    await add_user(
        message.from_user.id,
        message.from_user.username,
        message.from_user.first_name
    )

    matches = await find_subject_matches(message.text)

    if not matches:
        await message.answer("❌ Fan haqida ma'lumot topilmadi.")
        return

    phone = await get_setting("phone") or "+998-97-162-84-00"
    admin_user = await get_setting("admin_username") or "@Isroilova_Ozoda"

    # Agar 1 ta aniq fan bo'lsa
    if len(matches) == 1:
        target = matches[0]
        text = format_subject_card(target)
        await message.answer(
            text,
            reply_markup=subject_detail_keyboard(phone=phone, username=admin_user),
            parse_mode="HTML"
        )
    else:
        # Bir nechta guruh topilsa (masalan Matematika yoki Ingliz tili)
        q = clean_subject_query(message.text).capitalize()
        text = f"""
╭───────────────────────
│ 📚 <b>{q.upper()} KURSLARI</b>
╰───────────────────────

Ushbu fan bo'yicha markazimizda bir nechta guruhlar mavjud.
Kerakli yo'nalish yoki guruhni tanlang 👇
"""
        await message.answer(
            text,
            reply_markup=subjects_keyboard(matches),
            parse_mode="HTML"
        )


@router.callback_query(F.data.startswith("subject:"))
async def subject_handler(callback: CallbackQuery):

    subject_id = int(
        callback.data.split(":")[1]
    )

    subject = await get_subject(subject_id)

    if not subject:
        await callback.answer(
            "❌ Fan topilmadi!",
            show_alert=True
        )
        return

    text = format_subject_card(subject)
    phone = await get_setting("phone") or "+998-97-162-84-00"
    admin_user = await get_setting("admin_username") or "@Isroilova_Ozoda"

    await callback.message.answer(
        text,
        reply_markup=subject_detail_keyboard(phone=phone, username=admin_user),
        parse_mode="HTML"
    )

    await callback.answer()


@router.callback_query(F.data == "all_subjects")
async def all_subjects_callback(callback: CallbackQuery):

    subjects = await get_subjects()

    text = """
╭───────────────────────
│ 📚 <b>«PIRAMIDA» O'QUV MARKAZI FANLARI</b>
╰───────────────────────

Kerakli fanni tanlang va to'liq ma'lumotga ega bo'ling 👇
"""

    await callback.message.answer(
        text,
        reply_markup=subjects_keyboard(subjects),
        parse_mode="HTML"
    )

    await callback.answer()


# =========================================================
# USER - SCHEDULE
# =========================================================

def is_schedule_message(message: Message) -> bool:
    if not message.text:
        return False
    t = message.text.lower().strip()
    return t == "🕐 dars jadvali" or "dars jadvali" in t or "jadval" in t or t in ["/jadval", "/schedule"]


@router.message(is_schedule_message)
@router.message(F.text == "🕐 Dars jadvali")
@router.message(Command("jadval"))
async def schedule_handler(message: Message):

    subjects = await get_subjects()

    text = """
╭───────────────────────
│ 🕐 <b>TO'LIQ DARS JADVALI</b>
╰───────────────────────
"""

    if subjects:
        for idx, subject in enumerate(subjects, 1):
            sub_id, name, teacher, time, small_group, days, price = subject
            icon = get_subject_icon(name)
            text += f"\n{icon} <b>{name}</b>\n"
            text += f"├ 👨‍🏫 <b>Ustoz:</b> {teacher}\n"
            if days:
                text += f"├ 📅 <b>Kunlari:</b> {days}\n"
            text += f"├ 🕐 <b>Vaqti:</b> {time}\n"
            if price:
                text += f"├ 💰 <b>Narxi:</b> {price}\n"
            if small_group:
                text += f"└ 👥 <b>Qo'shimcha guruh:</b> {small_group}\n"
            else:
                text += f"└ 👥 <b>Guruh:</b> Asosiy guruh\n"
    else:
        text += "\n<i>Hozircha dars jadvali kiritilmagan.</i>\n"

    await message.answer(
        text,
        parse_mode="HTML"
    )


# =========================================================
# USER - TEACHERS
# =========================================================

def is_teachers_message(message: Message) -> bool:
    if not message.text:
        return False
    t = message.text.lower().strip()
    return t == "👨‍🏫 o'qituvchilar" or "o'qituvchilar" in t or "oqituvchilar" in t or "ustozlar" in t or t in ["/ustozlar", "/teachers"]


@router.message(is_teachers_message)
@router.message(F.text == "👨‍🏫 O'qituvchilar")
@router.message(Command("ustozlar"))
async def teachers_handler(message: Message):

    subjects = await get_subjects()

    text = """
╭───────────────────────
│ 👨‍🏫 <b>BIZNING USTOZLARIMIZ</b>
╰───────────────────────
"""

    if subjects:
        for idx, subject in enumerate(subjects, 1):
            sub_id, name, teacher, time, small_group, days, price = subject
            icon = get_subject_icon(name)
            text += f"\n⭐ <b>{teacher}</b>\n"
            text += f"├ {icon} <b>Fani:</b> {name}\n"
            if days:
                text += f"├ 📅 <b>Kunlari:</b> {days}\n"
            text += f"├ 🕐 <b>Dars vaqti:</b> {time}\n"
            if price:
                text += f"└ 💰 <b>Kurs narxi:</b> {price}\n"
            else:
                text += f"└ 👥 <b>Guruh:</b> Asosiy guruh\n"
    else:
        text += "\n<i>O'qituvchilar ro'yxati kiritilmagan.</i>\n"

    await message.answer(
        text,
        parse_mode="HTML"
    )


# =========================================================
# USER - ADDRESS
# =========================================================

def is_address_message(message: Message) -> bool:
    if not message.text:
        return False
    t = message.text.lower().strip()
    return t == "📍 manzil" or "manzil" in t or "adres" in t or "qayerda" in t or t in ["/manzil", "/address"]


@router.message(is_address_message)
@router.message(F.text == "📍 Manzil")
@router.message(Command("manzil"))
async def address_handler(message: Message):

    address = await get_setting("address") or "Piramida O'quv Markazi"
    map_url = await get_setting("map_url") or "https://maps.app.goo.gl/orwFAVu6N3APkD216"

    text = f"""
╭───────────────────────
│ 📍 <b>«PIRAMIDA» O'QUV MARKAZI MANZILI</b>
╰───────────────────────

🏢 <b>Mo'ljal:</b> {address}
📸 <b>Bino ko'rinishi:</b> Yuqoridagi fotosuratda markazimiz binosi va kirish qismi ko'rsatilgan.
"""

    if map_url:
        text += f"""
🗺 <b>Google Maps lokatsiyasi:</b>
{map_url}

<i>Xaritada ko'rish va yo'nalish olish uchun quyidagi tugmani bosing 👇</i>
"""

    reply_markup = map_inline_keyboard(map_url) if map_url else None

    photo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "image.png")

    if os.path.exists(photo_path):
        await message.answer_photo(
            photo=FSInputFile(photo_path),
            caption=text,
            reply_markup=reply_markup,
            parse_mode="HTML"
        )
    else:
        await message.answer(
            text,
            reply_markup=reply_markup,
            parse_mode="HTML"
        )


# =========================================================
# USER - ABOUT
# =========================================================

def is_about_message(message: Message) -> bool:
    if not message.text:
        return False
    t = message.text.lower().strip()
    return t == "ℹ️ markaz haqida" or "markaz haqida" in t or "haqida" in t or t in ["/about", "/haqida", "/info"]


@router.message(is_about_message)
@router.message(F.text == "ℹ️ Markaz haqida")
@router.message(Command("about"))
async def about_handler(message: Message):

    subjects = await get_subjects()
    phone = await get_setting("phone") or "+998-97-162-84-00"
    admin_name = await get_setting("admin_name") or "Isroilova Ozoda"
    admin_user = await get_setting("admin_username") or "@Isroilova_Ozoda"
    address = await get_setting("address") or "Piramida O'quv Markazi"

    sub_list = []
    if subjects:
        for s in subjects:
            icon = get_subject_icon(s[1])
            sub_list.append(f"• {icon} <b>{s[1]}</b> — <i>{s[2]}</i>")
    subjects_text = "\n".join(sub_list) if sub_list else "• Fanlar ro'yxati tez kunda e'lon qilinadi."

    text = f"""
╭───────────────────────
│ 🎓 <b>«PIRAMIDA» O'QUV MARKAZI</b>
╰───────────────────────

🏛 <b>Markaz haqida:</b>
«Piramida» o'quv markazi — abituriyentlar va o'quvchilarni oliy ta'lim muassasalariga (OTM) kirishga, milliy hamda xalqaro sertifikatlarga tayyorlovchi zamonaviy o'quv maskanidir!

✨ <b>Bizning afzalliklarimiz:</b>
• 👨‍🏫 Yuqori malakali va tajribali ustozlar
• 👥 Kichik guruhlarda sifatli ta'lim
• 📊 Haftalik sinov testlari va o'zlashtirish nazorati
• 🏢 Qulay, shinam va zamonaviy dars xonalari
• 🎯 OTM ga kirishda kafolatlangan yuqori natijalar

📚 <b>O'qitiladigan fanlar va ustozlar:</b>
{subjects_text}

───────────────────────
🏢 <b>Manzil:</b> {address}
👩‍💼 <b>Admin:</b> {admin_name}
📞 <b>Telefon:</b> <code>{phone}</code>
✈️ <b>Telegram:</b> {admin_user}

<i>Batafsil ma'lumot olish yoki kursga yozilish uchun quyidagi tugmalardan foydalaning 👇</i>
"""

    await message.answer(
        text,
        reply_markup=contact_inline_keyboard(phone=phone, username=admin_user),
        parse_mode="HTML"
    )


# =========================================================
# USER - CONTACT
# =========================================================

def is_contact_message(message: Message) -> bool:
    if not message.text:
        return False
    t = message.text.lower().strip()
    return (
        t == "📞 bog'lanish" or
        "bog'lanish" in t or
        "boglanish" in t or
        "aloqa" in t or
        "telefon" in t or
        "kontakt" in t or
        t in ["/contact", "/aloqa", "/boglanish"]
    )


@router.message(is_contact_message)
@router.message(F.text == "📞 Bog'lanish")
@router.message(Command("contact"))
async def contact_handler(message: Message):

    phone = await get_setting("phone") or "+998-97-162-84-00"
    address = await get_setting("address") or "Piramida O'quv Markazi"
    admin_name = await get_setting("admin_name") or "Isroilova Ozoda"
    admin_user = await get_setting("admin_username") or "@Isroilova_Ozoda"

    text = f"""
╭───────────────────────
│ 📞 <b>BOG'LANISH VA ALOQA</b>
╰───────────────────────

O'quv markazimizga yozilish yoki savollaringiz bo'lsa, biz bilan quyidagi vositalar orqali bog'lanishingiz mumkin:

👩‍💼 <b>Administrator:</b> {admin_name}
📱 <b>Telefon raqam:</b> <code>{phone}</code>
✈️ <b>Telegram admin:</b> {admin_user}
🏢 <b>Manzilimiz:</b> {address}
⏰ <b>Ish vaqti:</b> Har kuni 08:00 dan 20:00 gacha

<i>Savollaringiz bo'lsa, admin bilan bog'lanish yoki qo'ng'iroq qilish tugmasini bosing 👇</i>
"""

    await message.answer(
        text,
        reply_markup=contact_inline_keyboard(phone=phone, username=admin_user),
        parse_mode="HTML"
    )


# =========================================================
# ADMIN - STATISTICS
# =========================================================

@router.message(F.text == "📊 Statistika")
async def statistics_handler(message: Message):

    if not is_admin(message.from_user.id):
        return

    total = await get_users_count()
    active = await get_active_users()
    today = await get_today_users()

    await message.answer(
        f"""
╭───────────────────────
│ 📊 <b>BOT STATISTIKASI</b>
╰───────────────────────

👥 <b>Jami foydalanuvchilar:</b> {total} nafar
🟢 <b>Faol foydalanuvchilar:</b> {active} nafar
📅 <b>Bugun qo'shilganlar:</b> {today} nafar
""",
        parse_mode="HTML"
    )


# =========================================================
# ADMIN - MANAGE SUBJECTS
# =========================================================

@router.message(F.text == "📚 Fanlarni boshqarish")
async def manage_subjects_handler(message: Message):

    if not is_admin(message.from_user.id):
        return

    subjects = await get_subjects()

    await message.answer(
        """
📚 <b>FANLARNI BOSHQARISH</b>

✏️ — fan ma'lumotlarini o'zgartirish

🗑 — fanni o'chirish
""",
        reply_markup=admin_subjects_keyboard(
            subjects
        ),
        parse_mode="HTML"
    )


# =========================================================
# ADMIN - ADD SUBJECT
# =========================================================

@router.message(F.text == "➕ Fan qo'shish")
async def add_subject_start(
    message: Message,
    state: FSMContext
):

    if not is_admin(message.from_user.id):
        return

    await state.set_state(
        AddSubjectState.name
    )

    await message.answer(
        """
➕ <b>YANGI FAN QO'SHISH</b>

1️⃣ Fan nomini yozing.

Masalan:

<code>Informatika</code>
""",
        reply_markup=cancel_keyboard(),
        parse_mode="HTML"
    )


@router.message(AddSubjectState.name, F.text == "❌ Bekor qilish")
@router.message(AddSubjectState.teacher, F.text == "❌ Bekor qilish")
@router.message(AddSubjectState.days, F.text == "❌ Bekor qilish")
@router.message(AddSubjectState.time, F.text == "❌ Bekor qilish")
@router.message(AddSubjectState.price, F.text == "❌ Bekor qilish")
@router.message(AddSubjectState.small_group, F.text == "❌ Bekor qilish")
async def cancel_add_subject(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "❌ Yangi fan qo'shish bekor qilindi.",
        reply_markup=admin_menu()
    )


@router.message(AddSubjectState.name)
async def add_subject_name(
    message: Message,
    state: FSMContext
):

    if message.text in SYSTEM_MENU_BUTTONS:
        await state.clear()
        await message.answer(
            "❌ Yangi fan qo'shish bekor qilindi.",
            reply_markup=admin_menu()
        )
        return

    await state.update_data(
        name=message.text
    )

    await state.set_state(
        AddSubjectState.teacher
    )

    await message.answer(
        """
2️⃣ O'qituvchi ism-familiyasini yozing.

Masalan:

<code>Aliyev Ali</code>
""",
        parse_mode="HTML"
    )


@router.message(AddSubjectState.teacher)
async def add_subject_teacher(
    message: Message,
    state: FSMContext
):

    await state.update_data(
        teacher=message.text
    )

    await state.set_state(
        AddSubjectState.days
    )

    await message.answer(
        """
3️⃣ Dars kunlarini yozing.

Masalan:

<code>Seshanba, Payshanba, Shanba</code>
""",
        parse_mode="HTML"
    )


@router.message(AddSubjectState.days)
async def add_subject_days(
    message: Message,
    state: FSMContext
):

    await state.update_data(
        days=message.text
    )

    await state.set_state(
        AddSubjectState.time
    )

    await message.answer(
        """
4️⃣ Dars vaqtini yozing.

Masalan:

<code>16:00 - 18:00</code>
""",
        parse_mode="HTML"
    )


@router.message(AddSubjectState.time)
async def add_subject_time(
    message: Message,
    state: FSMContext
):

    await state.update_data(
        time=message.text
    )

    await state.set_state(
        AddSubjectState.price
    )

    await message.answer(
        """
5️⃣ Kurs narxini yozing.

Masalan:

<code>Oyiga 350 000 so'm</code>
""",
        parse_mode="HTML"
    )


@router.message(AddSubjectState.price)
async def add_subject_price(
    message: Message,
    state: FSMContext
):

    await state.update_data(
        price=message.text
    )

    await state.set_state(
        AddSubjectState.small_group
    )

    await message.answer(
        """
6️⃣ Qo'shimcha guruh / ma'lumotni yozing.

Masalan:

<code>Ertalabki o'quvchilar: 08:00 - 10:00</code>

Agar qo'shimcha guruh bo'lmasa:

<code>yo'q</code>
""",
        parse_mode="HTML"
    )


@router.message(AddSubjectState.small_group)
async def add_subject_small_group(
    message: Message,
    state: FSMContext
):

    data = await state.get_data()

    small_group = message.text

    if small_group.lower() in [
        "yo'q",
        "yoq",
        "yo'q.",
        "yoq."
    ]:
        small_group = ""

    await add_subject(
        name=data["name"],
        teacher=data["teacher"],
        time=data["time"],
        small_group=small_group,
        days=data.get("days", ""),
        price=data.get("price", "")
    )

    await state.clear()

    await message.answer(
        f"""
✅ <b>YANGI FAN QO'SHILDI!</b>

📚 Fan:
<b>{data["name"]}</b>

👨‍🏫 O'qituvchi:
<b>{data["teacher"]}</b>

📅 Kunlari:
<b>{data.get("days", "")}</b>

🕐 Vaqt:
<b>{data["time"]}</b>

💰 Narxi:
<b>{data.get("price", "")}</b>

👥 Qo'shimcha guruh:
<b>{small_group or "Mavjud emas"}</b>
""",
        reply_markup=admin_menu(),
        parse_mode="HTML"
    )


# =========================================================
# ADMIN - EDIT SUBJECT
# =========================================================

@router.callback_query(F.data.startswith("edit:"))
async def edit_subject_start(
    callback: CallbackQuery,
    state: FSMContext
):

    if not is_admin(callback.from_user.id):
        return

    subject_id = int(
        callback.data.split(":")[1]
    )

    subject = await get_subject(subject_id)

    if not subject:

        await callback.answer(
            "Fan topilmadi!",
            show_alert=True
        )

        return

    await state.update_data(
        subject_id=subject_id
    )

    await state.set_state(
        EditSubjectState.name
    )

    await callback.message.answer(
        f"""
✏️ <b>FANNI O'ZGARTIRISH</b>

Hozirgi nom:

<b>{subject[1]}</b>

Yangi fan nomini yozing:
""",
        parse_mode="HTML"
    )

    await callback.answer()


@router.message(EditSubjectState.name)
async def edit_subject_name(
    message: Message,
    state: FSMContext
):

    await state.update_data(
        name=message.text
    )

    await state.set_state(
        EditSubjectState.teacher
    )

    await message.answer(
        "👨‍🏫 Yangi o'qituvchi ism-familiyasini yozing:"
    )


@router.message(EditSubjectState.teacher)
async def edit_subject_teacher(
    message: Message,
    state: FSMContext
):

    await state.update_data(
        teacher=message.text
    )

    await state.set_state(
        EditSubjectState.days
    )

    await message.answer(
        "📅 Yangi dars kunlarini yozing (masalan: Seshanba, Payshanba, Shanba):"
    )


@router.message(EditSubjectState.days)
async def edit_subject_days(
    message: Message,
    state: FSMContext
):

    await state.update_data(
        days=message.text
    )

    await state.set_state(
        EditSubjectState.time
    )

    await message.answer(
        "🕐 Yangi dars vaqtini yozing (masalan: 16:00 - 18:00):"
    )


@router.message(EditSubjectState.time)
async def edit_subject_time(
    message: Message,
    state: FSMContext
):

    await state.update_data(
        time=message.text
    )

    await state.set_state(
        EditSubjectState.price
    )

    await message.answer(
        "💰 Yangi kurs narxini yozing (masalan: Oyiga 350 000 so'm):"
    )


@router.message(EditSubjectState.price)
async def edit_subject_price(
    message: Message,
    state: FSMContext
):

    await state.update_data(
        price=message.text
    )

    await state.set_state(
        EditSubjectState.small_group
    )

    await message.answer(
        """
👥 Qo'shimcha guruh vaqtini yozing.

Masalan:

<code>Ertalabki o'quvchilar: 08:00 - 10:00</code>

Yoki:

<code>yo'q</code>
""",
        parse_mode="HTML"
    )


@router.message(EditSubjectState.small_group)
async def edit_subject_small_group(
    message: Message,
    state: FSMContext
):

    data = await state.get_data()

    small_group = message.text

    if small_group.lower() in [
        "yo'q",
        "yoq",
        "yo'q.",
        "yoq."
    ]:
        small_group = ""

    await update_subject(
        subject_id=data["subject_id"],
        name=data["name"],
        teacher=data["teacher"],
        time=data["time"],
        small_group=small_group,
        days=data.get("days", ""),
        price=data.get("price", "")
    )

    await state.clear()

    await message.answer(
        """
✅ <b>FAN MUVAFFAQIYATLI O'ZGARTIRILDI!</b>
""",
        reply_markup=admin_menu(),
        parse_mode="HTML"
    )


# =========================================================
# ADMIN - DELETE SUBJECT
# =========================================================

@router.callback_query(F.data.startswith("delete:"))
async def delete_subject_handler(
    callback: CallbackQuery
):

    if not is_admin(callback.from_user.id):
        return

    subject_id = int(
        callback.data.split(":")[1]
    )

    subject = await get_subject(
        subject_id
    )

    if not subject:

        await callback.answer(
            "Fan topilmadi!",
            show_alert=True
        )

        return

    await delete_subject(
        subject_id
    )

    await callback.message.edit_text(
        f"""
🗑 <b>Fan o'chirildi!</b>

📚 {subject[1]}
""",
        parse_mode="HTML"
    )

    await callback.answer(
        "Fan o'chirildi"
    )


# =========================================================
# ADMIN - SETTINGS
# =========================================================

@router.message(F.text.in_(["⚙️ Sozlamalar", "📚 ⚙️ Sozlamalar"]))
async def settings_handler(
    message: Message
):

    if not is_admin(message.from_user.id):
        return

    await message.answer(
        """
⚙️ <b>SOZLAMALAR</b>

Quyidagi ma'lumotlarni
Telegram orqali o'zgartirishingiz mumkin:
""",
        reply_markup=settings_keyboard(),
        parse_mode="HTML"
    )


# =========================================================
# ADMIN - SETTING EDIT
# =========================================================

@router.callback_query(F.data.startswith("setting:"))
async def setting_start(
    callback: CallbackQuery,
    state: FSMContext
):

    if not is_admin(callback.from_user.id):
        return

    key = callback.data.split(":")[1]

    names = {
        "center_name": "🏫 Markaz nomi",
        "address": "📍 Manzil",
        "map_url": "🗺 Xarita linki",
        "phone": "📞 Telefon",
        "admin_name": "👩‍💼 Admin ismi",
        "admin_username": "✈️ Admin Telegram",
        "description": "ℹ️ Markaz haqida"
    }

    await state.update_data(
        setting_key=key
    )

    await state.set_state(
        SettingState.value
    )

    current = await get_setting(key)

    await callback.message.answer(
        f"""
⚙️ <b>{names.get(key, key)}</b>

Hozirgi qiymat:

<code>{current}</code>

Yangi qiymatni yuboring:
""",
        parse_mode="HTML"
    )

    await callback.answer()


@router.message(SettingState.value)
async def setting_save(
    message: Message,
    state: FSMContext
):

    data = await state.get_data()

    key = data["setting_key"]

    await set_setting(
        key,
        message.text
    )

    await state.clear()

    await message.answer(
        """
✅ <b>Sozlama muvaffaqiyatli saqlandi!</b>
""",
        reply_markup=admin_menu(),
        parse_mode="HTML"
    )


# =========================================================
# ADMIN - BROADCAST
# =========================================================

@router.message(F.text == "📢 Xabar yuborish")
async def broadcast_start(
    message: Message,
    state: FSMContext
):

    if not is_admin(message.from_user.id):
        return

    await state.set_state(
        BroadcastState.message
    )

    await message.answer(
        """
📢 <b>BARCHA FOYDALANUVCHILARGA XABAR</b>

Yubormoqchi bo'lgan xabaringizni yozing.

Masalan:

<b>Ertaga barcha darslar soat 14:00 da boshlanadi.</b>
""",
        parse_mode="HTML"
    )


@router.message(BroadcastState.message)
async def broadcast_send(
    message: Message,
    state: FSMContext
):

    if not is_admin(message.from_user.id):
        return

    users = await get_all_user_ids()

    sent = 0
    failed = 0

    await message.answer(
        f"""
📢 Xabar yuborilmoqda...

👥 Foydalanuvchilar:
<b>{len(users)}</b>
""",
        parse_mode="HTML"
    )

    for user_id in users:

        try:

            await message.bot.copy_message(
                chat_id=user_id,
                from_chat_id=message.chat.id,
                message_id=message.message_id
            )

            sent += 1

        except Exception:

            failed += 1

    await state.clear()

    await message.answer(
        f"""
📢 <b>XABAR YUBORILDI</b>

✅ Muvaffaqiyatli:
<b>{sent}</b>

❌ Yuborilmadi:
<b>{failed}</b>
""",
        reply_markup=admin_menu(),
        parse_mode="HTML"
    )


# =========================================================
# ADMIN - BACK
# =========================================================

@router.message(F.text == "⬅️ Asosiy menyu")
async def back_handler(message: Message, state: FSMContext = None):

    if state:
        await state.clear()

    subjects = await get_subjects()

    await message.answer(
        "🏠 <b>Asosiy menyu:</b>",
        reply_markup=main_menu(subjects=subjects),
        parse_mode="HTML"
    )


@router.message(F.text == "🚪 Chiqish")
async def logout_handler(message: Message):

    authenticated_admins.discard(message.from_user.id)
    subjects = await get_subjects()

    await message.answer(
        "🔒 <b>Admin panelidan chiqildi.</b>",
        reply_markup=main_menu(subjects=subjects),
        parse_mode="HTML"
    )


@router.message(F.text == "👑 Admin panel")
@router.message(Command("admin"))
async def admin_panel_handler(message: Message, state: FSMContext):

    if is_admin(message.from_user.id):

        await message.answer(
            """
╭───────────────────────
│ 👑 <b>ADMINISTRATOR PANELI</b>
╰───────────────────────

Boshqarish uchun quyidagi bo'limlardan birini tanlang 👇
""",
            reply_markup=admin_menu(),
            parse_mode="HTML"
        )
        return

    await state.set_state(AdminLoginState.password)
    await message.answer(
        """
╭───────────────────────
│ 🔐 <b>ADMIN PANELGA KIRISH</b>
╰───────────────────────

Iltimos, administrator parolini kiriting:
""",
        reply_markup=cancel_keyboard(),
        parse_mode="HTML"
    )


@router.message(AdminLoginState.password)
async def check_admin_password(message: Message, state: FSMContext):

    if message.text == "❌ Bekor qilish":
        await state.clear()
        subjects = await get_subjects()
        await message.answer(
            "❌ Kirish bekor qilindi.",
            reply_markup=main_menu(subjects=subjects)
        )
        return

    if message.text.strip() == str(ADMIN_PASSWORD):
        authenticated_admins.add(message.from_user.id)
        await state.clear()
        await message.answer(
            """
╭───────────────────────
│ ✅ <b>PAROL TASDIQLANDI!</b>
╰───────────────────────

👑 <b>Administrator paneliga xush kelibsiz!</b>
Kerakli bo'limni tanlang 👇
""",
            reply_markup=admin_menu(),
            parse_mode="HTML"
        )
    else:
        await message.answer(
            """
╭───────────────────────
│ ❌ <b>NOTO'G'RI PAROL!</b>
╰───────────────────────

Iltimos, parolni qaytadan kiriting yoki <b>❌ Bekor qilish</b> tugmasini bosing:
""",
            reply_markup=cancel_keyboard(),
            parse_mode="HTML"
        )