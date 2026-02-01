import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters

# ==========================================================
#                     ⚙️ الإعدادات
# ==========================================================
TOKEN = "التوكن"
ADMIN_ID = id
CHANNEL_ID = -1003700097462
CHANNEL_LINK = "https://t.me/p2psyria110"  # رابط القناة
COMMISSION = 0.25
OFFERS_FILE = "offers.json"

# ==========================================================
#                     📦 التخزين
# ==========================================================
offers = {}
user_steps = {}
offer_counter = 1000
mediation_sessions = {}
admin_reply_to = {}

# ==========================================================
#                     💾 تحميل / حفظ
# ==========================================================
def load_offers():
    global offers
    try:
        with open(OFFERS_FILE, "r", encoding="utf-8") as f:
            offers.update(json.load(f))
    except:
        offers.clear()

def save_offers():
    with open(OFFERS_FILE, "w", encoding="utf-8") as f:
        json.dump(offers, f, ensure_ascii=False, indent=2)

# ==========================================================
#                     🏠 واجهة البداية
# ==========================================================
START_TEXT = f"""
━━━━━━━━━━━━━━━━━━━━
💎  P2P SYRIA - USDT
━━━━━━━━━━━━━━━━━━━━
🔒 وساطة آمنة 100%
💸 عمولة الوسيط: {COMMISSION}$
━━━━━━━━━━━━━━━━━━━━
"""

def start_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🟢 شراء USDT", callback_data="buy")],
        [InlineKeyboardButton("🔴 بيع USDT", callback_data="sell")]
    ])

# ==========================================================
#                     ▶️ /start
# ==========================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.message.from_user.id

    # تحقق الاشتراك بالقناة
    try:
        member = await context.bot.get_chat_member(CHANNEL_ID, uid)
        if member.status not in ["member", "creator", "administrator"]:
            await update.message.reply_text(
                "🔔 الرجاء الاشتراك بقناة العروض لتتمكن من استخدام البوت",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔗 الانتقال للقناة", url=CHANNEL_LINK)],
                    [InlineKeyboardButton("✅ تم الاشتراك", callback_data="check_subscription")]
                ])
            )
            return
    except:
        await update.message.reply_text(
            "❌ حدث خطأ أثناء التحقق من الاشتراك، الرجاء المحاولة لاحقًا"
        )
        return

    if context.args:
        arg = context.args[0]
        if arg.startswith("reserve_"):
            offer_id = arg.split("_")[-1]
            offer = offers.get(offer_id)

            if not offer or offer["status"] != "published":
                await update.message.reply_text("❌ هذا العرض غير متاح")
                return

            await update.message.reply_text(
                "🛒 تأكيد حجز العرض؟",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("✅ تأكيد الحجز", callback_data=f"confirm_reserve_{offer_id}")],
                    [InlineKeyboardButton("❌ إلغاء", callback_data="cancel_reserve")]
                ])
            )
            return

    await update.message.reply_text(START_TEXT, reply_markup=start_keyboard())

# ==========================================================
#                     🎛 الأزرار
# ==========================================================
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global offer_counter
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    data = q.data

    # ======= التحقق من الاشتراك =======
    if data == "check_subscription":
        member = await context.bot.get_chat_member(CHANNEL_ID, uid)
        if member.status not in ["member", "creator", "administrator"]:
            await q.answer("❌ لم يتم العثور على اشتراكك، الرجاء الاشتراك أولاً", show_alert=True)
            return
        await q.message.edit_text(START_TEXT, reply_markup=start_keyboard())
        await q.answer("✅ تم التحقق من الاشتراك")
        return

    # ======= شراء / بيع =======
    if data in ["buy", "sell"]:
        user_steps[uid] = {"action": "شراء" if data == "buy" else "بيع"}
        await q.message.edit_text(
            "💳 اختر طريقة الدفع:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("💚 سيريتل كاش", callback_data="pay_s")],
                [InlineKeyboardButton("💛 MTN كاش", callback_data="pay_m")]
            ])
        )

    elif data.startswith("pay_"):
        payments = {"pay_s": "سيريتل كاش", "pay_m": "MTN كاش"}
        user_steps[uid]["payment"] = payments[data]
        await q.message.edit_text("💰 أدخل كمية USDT:")

    elif data == "confirm_offer":
        offer_counter += 1
        offer_id = str(offer_counter)
        d = user_steps[uid]

        offers[offer_id] = {
            "owner": uid,
            "action": d["action"],
            "payment": d["payment"],
            "amount": d["amount"],
            "price": d["price"],
            "status": "published"
        }

        msg_text = f"""
━━━━━━━━━━━━━━━━━━━━━━
📢 عرض جديد على P2P SYRIA
━━━━━━━━━━━━━━━━━━━━━━
🔁 العملية: {d['action']}
💰 الكمية: {d['amount']} USDT
💵 السعر: {d['price']}
💳 طريقة الدفع: {d['payment']}
💸 عمولة الوسيط: {COMMISSION}$
━━━━━━━━━━━━━━━━━━━━━━
"""
        msg = await context.bot.send_message(
            CHANNEL_ID,
            msg_text,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🛒 حجز العرض",
                 url=f"https://t.me/{context.bot.username}?start=reserve_{offer_id}")]
            ])
        )

        offers[offer_id]["message_id"] = msg.message_id
        save_offers()
        await q.message.edit_text("✅ تم نشر العرض بنجاح")

    elif data == "cancel_reserve":
        await q.message.edit_text("❌ تم إلغاء الحجز")

    # ======= تأكيد حجز العرض =======
    elif data.startswith("confirm_reserve_"):
        offer_id = data.split("_")[-1]
        offer = offers.get(offer_id)

        if not offer or offer["status"] != "published":
            await q.message.edit_text("❌ هذا العرض غير متاح")
            return

        offer["pending_buyer"] = uid
        offer["status"] = "pending"
        save_offers()

        msg_text = f"""
━━━━━━━━━━━━━━━━━━━━
🔔 طلب حجز جديد
📌 رقم العرض: {offer_id}
━━━━━━━━━━━━━━━━━━━━
هل توافق على الحجز؟
"""
        msg = await context.bot.send_message(
            offer["owner"],
            msg_text,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ موافقة", callback_data=f"approve_{offer_id}")],
                [InlineKeyboardButton("❌ رفض", callback_data=f"reject_{offer_id}")]
            ])
        )

        await q.message.edit_text("⏳ تم إرسال طلب الحجز لصاحب العرض")

    # ======= موافقة على الحجز =======
    elif data.startswith("approve_"):
        offer_id = data.split("_")[-1]
        offer = offers.get(offer_id)

        if not offer or offer["status"] != "pending":
            return

        buyer_id = offer["pending_buyer"]
        offer["buyer"] = buyer_id
        offer["status"] = "reserved"
        save_offers()

        mediation_sessions[offer_id] = {
            "owner": offer["owner"],
            "buyer": buyer_id,
            "active": False,
            "log": []
        }

        # حذف رسالة صاحب العرض القديم
        await context.bot.delete_message(offer["owner"], q.message.message_id)

        # إشعار للطرفين
        await context.bot.send_message(buyer_id, f"✅ تم قبول حجز العرض انتظر ليقوم الوسيط بفتح المحادثة")
        await context.bot.send_message(offer["owner"], f"✅ لقد وافقت على الحجز انتظر ليقوم الوسيط بفتح المحادثة")

        # تحديث رسالة القناة
        await context.bot.edit_message_text(
            chat_id=CHANNEL_ID,
            message_id=offer["message_id"],
            text=f"""
━━━━━━━━━━━━━━━━━━━━
📢 تم حجز هذا العرض 🔒
━━━━━━━━━━━━━━━━━━━━
🔁 العملية: {offer['action']}
💰 الكمية: {offer['amount']} USDT
💵 السعر: {offer['price']}
💳 الدفع: {offer['payment']}
💸 عمولة الوسيط: {COMMISSION}$
━━━━━━━━━━━━━━━━━━━━
""",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔒 محجوز", callback_data="reserved")]
            ])
        )

        # ======= إشعار الوسيط مع زر فتح الجلسة =======
        await context.bot.send_message(
            ADMIN_ID,
            f"""
🔔 تم حجز عرض جديد!
📌 رقم العرض: {offer_id}
🔁 العملية: {offer['action']}
💰 الكمية: {offer['amount']} USDT
💵 السعر: {offer['price']}
💳 الدفع: {offer['payment']}
👤 صاحب العرض: {offer['owner']}
👤 الزبون: {buyer_id}
""",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🟢 فتح جلسة الوساطة", callback_data=f"open_session_{offer_id}")]
            ])
        )

    # ======= رفض الحجز =======
    elif data.startswith("reject_"):
        offer_id = data.split("_")[-1]
        offer = offers.get(offer_id)

        if not offer or offer["status"] != "pending":
            return

        buyer_id = offer["pending_buyer"]

        # حذف رسالة صاحب العرض القديم
        await context.bot.delete_message(offer["owner"], q.message.message_id)

        # حذف رسالة العرض من القناة
        try:
            await context.bot.delete_message(CHANNEL_ID, offer["message_id"])
        except:
            pass

        # إشعار للطرفين
        await context.bot.send_message(buyer_id, f"❌ تم رفض الحجز رقم {offer_id}")
        await context.bot.send_message(offer["owner"], f"❌ لقد رفضت الحجز رقم {offer_id}")

        # إزالة العرض من التخزين
        offers.pop(offer_id)
        save_offers()

    elif data == "reserved":
        await q.answer("🔒 هذا العرض محجوز بالفعل", show_alert=True)

    # ======= جلسة الوساطة =======
    elif data.startswith("open_session_") and uid == ADMIN_ID:
        offer_id = data.split("_")[-1]
        session = mediation_sessions.get(offer_id)
        session["active"] = True

        await q.message.edit_text(
            f"🟢 جلسة وساطة مفتوحة\n📌 رقم العرض: {offer_id}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📤 إرسال لصاحب العرض", callback_data=f"send_owner_{offer_id}")],
                [InlineKeyboardButton("📤 إرسال للزبون", callback_data=f"send_buyer_{offer_id}")],
                [InlineKeyboardButton("🔒 إنهاء الجلسة", callback_data=f"close_session_{offer_id}")]
            ])
        )

        # إشعار للطرفين أن الوسيط فتح الجلسة
        await context.bot.send_message(
            session["owner"],
            "💌 قام الوسيط بفتح الجلسة، يمكنك الآن إرسال الرسائل بأمان"
        )
        await context.bot.send_message(
            session["buyer"],
            "💌 قام الوسيط بفتح الجلسة، يمكنك الآن إرسال الرسائل بأمان"
        )

    elif data.startswith("send_owner_") and uid == ADMIN_ID:
        offer_id = data.split("_")[-1]
        admin_reply_to[uid] = mediation_sessions[offer_id]["owner"]
        await q.answer("✍️ اكتب الرسالة لإرسالها لصاحب العرض")

    elif data.startswith("send_buyer_") and uid == ADMIN_ID:
        offer_id = data.split("_")[-1]
        admin_reply_to[uid] = mediation_sessions[offer_id]["buyer"]
        await q.answer("✍️ اكتب الرسالة لإرسالها للزبون")

    elif data.startswith("close_session_") and uid == ADMIN_ID:
        offer_id = data.split("_")[-1]
        session = mediation_sessions.get(offer_id)
        session["active"] = False

        await context.bot.send_message(session["owner"], "🔒 تم إنهاء جلسة الوساطة شكرًا لثقتكم ♥️")
        await context.bot.send_message(session["buyer"], "🔒 تم إنهاء جلسة الوساطة شكرًا لثقتكم ♥️")

        admin_reply_to.clear()
        await q.message.edit_text("🔒 تم إنهاء الجلسة بنجاح")

# ==========================================================
#                     💬 استقبال الرسائل
# ==========================================================
async def messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.message.from_user.id
    text = update.message.text

    if uid == ADMIN_ID and uid in admin_reply_to:
        target = admin_reply_to[uid]
        await context.bot.send_message(target, f"📩 رسالة من الوسيط:\n\n{text}")
        await update.message.reply_text("✅ تم إرسال الرسالة")
        return

    for session in mediation_sessions.values():
        if session["active"] and (uid == session["owner"] or uid == session["buyer"]):

            sender_role = "صاحب العرض" if uid == session["owner"] else "الزبون"

            await context.bot.send_message(
                ADMIN_ID,
                f"📨 رسالة من {sender_role}:\n\n{text}"
            )

            await update.message.reply_text("📩 تم إرسال رسالتك للوسيط")
            return

    if uid in user_steps:
        step = user_steps[uid]

        if "amount" not in step:
            step["amount"] = float(text)
            await update.message.reply_text("💵 أدخل السعر:")
            return

        if "price" not in step:
            step["price"] = float(text)
            await update.message.reply_text(
                "📄 تأكيد نشر العرض؟",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("✅ تأكيد", callback_data="confirm_offer")]
                ])
            )
            return

# ==========================================================
#                     🚀 تشغيل البوت
# ==========================================================
load_offers()

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(
    buttons,
    pattern="^(buy|sell|pay_|confirm_offer|confirm_reserve_|cancel_reserve|approve_|reject_|open_session_|send_owner_|send_buyer_|close_session_|reserved|check_subscription)"
))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, messages))

app.run_polling()
