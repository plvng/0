from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from datetime import datetime, timezone, timedelta
import os
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    MessageReactionHandler,
    filters,
    ContextTypes,
)
TGK = os.getenv("TGK")
TOKEN = os.getenv("TOKEN")

STOP_MESSAGE = f"🍭РАЗГОВОР ОКОНЧЕН🍭"
FIND_MESSAGE = f"🍭ИЩЕМ ЖДИ🍭"
STOP_FIND_MESSAGE = f"🍭ПОИСК ЗАВЕРШЕН🍭"
FIND_MESSAGE_2 = f"🍭ВСЕ ЕЩЕ ИЩЕМ ЖДИ🍭"
FOUND_MESSAGE = f"🍭РАЗГОВОР НАЧАТ🍭"
SUB_MESSAGE = f"🍭ПОДПИШИСЬ НА {TGK} ЧТОБ РАБОТАЛО🍭"
ONLINE_MESSAGE = f"🍭ОНЛАЙН: $ 🍭"
PREMIUM_MESSAGE = f"🍭ПРЕМИУМ РЕАКЦИИ НЕ ОТПРАВЯТСЯ(🍭"
FIND_PAIR_MESSAGE = f"🍭ТЫ УЖЕ БЕСЕДУЕШЬ>🍭"
CONTACT_MESSAGE = f"🍭НАЖМИ НА КНОПКУ🍭"

NO_TEXT = ['photo', 'video', 'document', 'voice', 'audio', 'video_note', 'sticker', 'animation', 'contact', 'location', 'venue', 'poll']

CONTACT_MARKUP = ReplyKeyboardMarkup([[KeyboardButton("даю свой контакт собеседнику", request_contact=True)]], resize_keyboard=True, one_time_keyboard=True)

def make_user_info(user):
    return f'{user.full_name} @{user.username}'

def start_message():
    utc_time = datetime.now(timezone.utc)
    hour = utc_time.astimezone(timezone(timedelta(hours=3))).hour
    if 5 <= hour < 12: hello = 'Здорово почивали!'
    elif 12 <= hour < 18: hello = 'Здорово дневали!'
    else: hello = 'Здорово вечеряли!'
    return  f"🍭{hello} Знакомства в МГУТУ от админов {TGK}!\n/find - найти собеседника\n/stop - прервать диалог/поиск\n/online - сколько сейчас в сети\nБудь осторожней!🍭"

def clear_map(userid, partnerid, map_):
    keys = map_.keys()
    keys = list(filter(lambda x: str(userid) in x or str(partnerid) in x, keys))
    for key in keys:
        del map_[key]
    return map_

async def check_admin(userid, context):
    member = await context.bot.get_chat_member(chat_id=TGK, user_id=userid)
    return member.status in ['administrator', 'creator']

async def get_info_by_id(update, context):
    if not await check_admin(update.effective_user.id, context): return
    userid = int(update.effective_message.text.split()[1])
    member = await context.bot.get_chat_member(chat_id=TGK, user_id=userid)
    await context.bot.send_message(update.effective_user.id, make_user_info(member.user), reply_markup=ReplyKeyboardRemove())

async def check_online(update, context):
    online_num = str(len(context.bot_data['pairs']) + len(context.bot_data['waiting']))
    await context.bot.send_message(update.effective_user.id, ONLINE_MESSAGE.replace('$', online_num), reply_markup=ReplyKeyboardRemove())

async def check_channel_subscription(userid: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    try:
        member = await context.bot.get_chat_member(chat_id=TGK, user_id=userid)
        return member.status in ['member', 'administrator', 'creator']
    except Exception as _:
        return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(update.effective_user.id, start_message(), reply_markup=ReplyKeyboardRemove())

async def contact_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    userid = update.effective_user.id
    partnerid = context.bot_data['pairs'][userid]
    await context.bot.send_contact(partnerid, *update.effective_message.contact, reply_markup=ReplyKeyboardRemove())

async def contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(update.effective_user.id, CONTACT_MESSAGE, reply_markup=CONTACT_MARKUP)

async def find(update: Update, context: ContextTypes.DEFAULT_TYPE):
    userid = update.effective_user.id
    if not await check_channel_subscription(userid, context):
        await context.bot.send_message(userid, SUB_MESSAGE, reply_markup=ReplyKeyboardRemove())
        return

    if userid in context.bot_data['waiting']:
        await context.bot.send_message(userid, FIND_MESSAGE_2, reply_markup=ReplyKeyboardRemove())
        return

    if userid in context.bot_data['pairs']:
        await context.bot.send_message(userid, FIND_PAIR_MESSAGE, reply_markup=ReplyKeyboardRemove())
        return

    if context.bot_data['waiting']:

        partnerid = context.bot_data['waiting'].pop(0)

        context.bot_data['pairs'][userid] = partnerid
        context.bot_data['pairs'][partnerid] = userid

        print(f"find {userid} {partnerid}")

        await context.bot.send_message(userid, FOUND_MESSAGE, reply_markup=ReplyKeyboardRemove())
        await context.bot.send_message(partnerid, FOUND_MESSAGE, reply_markup=ReplyKeyboardRemove())

    else:
        context.bot_data['waiting'].append(userid)
        await context.bot.send_message(userid, FIND_MESSAGE, reply_markup=ReplyKeyboardRemove())


async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    userid = update.effective_user.id

    if userid in context.bot_data['pairs']:
        partnerid = context.bot_data['pairs'][userid]

        del context.bot_data['pairs'][userid]
        del context.bot_data['pairs'][partnerid]

        await context.bot.send_message(partnerid, STOP_MESSAGE, reply_markup=ReplyKeyboardRemove())
        await context.bot.send_message(userid, STOP_MESSAGE, reply_markup=ReplyKeyboardRemove())
        context.bot_data["message_map"] = clear_map(userid, partnerid, context.bot_data["message_map"])
        print(f"stop {userid} {partnerid}")

    elif userid in context.bot_data['waiting']:
        context.bot_data['waiting'].remove(userid)
        await context.bot.send_message(userid, STOP_FIND_MESSAGE)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user: return
    if update.effective_user.id not in context.bot_data['pairs']: return

    userid = update.effective_user.id

    partnerid = context.bot_data['pairs'][userid]
    message = update.effective_message
    text = message.text if message.text else message.contact.phone_number if message.contact else "no text"
    print(f'{userid} {text}')


    reply_to_id = None
    if message.reply_to_message:
        original_msg_id = message.reply_to_message.message_id
        map_key = f"{userid}:{original_msg_id}"
        reply_to_id = context.bot_data['message_map'].get(map_key)

    try:
        sent_message = await context.bot.copy_message(chat_id=partnerid, from_chat_id=userid, message_id=message.message_id, reply_to_message_id=reply_to_id, reply_markup=ReplyKeyboardRemove())
        context.bot_data['message_map'][f"{userid}:{message.message_id}"] = sent_message.message_id
        context.bot_data['message_map'][f"{partnerid}:{sent_message.message_id}"] = message.message_id
    except Exception as _:
        return


async def handle_reaction(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user: return
    userid = update.effective_user.id
    if userid not in context.bot_data['pairs']: return

    reaction = update.message_reaction
    partnerid = context.bot_data['pairs'][userid]

    try:
        map_key = f"{userid}:{reaction.message_id}"
        partner_message_id = context.bot_data['message_map'].get(map_key)
        if partner_message_id: await context.bot.set_message_reaction(chat_id=partnerid, message_id=partner_message_id, reaction=[] if not reaction.new_reaction else reaction.new_reaction[0])
    except Exception as _:
        await context.bot.send_message(userid, PREMIUM_MESSAGE)


def main():
    application = Application.builder().token(TOKEN).build()

    application.bot_data['waiting'] = []
    application.bot_data['pairs'] = {}
    application.bot_data['message_map'] = {}

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("find", find))
    application.add_handler(CommandHandler("stop", stop))
    application.add_handler(CommandHandler("online", check_online))
    application.add_handler(CommandHandler("get", get_info_by_id))
    application.add_handler(CommandHandler("contact", contact))

    application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND & ~filters.UpdateType.EDITED_MESSAGE, handle_message))
    application.add_handler(MessageReactionHandler(handle_reaction))
    application.add_handler(MessageHandler(filters.CONTACT, contact_callback))
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()