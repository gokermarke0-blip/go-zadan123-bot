import asyncio
import os
import zipfile
import aiohttp
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import FSInputFile, ReplyKeyboardMarkup, KeyboardButton

load_dotenv()

bot = Bot(token=os.getenv("8734956156:AAHgBvqF54ASeJe_bI9xt-04gQuROFce5Aw"))
dp = Dispatcher()

# تخزين مؤقت للبيانات
user_data = {}

# ====================== دالة الـ AI (Groq + Gemini) ======================
async def improve_with_ai(html_code: str, user_id: int):
    prompt = f"""
أنت خبير ويب ديفلوبر محترف.
لدي كود HTML التالي، قم بـ:
1. تصليح أي أخطاء موجودة.
2. تحسين التصميم ليصبح فخم وعصري جداً (استخدم Tailwind أو CSS حديث).
3. جعله Responsive.
4. كتابة وصف جميل للمشروع (بالعربي).

الكود:
{html_code[:8000]}  # نحد من الحجم

أعد الكود المحسن كاملاً في صورة HTML واحد جاهز.
"""

    # نستخدم Groq أولاً لأنه سريع
    async with aiohttp.ClientSession() as session:
        async with session.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {os.getenv('GROQ_API_KEY')}"},
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7
            }
        ) as resp:
            data = await resp.json()
            improved_html = data['choices'][0]['message']['content']
            return improved_html

# ====================== استقبال الملف ======================
@dp.message(F.document)
async def handle_document(message: types.Message):
    doc = message.document
    user_id = message.from_user.id

    if not doc.file_name.lower().endswith('.html'):
        await message.reply("❌ يرجى إرسال ملف HTML فقط في البداية.")
        return

    # تحميل الملف
    file = await bot.get_file(doc.file_id)
    file_path = f"uploads/{user_id}_{doc.file_name}"
    os.makedirs("uploads", exist_ok=True)

    await bot.download_file(file.file_path, file_path)

    user_data[user_id] = {
        "html_path": file_path,
        "html_name": doc.file_name
    }

    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="لا يوجد")]],
        resize_keyboard=True,
        one_time_keyboard=True
    )

    await message.reply(
        "✅ تم استلام ملف HTML بنجاح.\n\n"
        "هل لديك ملف **CSS** منفصل؟\n"
        "أرسله الآن، أو اكتب 'لا يوجد'",
        reply_markup=keyboard
    )

# ====================== التعامل مع CSS ======================
@dp.message(F.document | F.text.lower().in_(["لا", "لا يوجد", "no"]))
async def handle_css_or_next(message: types.Message):
    user_id = message.from_user.id
    data = user_data.get(user_id)

    if not data:
        await message.reply("ابدأ بإرسال ملف HTML أولاً.")
        return

    if message.document and message.document.file_name.lower().endswith('.css'):
        # حفظ CSS
        file = await bot.get_file(message.document.file_id)
        css_path = f"uploads/{user_id}_style.css"
        await bot.download_file(file.file_path, css_path)
        data["css_path"] = css_path
        await message.reply("✅ تم استلام ملف CSS.\n\nهل لديك ملف JavaScript؟\nأرسله أو اكتب 'لا يوجد'")

    else:
        # لا يوجد CSS → نروح للـ AI
        await process_with_ai(message, user_id)

# ====================== معالجة بالـ AI و النشر ======================
async def process_with_ai(message: types.Message, user_id: int):
    data = user_data.get(user_id)
    if not data:
        return

    await message.reply("⏳ جاري تحسين الموقع باستخدام الذكاء الاصطناعي...")

    # قراءة الكود
    with open(data["html_path"], "r", encoding="utf-8") as f:
        html_code = f.read()

    # تحسين بالـ AI
    improved_html = await improve_with_ai(html_code, user_id)

    # حفظ الكود المحسن
    final_path = f"uploads/{user_id}_final.html"
    with open(final_path, "w", encoding="utf-8") as f:
        f.write(improved_html)

    # إنشاء ZIP
    zip_path = f"uploads/{user_id}_project.zip"
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        zipf.write(final_path, "index.html")

    await message.reply("✅ تم تحسين الموقع بنجاح!\nجاري نشره على الإنترنت...")

    # هنا سنضيف دالة النشر على Tiiny لاحقاً (في الرسالة القادمة)

    # مؤقتاً
    await message.reply(f"🔗 رابط المشروع:\nhttps://example.tiiny.site\n(سيتم تفعيل النشر قريباً)")

@dp.message(Command("start"))
async def start(message: types.Message):
    await message.reply("👋 مرحبا!\nأرسل ملف HTML الخاص بمشروعك وسأساعدك في تحسينه ونشره باستخدام الذكاء الاصطناعي.")

async def main():
    print("🚀 البوت شغال على JustRunMy.App")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())