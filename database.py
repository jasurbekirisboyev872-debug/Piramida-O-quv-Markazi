import aiosqlite
from datetime import datetime, timedelta

DB_NAME = "pramida.db"


async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:

        # Foydalanuvchilar
        await db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            last_seen TEXT,
            joined_at TEXT
        )
        """)

        # Fanlar
        await db.execute("""
        CREATE TABLE IF NOT EXISTS subjects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            teacher TEXT NOT NULL,
            time TEXT NOT NULL,
            small_group TEXT DEFAULT '',
            days TEXT DEFAULT '',
            price TEXT DEFAULT ''
        )
        """)

        # Sozlamalar
        await db.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
        """)

        await db.commit()

        # Eski bazaga yangi ustunlar (days, price) mavjudligini tekshirib qo'shish
        cursor = await db.execute("PRAGMA table_info(subjects)")
        columns = [row[1] for row in await cursor.fetchall()]
        if "days" not in columns:
            await db.execute("ALTER TABLE subjects ADD COLUMN days TEXT DEFAULT ''")
        if "price" not in columns:
            await db.execute("ALTER TABLE subjects ADD COLUMN price TEXT DEFAULT ''")

        await db.commit()

        # Standart fanlarni faqat birinchi marta qo'shish
        cursor = await db.execute(
            "SELECT COUNT(*) FROM subjects"
        )
        count = (await cursor.fetchone())[0]

        if count == 0:

            default_subjects = [
                (
                    "Ona tili",
                    "Bozorboyev Murodbek",
                    "16:00 - 18:00",
                    "",
                    "Seshanba, Payshanba, Shanba",
                    "(Oyiga 350 000 so'm)"
                ),
                (
                    "Matematika (Kattalar)",
                    "Tursunboyev Haitboy",
                    "16:00 - 18:00",
                    "Ertalabki o'quvchilar: 08:00 - 10:00 ",
                    "Seshanba, Payshanba, Shanba",
                    "   (Oyiga 350 000 so'm)"
                ),
                (
                    "Matematika (Yosh bolalar)",
                    "Ergashev Ohunjon",
                    "16:00 - 18:00",
                    "",
                    "Seshanba, Payshanba, Shanba",
                    "(Oyiga 350 000 so'm)"
                ),
                (
                    "Matematika (Kichkinalar)",
                    "Saidmurodov Ro'zimurod",
                    "Ertalabki Darsi: 08:00 - 10:00",
                    "Tushdan keyingi guruh: 14:00 - 16:00",
                    "Seshanba, Payshanba, Shanba",
                    "(Oyiga 250 000 so'm)"
                ),
                (
                    "Ingliz tili (Ibrohim)",
                    "Majidov Ibrohim",
                    "14:00 - 18:00",
                    "",
                    "Dushanba, Chorshanba, Juma",
                    "(Oyiga 350 000 so'm)"
                ),
                (
                    "Kimyo",
                    "Bekbo'tayev Zohid",
                    "14:00 - 18:00",
                    "",
                    "Dushanba, Chorshanba, Juma",
                    "(Oyiga 350 000 so'm)"  
                ),
                (
                    "Rus tili",
                    "Ortiqova Iroda",
                    "14:00 - 16:00",
                    "Ertalabki darsi (Yosh bolalar): 08:00 - 10:00",
                    "Seshanba, Payshanba, Shanba",
                    "(Oyiga 350 000 so'm)"
                ),
                (
                    "Tarix",
                    "Bozorboyev Murodbek",
                    "14:00 - 16:00",
                    "",
                    "Seshanba, Payshanba, Shanba",
                    "Oyiga 350 000 so'm"
                ),
                (
                    "Ingliz tili (Jaloliddin)",
                    "Yangiboyev Jaloliddin",
                    "16:30 - 18:30",
                    "Ertalabki guruh (Bolalar): 08:00 - 10:00",
                    "Seshanba, Payshanba, Shanba",
                    "(Oyiga 250 000 so'm)"
                ),
                (
                    "Biologiya",
                    "Abduvoitova Gulnora",
                    "16:30 - 18:30",
                    "",
                    "Seshanba, Payshanba, Shanba",
                    "(Oyiga 350 000 so'm)"
                ),
                (
                    "Fizika",
                    "Azzamqulov Islombek",
                    "16:30 - 18:30",
                    "",
                    "Dushanba, Chorshanba, Juma",
                    "(Oyiga 350 000 so'm)"
                ),
                (
                    "Huquq",
                    "G'oibnazarov Nodir",
                    "15:00 - 17:00",
                    "",
                    "Seshanba, Payshanba, Shanba",
                    "(Oyiga 350 000 so'm)"
                ),
                (
                    "Informatika",
                    "Malakali ustoz",
                    "14:00 - 18:00",
                    "Kompyuter savodxonligi va IT dasturlash",
                    "Dushanba, Chorshanba, Juma",
                    "(Oyiga 350 000 so'm)"
                )
            ]

            await db.executemany("""
            INSERT INTO subjects
            (name, teacher, time, small_group, days, price)
            VALUES (?, ?, ?, ?, ?, ?)
            """, default_subjects)

            await db.commit()

        # Markaz sozlamalari
        default_settings = {
            "center_name": "Piramida O'quv Markazi",
            "address": "Piramida O'quv Markazi",
            "phone": "+998-97-152-84-00",
            "admin_name": "Isroilova Ozoda",
            "admin_username": "@Isroilova_Ozoda",
            "description": (
                "🎓 <b>PIRAMIDA O'QUV MARKAZI</b>\n\n"
                "Markazimizda abituriyentlar va o'quvchilar uchun sifatli va "
                "chuqurlashtirilgan o'quv kurslari faoliyat yuritadi."
            ),
            "map_url": "https://maps.app.goo.gl/orwFAVu6N3APkD216"
        }

        for key, value in default_settings.items():

            await db.execute("""
            INSERT OR IGNORE INTO settings
            (key, value)
            VALUES (?, ?)
            """, (key, value))

        await db.commit()


# =========================================================
# USERS
# =========================================================

async def add_user(user_id, username, first_name):

    now = datetime.now().isoformat()

    async with aiosqlite.connect(DB_NAME) as db:

        await db.execute("""
        INSERT INTO users
        (id, username, first_name, last_seen, joined_at)
        VALUES (?, ?, ?, ?, ?)

        ON CONFLICT(id)
        DO UPDATE SET
            username=excluded.username,
            first_name=excluded.first_name,
            last_seen=excluded.last_seen
        """, (
            user_id,
            username or "",
            first_name or "",
            now,
            now
        ))

        await db.commit()


async def get_users_count():

    async with aiosqlite.connect(DB_NAME) as db:

        cursor = await db.execute(
            "SELECT COUNT(*) FROM users"
        )

        return (await cursor.fetchone())[0]


async def get_active_users():

    limit = datetime.now() - timedelta(minutes=5)

    async with aiosqlite.connect(DB_NAME) as db:

        cursor = await db.execute("""
        SELECT COUNT(*)
        FROM users
        WHERE last_seen >= ?
        """, (limit.isoformat(),))

        return (await cursor.fetchone())[0]


async def get_today_users():

    today = datetime.now().date().isoformat()

    async with aiosqlite.connect(DB_NAME) as db:

        cursor = await db.execute("""
        SELECT COUNT(*)
        FROM users
        WHERE date(joined_at) = ?
        """, (today,))

        return (await cursor.fetchone())[0]


async def get_all_user_ids():

    async with aiosqlite.connect(DB_NAME) as db:

        cursor = await db.execute(
            "SELECT id FROM users"
        )

        rows = await cursor.fetchall()

        return [row[0] for row in rows]


# =========================================================
# SUBJECTS
# =========================================================

_cached_subjects = []


def get_cached_subjects():
    global _cached_subjects
    return _cached_subjects


async def get_subjects():
    global _cached_subjects
    async with aiosqlite.connect(DB_NAME) as db:

        cursor = await db.execute("""
        SELECT id, name, teacher, time, small_group, days, price
        FROM subjects
        ORDER BY id
        """)

        rows = await cursor.fetchall()
        _cached_subjects = rows
        return rows


async def get_subject(subject_id):

    async with aiosqlite.connect(DB_NAME) as db:

        cursor = await db.execute("""
        SELECT id, name, teacher, time, small_group, days, price
        FROM subjects
        WHERE id=?
        """, (subject_id,))

        return await cursor.fetchone()


async def add_subject(
    name,
    teacher,
    time,
    small_group="",
    days="",
    price=""
):

    async with aiosqlite.connect(DB_NAME) as db:

        await db.execute("""
        INSERT INTO subjects
        (name, teacher, time, small_group, days, price)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (
            name,
            teacher,
            time,
            small_group,
            days,
            price
        ))

        await db.commit()


async def update_subject(
    subject_id,
    name,
    teacher,
    time,
    small_group,
    days="",
    price=""
):

    async with aiosqlite.connect(DB_NAME) as db:

        await db.execute("""
        UPDATE subjects

        SET name=?,
            teacher=?,
            time=?,
            small_group=?,
            days=?,
            price=?

        WHERE id=?
        """, (
            name,
            teacher,
            time,
            small_group,
            days,
            price,
            subject_id
        ))

        await db.commit()


async def delete_subject(subject_id):

    async with aiosqlite.connect(DB_NAME) as db:

        await db.execute(
            "DELETE FROM subjects WHERE id=?",
            (subject_id,)
        )

        await db.commit()


# =========================================================
# SETTINGS
# =========================================================

async def get_setting(key):

    async with aiosqlite.connect(DB_NAME) as db:

        cursor = await db.execute("""
        SELECT value
        FROM settings
        WHERE key=?
        """, (key,))

        result = await cursor.fetchone()

        if result:
            return result[0]

        return ""


async def set_setting(key, value):

    async with aiosqlite.connect(DB_NAME) as db:

        await db.execute("""
        INSERT INTO settings
        (key, value)

        VALUES (?, ?)

        ON CONFLICT(key)
        DO UPDATE SET value=excluded.value
        """, (
            key,
            value
        ))

        await db.commit()


async def get_all_settings():

    async with aiosqlite.connect(DB_NAME) as db:

        cursor = await db.execute("""
        SELECT key, value
        FROM settings
        """)

        return await cursor.fetchall()