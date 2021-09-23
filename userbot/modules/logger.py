import asyncio

from telethon import events
from telethon.tl.functions.users import GetFullUserRequest

from userbot import BOTLOG, BOTLOG_CHATID, CMD_HELP, LOGS, bot
from userbot.events import register
from userbot.modules.sql_helper import no_log_pms_sql
from userbot.modules.sql_helper.globals import addgvar, gvarstatus
from userbot.utils import edit_delete
from userbot.utils.tools import media_type


class LOG_CHATS:
    def __init__(self):
        self.RECENT_USER = None
        self.NEWPM = None
        self.COUNT = 0


LOG_CHATS_ = LOG_CHATS()


@bot.on(events.NewMessage(incoming=True, func=lambda e: e.is_private))
async def monito_p_m_s(event):
    if not BOTLOG_CHATID:
        return
    if gvarstatus("PMLOG") and gvarstatus("PMLOG") == "false":
        return
    sender = await event.get_sender()
    if not sender.bot:
        chat = await event.get_chat()
        if not no_log_pms_sql.is_approved(chat.id) and chat.id != 777000:
            if LOG_CHATS_.RECENT_USER != chat.id:
                LOG_CHATS_.RECENT_USER = chat.id
                if LOG_CHATS_.NEWPM:
                    if LOG_CHATS_.COUNT > 1:
                        await LOG_CHATS_.NEWPM.edit(
                            LOG_CHATS_.NEWPM.text.replace(
                                "new message", f"{LOG_CHATS_.COUNT} messages"
                            )
                        )
                    else:
                        await LOG_CHATS_.NEWPM.edit(
                            LOG_CHATS_.NEWPM.text.replace(
                                "new message", f"{LOG_CHATS_.COUNT} message"
                            )
                        )
                    LOG_CHATS_.COUNT = 0
                    him_id = event.query.user_id
                LOG_CHATS_.NEWPM = await event.client.send_message(
                    BOTLOG_CHATID,
                    f"👤 [New Pm](tg://user?id={him_id}) has sent a new message \nId : `{chat.id}`",
                )
            try:
                if event.message:
                    await event.client.forward_messages(
                        BOTLOG_CHATID, event.message, silent=True
                    )
                LOG_CHATS_.COUNT += 1
            except Exception as e:
                LOGS.warn(str(e))


@bot.on(events.NewMessage(incoming=True, func=lambda e: e.mentioned))
async def log_tagged_messages(event):
    hmm = await event.get_chat()

    if gvarstatus("GRPLOG") and gvarstatus("GRPLOG") == "false":
        return
    if (
        (no_log_pms_sql.is_approved(hmm.id))
        or (not BOTLOG_CHATID)
        or (await event.get_sender() and (await event.get_sender()).bot)
    ):
        return
    full = None
    try:
        full = await event.client.get_entity(event.message.from_id)
    except Exception as e:
        LOGS.info(str(e))
    messaget = media_type(event)
    resalt = f"#TAGS \n<b>Group : </b><code>{hmm.title}</code>"
    await event.client(GetFullUserRequest(event.query.user_id))
    him_id = event.query.user_id
    if full is not None:
        resalt += f"\n<b>From : </b> 👤 [New MSG📨](tg://user?id={him_id})"
    if messaget is not None:
        resalt += f"\n<b>Message type : </b><code>{messaget}</code>"
    else:
        resalt += f"\n<b>Message : </b>{event.message.message}"
    resalt += f"\n<b>Message link: </b><a href = 'https://t.me/c/{hmm.id}/{event.message.id}'> link</a>"
    if not event.is_private:
        await event.client.send_message(
            BOTLOG_CHATID,
            resalt,
            parse_mode="html",
            link_preview=False,
        )


@register(outgoing=True, pattern=r"^\.save(?: |$)(.*)")
async def log(log_text):
    if BOTLOG:
        if log_text.reply_to_msg_id:
            reply_msg = await log_text.get_reply_message()
            await reply_msg.forward_to(BOTLOG_CHATID)
        elif log_text.pattern_match.group(1):
            user = f"#LOG / Chat ID: {log_text.chat_id}\n\n"
            textx = user + log_text.pattern_match.group(1)
            await log_text.client.send_message(BOTLOG_CHATID, textx)
        else:
            await log_text.edit("`What am I supposed to log?`")
            return
        await log_text.edit("`Logged Successfully`")
    else:
        await log_text.edit("`This feature requires Logging to be enabled!`")
    await asyncio.sleep(2)
    await log_text.delete()


@register(outgoing=True, pattern=r"^\.log$")
async def set_no_log_p_m(event):
    if BOTLOG_CHATID is not None:
        chat = await event.get_chat()
        if no_log_pms_sql.is_approved(chat.id):
            no_log_pms_sql.disapprove(chat.id)
            await edit_delete(
                event, "`logging of messages from this group has been started`", 5
            )


@register(outgoing=True, pattern=r"^\.nolog$")
async def set_no_log_p_m(event):
    if BOTLOG_CHATID is not None:
        chat = await event.get_chat()
        if not no_log_pms_sql.is_approved(chat.id):
            no_log_pms_sql.approve(chat.id)
            await edit_delete(
                event, "`Logging of messages from this chat has been stopped`", 5
            )


@register(outgoing=True, pattern=r"^\.pmlog (on|off)$")
async def set_pmlog(event):
    if event.fwd_from:
        return
    input_str = event.pattern_match.group(1)
    if input_str == "off":
        h_type = False
    elif input_str == "on":
        h_type = True
    if gvarstatus("PMLOG") and gvarstatus("PMLOG") == "false":
        PMLOG = False
    else:
        PMLOG = True
    if PMLOG:
        if h_type:
            await event.edit("`Pm logging is already enabled`")
        else:
            addgvar("PMLOG", h_type)
            await event.edit("`Pm logging is disabled`")
    else:
        if h_type:
            addgvar("PMLOG", h_type)
            await event.edit("`Pm logging is enabled`")
        else:
            await event.edit("`Pm logging is already disabled`")


@register(outgoing=True, pattern=r"^\.gruplog (on|off)$")
async def set_grplog(event):
    if event.fwd_from:
        return
    input_str = event.pattern_match.group(1)
    if input_str == "off":
        h_type = False
    elif input_str == "on":
        h_type = True
    if gvarstatus("GRPLOG") and gvarstatus("GRPLOG") == "false":
        GRPLOG = False
    else:
        GRPLOG = True
    if GRPLOG:
        if h_type:
            await event.edit("`Group logging is already enabled`")
        else:
            addgvar("GRPLOG", h_type)
            await event.edit("`Group logging is disabled`")
    else:
        if h_type:
            addgvar("GRPLOG", h_type)
            await event.edit("`Group logging is enabled`")
        else:
            await event.edit("`Group logging is already disabled`")


CMD_HELP.update(
    {
        "logchats": "**Plugin : **`logchats`\
        \n\n  •  **Syntax :** `.save`\
        \n  •  **Function : **__Saves tagged message in private group .__\
        \n\n  •  **Syntax :** `.log`\
        \n  •  **Function : **__By default will log all private chat messages if you use .nolog and want to log again then you need to use this__\
        \n\n  •  **Syntax :** `.nolog`\
        \n  •  **Function : **__Stops logging from a private chat or group where you used__\
        \n\n  •  **Syntax :** `.pmlog on/off`\
        \n  •  **Function : **__To turn on and turn off personal messages logging__\
        \n\n  •  **Syntax :** `.nolog`\
        \n  •  **Function : **__To turn on and turn off Group messages(tagged) logging__"
    }
)
