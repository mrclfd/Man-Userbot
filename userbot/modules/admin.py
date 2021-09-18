# Copyright (C) 2019 The Raphielscape Company LLC.
#
# Licensed under the Raphielscape Public License, Version 1.c (the "License");
# you may not use this file except in compliance with the License.

import logging
from asyncio import sleep

from telethon.errors import (
    BadRequestError,
    ImageProcessFailedError,
    PhotoCropSizeSmallError,
)
from telethon.errors.rpcerrorlist import UserAdminInvalidError, UserIdInvalidError
from telethon.tl.functions.channels import (
    EditAdminRequest,
    EditBannedRequest,
    EditPhotoRequest,
)
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.types import (
    ChannelParticipantsAdmins,
    ChatAdminRights,
    ChatBannedRights,
    InputChatPhotoEmpty,
    MessageEntityMentionName,
    MessageMediaPhoto,
)
from telethon.utils import get_display_name

from userbot import ALIVE_NAME, BOTLOG, BOTLOG_CHATID, CMD_HELP, DEVS
from userbot.events import register
from userbot.utils import _format, edit_delete, edit_or_reply

# =================== CONSTANT ===================
PP_TOO_SMOL = "**Gambar Terlalu Kecil**"
PP_ERROR = "**Gagal Memproses Gambar**"
NO_ADMIN = "**Gagal dikarenakan Bukan Admin :)**"
NO_PERM = "**Tidak Mempunyai Izin!**"
NO_SQL = "**Berjalan Pada Mode Non-SQL**"
CHAT_PP_CHANGED = "**Berhasil Mengubah Profil Grup**"
INVALID_MEDIA = "**Media Tidak Valid**"

BANNED_RIGHTS = ChatBannedRights(
    until_date=None,
    view_messages=True,
    send_messages=True,
    send_media=True,
    send_stickers=True,
    send_gifs=True,
    send_games=True,
    send_inline=True,
    embed_links=True,
)

UNBAN_RIGHTS = ChatBannedRights(
    until_date=None,
    send_messages=None,
    send_media=None,
    send_stickers=None,
    send_gifs=None,
    send_games=None,
    send_inline=None,
    embed_links=None,
)
logging.basicConfig(
    format="[%(levelname)s- %(asctime)s]- %(name)s- %(message)s",
    level=logging.INFO,
    datefmt="%H:%M:%S",
)

LOGS = logging.getLogger(__name__)
MUTE_RIGHTS = ChatBannedRights(until_date=None, send_messages=True)
UNMUTE_RIGHTS = ChatBannedRights(until_date=None, send_messages=False)
# ================================================


@register(outgoing=True, pattern=r"^\.setgpic( -s| -d)$")
async def set_group_photo(event):
    "For changing Group dp"
    flag = (event.pattern_match.group(1)).strip()
    if flag == "-s":
        replymsg = await event.get_reply_message()
        photo = None
        if replymsg and replymsg.media:
            if isinstance(replymsg.media, MessageMediaPhoto):
                photo = await event.client.download_media(message=replymsg.photo)
            elif "image" in replymsg.media.document.mime_type.split("/"):
                photo = await event.client.download_file(replymsg.media.document)
            else:
                return await edit_delete(event, INVALID_MEDIA)
        if photo:
            try:
                await event.client(
                    EditPhotoRequest(
                        event.chat_id, await event.client.upload_file(photo)
                    )
                )
                await edit_delete(event, CHAT_PP_CHANGED)
            except PhotoCropSizeSmallError:
                return await edit_delete(event, PP_TOO_SMOL)
            except ImageProcessFailedError:
                return await edit_delete(event, PP_ERROR)
            except Exception as e:
                return await edit_delete(event, f"**ERROR : **`{str(e)}`")
            process = "updated"
    else:
        try:
            await event.client(EditPhotoRequest(event.chat_id, InputChatPhotoEmpty()))
        except Exception as e:
            return await edit_delete(event, f"**ERROR : **`{e}`")
        process = "deleted"
        await edit_delete(event, "**Foto Profil Grup Berhasil dihapus.**", 30)
    if BOTLOG:
        await event.client.send_message(
            BOTLOG_CHATID,
            "**#GROUPPIC**\n"
            f"📸 **Group profile pic {process} successfully**\n"
            f"👥 **CHAT :** {get_display_name(await event.get_chat())}(`{event.chat_id}`)",
        )


@register(outgoing=True, pattern=r"^\.promote(?:\s|$)([\s\S]*)")
async def promote(event):
    new_rights = ChatAdminRights(
        add_admins=False,
        change_info=False,
        invite_users=True,
        ban_users=True,
        delete_messages=True,
        pin_messages=True,
        manage_call=True,
    )
    user, rank = await get_user_from_event(event)
    if not rank:
        rank = "admin"
    if not user:
        return
    eventman = await edit_or_reply(event, "`Promoting...`")
    try:
        await event.client(EditAdminRequest(event.chat_id, user.id, new_rights, rank))
    except BadRequestError:
        return await eventman.edit(NO_PERM)
    await edit_delete(eventman, "`Promoted Successfully!`", 30)
    if BOTLOG:
        await event.client.send_message(
            BOTLOG_CHATID,
            f"**#PROMOTE**\
            \n👤 **USER :** [{user.first_name}](tg://user?id={user.id})\
            \n👥 **CHAT :** {get_display_name(await event.get_chat())} (`{event.chat_id}`)",
        )


@register(outgoing=True, pattern=r"^\.demote(?:\s|$)([\s\S]*)")
async def demote(event):
    "To demote a person in group"
    user, _ = await get_user_from_event(event)
    if not user:
        return
    eventman = await edit_or_reply(event, "`Demoting...`")
    newrights = ChatAdminRights(
        add_admins=None,
        invite_users=None,
        change_info=None,
        ban_users=None,
        delete_messages=None,
        pin_messages=None,
    )
    rank = "admin"
    try:
        await event.client(EditAdminRequest(event.chat_id, user.id, newrights, rank))
    except BadRequestError:
        return await eventman.edit(NO_PERM)
    await edit_delete(eventman, "`Demoted Successfully!`", 30)
    if BOTLOG:
        await event.client.send_message(
            BOTLOG_CHATID,
            f"**#DEMOTE**\
            \n👤 **USER :** [{user.first_name}](tg://user?id={user.id})\
            \n👥 **CHAT :** {get_display_name(await event.get_chat())}(`{event.chat_id}`)",
        )


@register(outgoing=True, pattern=r"^\.ban(?:\s|$)([\s\S]*)")
async def _ban_person(event):
    user, reason = await get_user_from_event(event)
    if not user:
        return
    if user.id == event.client.uid:
        return await edit_delete(event, "**Tidak Bisa Membanned Diri Sendiri 🐷**", 60)
    
    if user.id in DEVS:
        return await edit_delete(event, "**Gagal Banned, Dia Adalah Pembuat Saya 🤪**", 60)

    eventman = await edit_or_reply(event, "`Processing...`")
    try:
        await event.client(EditBannedRequest(event.chat_id, user.id, BANNED_RIGHTS))
    except BadRequestError:
        return await eventman.edit(NO_PERM)
    try:
        reply = await event.get_reply_message()
        if reply:
            await reply.delete()
    except BadRequestError:
        return await eventman.edit(
            "**Saya Tidak Memiliki Hak Hapus Pesan Grup! Tapi tetap saja dia di banned!**"
        )
    if reason:
        await eventman.edit(
            f"**Mampus Kau** {_format.mentionuser(user.first_name ,user.id)} **TERBANNED 😡**\n**Karena : **`{reason}`"
        )
    else:
        await eventman.edit(
            f"**Mampus Kau** {_format.mentionuser(user.first_name ,user.id)} **TERBANNED** 😡"
        )
    if BOTLOG:
        if reason:
            await event.client.send_message(
                BOTLOG_CHATID,
                f"**#Banned_User**\
                \n👤 **First Name:** [{user.first_name}](tg://user?id={user.id})\
                \n👥 **Group:** {get_display_name(await event.get_chat())}(`{event.chat_id}`)\
                \n🔖 **Reason:** {reason}",
            )
        else:
            await event.client.send_message(
                BOTLOG_CHATID,
                f"**#Banned_User**\
                \n👤 **First Name:** [{user.first_name}](tg://user?id={user.id})\
                \n👥 **Group:** {get_display_name(await event.get_chat())}(`{event.chat_id}`)",
            )


@register(outgoing=True, pattern=r"^\.unban(?:\s|$)([\s\S]*)")
async def nothanos(event):
    user, _ = await get_user_from_event(event)
    if not user:
        return
    eventman = await edit_or_reply(event, "`Unbanning...`")
    try:
        await event.client(EditBannedRequest(event.chat_id, user.id, UNBAN_RIGHTS))
        await eventman.edit(
            f"{_format.mentionuser(user.first_name ,user.id)} **Berhasil di Unbanned**"
        )
        await sleep(10)
        await eventman.delete()
        if BOTLOG:
            await event.client.send_message(
                BOTLOG_CHATID,
                "**#UNBAN**\n"
                f"👤 **First Name:** [{user.first_name}](tg://user?id={user.id})\n"
                f"👥 **Group:** {get_display_name(await event.get_chat())}(`{event.chat_id}`)",
            )
    except UserIdInvalidError:
        await eventman.edit("**Maaf Logika Unban Saya Rusak 🥺**")
    except Exception as e:
        await eventman.edit(f"**ERROR:** `{e}`")


@register(outgoing=True, pattern=r"^\.dmute(?: |$)(.*)")
async def spider(spdr):
    # Check if the function running under SQL mode
    try:
        from userbot.modules.sql_helper.spam_mute_sql import mute
    except AttributeError:
        return await spdr.edit(NO_SQL)

    # Admin or creator check
    chat = await spdr.get_chat()
    admin = chat.admin_rights
    creator = chat.creator

    # If not admin and not creator, return
    if not admin and not creator:
        return await spdr.edit(NO_ADMIN)

    user, reason = await get_user_from_event(spdr)
    if not user:
        return

    self_user = await spdr.client.get_me()

    if user.id == self_user.id:
        return await spdr.edit("`Tidak Bisa Membisukan Diri Sendiri..（>﹏<）`")

    if user.id in DEVS:
        return await spdr.edit("**Gagal Mute, Dia Adalah Pembuat Saya 🤪**")

    # If everything goes well, do announcing and mute
    await spdr.edit(
        r"\\**#DMute_User**//"
        f"\n\n**First Name:** [{user.first_name}](tg://user?id={user.id})\n"
        f"**User ID:** `{user.id}`\n"
        f"**Action:** `DMute by {ALIVE_NAME}`"
    )
    if mute(spdr.chat_id, user.id) is False:
        return await spdr.edit("`Error! Pengguna Sudah Dibisukan.`")
    try:
        await spdr.client(EditBannedRequest(spdr.chat_id, user.id, MUTE_RIGHTS))

        # Announce that the function is done
        if reason:
            await spdr.edit(
                r"\\**#DMute_User**//"
                f"\n\n**First Name:** [{user.first_name}](tg://user?id={user.id})\n"
                f"**User ID:** `{user.id}`\n"
                f"**Reason:** `{reason}`"
            )
        else:
            await spdr.edit(
                r"\\**#DMute_User**//"
                f"\n\n**First Name:** [{user.first_name}](tg://user?id={user.id})\n"
                f"**User ID:** `{user.id}`\n"
                f"**Action:** `DMute by {ALIVE_NAME}`"
            )

        # Announce to logging group
        if BOTLOG:
            await spdr.client.send_message(
                BOTLOG_CHATID,
                "#MUTE\n"
                f"PENGGUNA: [{user.first_name}](tg://user?id={user.id})\n"
                f"GRUP: {spdr.chat.title}(`{spdr.chat_id}`)",
            )
    except UserIdInvalidError:
        return await spdr.edit("`Terjadi Kesalahan!`")


@register(outgoing=True, pattern=r"^\.undmute(?: |$)(.*)")
async def unmoot(unmot):
    # Admin or creator check
    chat = await unmot.get_chat()
    admin = chat.admin_rights
    creator = chat.creator

    # If not admin and not creator, return
    if not admin and not creator:
        return await unmot.edit(NO_ADMIN)

    # Check if the function running under SQL mode
    try:
        from userbot.modules.sql_helper.spam_mute_sql import unmute
    except AttributeError:
        return await unmot.edit(NO_SQL)

    # If admin or creator, inform the user and start unmuting
    await unmot.edit("```Melakukan Unmute...```")
    user = await get_user_from_event(unmot)
    user = user[0]
    if not user:
        return

    if unmute(unmot.chat_id, user.id) is False:
        return await unmot.edit("**ERROR!** Pengguna Sudah Tidak Dibisukan.")
    try:
        await unmot.client(EditBannedRequest(unmot.chat_id, user.id, UNBAN_RIGHTS))
        await unmot.edit(
            "**Berhasil Melakukan Unmute! User Sudah Tidak Lagi Dibisukan**"
        )
        await sleep(3)
        await unmot.delete()
    except UserIdInvalidError:
        return await unmot.edit("**Terjadi ERROR!**")

    if BOTLOG:
        await unmot.client.send_message(
            BOTLOG_CHATID,
            "#UNMUTE\n"
            f"PENGGUNA: [{user.first_name}](tg://user?id={user.id})\n"
            f"GRUP: {unmot.chat.title}(`{unmot.chat_id}`)",
        )


@register(incoming=True)
async def muter(moot):
    try:
        from userbot.modules.sql_helper.gmute_sql import is_gmuted
        from userbot.modules.sql_helper.spam_mute_sql import is_muted
    except AttributeError:
        return
    muted = is_muted(moot.chat_id)
    gmuted = is_gmuted(moot.sender_id)
    rights = ChatBannedRights(
        until_date=None,
        send_messages=True,
        send_media=True,
        send_stickers=True,
        send_gifs=True,
        send_games=True,
        send_inline=True,
        embed_links=True,
    )
    if muted:
        for i in muted:
            if str(i.sender) == str(moot.sender_id):
                await moot.delete()
                await moot.client(
                    EditBannedRequest(moot.chat_id, moot.sender_id, rights)
                )
    for i in gmuted:
        if i.sender == str(moot.sender_id):
            await moot.delete()


@register(outgoing=True, pattern=r"^\.ungmute(?: |$)(.*)")
async def ungmoot(un_gmute):
    # Admin or creator check
    chat = await un_gmute.get_chat()
    admin = chat.admin_rights
    creator = chat.creator

    # If not admin and not creator, return
    if not admin and not creator:
        return await un_gmute.edit(NO_ADMIN)

    # Check if the function running under SQL mode
    try:
        from userbot.modules.sql_helper.gmute_sql import ungmute
    except AttributeError:
        return await un_gmute.edit(NO_SQL)

    user = await get_user_from_event(un_gmute)
    user = user[0]
    if not user:
        return

    # If pass, inform and start ungmuting
    await un_gmute.edit("```Membuka Global Mute Pengguna...```")

    if ungmute(user.id) is False:
        await un_gmute.edit("**ERROR!** Pengguna Sedang Tidak Di Gmute.")
    else:
        # Inform about success
        await un_gmute.edit("**Berhasil! Pengguna Sudah Tidak Lagi Dibisukan**")
        await sleep(3)
        await un_gmute.delete()

        if BOTLOG:
            await un_gmute.client.send_message(
                BOTLOG_CHATID,
                "#UNGMUTE\n"
                f"PENGGUNA: [{user.first_name}](tg://user?id={user.id})\n"
                f"GRUP: {un_gmute.chat.title}(`{un_gmute.chat_id}`)",
            )


@register(outgoing=True, pattern=r"^\.gmute(?: |$)(.*)")
async def gspider(gspdr):
    # Admin or creator check
    chat = await gspdr.get_chat()
    admin = chat.admin_rights
    creator = chat.creator

    # If not admin and not creator, return
    if not admin and not creator:
        return await gspdr.edit(NO_ADMIN)

    # Check if the function running under SQL mode
    try:
        from userbot.modules.sql_helper.gmute_sql import gmute
    except AttributeError:
        return await gspdr.edit(NO_SQL)

    user, reason = await get_user_from_event(gspdr)
    if not user:
        return

    self_user = await gspdr.client.get_me()

    if user.id == self_user.id:
        return await gspdr.edit("**Tidak Bisa Membisukan Diri Sendiri..（>﹏<）**")

    if user.id in DEVS:
        return await gspdr.edit("**Gagal Global Mute, Dia Adalah Pembuat Saya 🤪**")

    # If pass, inform and start gmuting
    await gspdr.edit("**Berhasil Membisukan Pengguna!**")
    if gmute(user.id) is False:
        await gspdr.edit("**ERROR! Pengguna Sudah Dibisukan.**")
    else:
        if reason:
            await gspdr.edit(
                r"\\**#GMuted_User**//"
                f"\n\n**First Name:** [{user.first_name}](tg://user?id={user.id})\n"
                f"**User ID:** `{user.id}`\n"
                f"**Reason:** `{reason}`"
            )
        else:
            await gspdr.edit(
                r"\\**#GMuted_User**//"
                f"\n\n**First Name:** [{user.first_name}](tg://user?id={user.id})\n"
                f"**User ID:** `{user.id}`\n"
                f"**Action:** `Global Muted by {ALIVE_NAME}`"
            )

        if BOTLOG:
            await gspdr.client.send_message(
                BOTLOG_CHATID,
                "#GLOBALMUTE\n"
                f"PENGGUNA: [{user.first_name}](tg://user?id={user.id})\n"
                f"GRUP: {gspdr.chat.title}(`{gspdr.chat_id}`)",
            )


@register(outgoing=True, pattern=r"^\.zombies(?: |$)(.*)", groups_only=False)
async def rm_deletedacc(show):

    con = show.pattern_match.group(1).lower()
    del_u = 0
    del_status = "`Grup Bersih, Tidak Menemukan Akun Terhapus.`"

    if con != "clean":
        await show.edit("`Mencari Akun Depresi/Terhapus/Zombie...`")
        async for user in show.client.iter_participants(show.chat_id):

            if user.deleted:
                del_u += 1
                await sleep(1)
        if del_u > 0:
            del_status = (
                f"**Menemukan** `{del_u}` **Akun Depresi/Terhapus/Zombie Dalam Grup Ini,"
                "\nBersihkan Itu Menggunakan Perintah** `.zombies clean`"
            )
        return await show.edit(del_status)

    # Here laying the sanity check
    chat = await show.get_chat()
    admin = chat.admin_rights
    creator = chat.creator

    # Well
    if not admin and not creator:
        return await show.edit("**Bukan Admin Disini!**")

    await show.edit("`Menghapus Akun Depresi... Tunggu Sebentar`")
    del_u = 0
    del_a = 0

    async for user in show.client.iter_participants(show.chat_id):
        if user.deleted:
            try:
                await show.client(
                    EditBannedRequest(show.chat_id, user.id, BANNED_RIGHTS)
                )
            except ChatAdminRequiredError:
                return await show.edit("`Tidak Memiliki Izin Banned Dalam Grup Ini`")
            except UserAdminInvalidError:
                del_u -= 1
                del_a += 1
            await show.client(EditBannedRequest(show.chat_id, user.id, UNBAN_RIGHTS))
            del_u += 1

    if del_u > 0:
        del_status = f"**Membersihkan** `{del_u}` **Akun Terhapus**"

    if del_a > 0:
        del_status = (
            f"**Membersihkan** `{del_u}` **Akun Terhapus** "
            f"\n`{del_a}` **Akun Admin Yang Terhapus Tidak Dihapus.**"
        )
    await show.edit(del_status)
    await sleep(2)
    await show.delete()

    if BOTLOG:
        await show.client.send_message(
            BOTLOG_CHATID,
            "#MEMBERSIHKAN\n"
            f"**Membersihkan** `{del_u}` **Akun Terhapus!**"
            f"\nGRUP: {show.chat.title}(`{show.chat_id}`)",
        )


@register(outgoing=True, pattern=r"^\.admins$")
async def get_admin(show):
    info = await show.client.get_entity(show.chat_id)
    title = info.title or "Grup Ini"
    mentions = f"<b>👑 Daftar Admin Grup {title}:</b> \n"
    try:
        async for user in show.client.iter_participants(
            show.chat_id, filter=ChannelParticipantsAdmins
        ):
            if not user.deleted:
                link = f'<a href="tg://user?id={user.id}">{user.first_name}</a>'
                mentions += f"\n⚜️ {link}"
            else:
                mentions += f"\nAkun Terhapus <code>{user.id}</code>"
    except ChatAdminRequiredError as err:
        mentions += " " + str(err) + "\n"
    await show.edit(mentions, parse_mode="html")


@register(outgoing=True, groups_only=True, pattern=r"^\.pin( loud|$)")
async def pin(event):
    to_pin = event.reply_to_msg_id
    if not to_pin:
        return await edit_delete(event, "`Reply Pesan untuk Melakukan Pin.`", 30)
    options = event.pattern_match.group(1)
    is_silent = bool(options)
    try:
        await event.client.pin_message(event.chat_id, to_pin, notify=is_silent)
    except BadRequestError:
        return await edit_delete(event, NO_PERM, 5)
    except Exception as e:
        return await edit_delete(event, f"`{e}`", 5)
    await edit_delete(event, "`Pinned Successfully!`", 3)
    if BOTLOG and not event.is_private:
        await event.client.send_message(
            BOTLOG_CHATID,
            f"**#PIN**\
                \n**Berhasil menyematkan pesan di Group**\
                \n👥**CHAT :** {get_display_name(await event.get_chat())}(`{event.chat_id}`)\
                \n📌 **LOUD :** {is_silent}",
        )


@register(outgoing=True, groups_only=True, pattern=r"^\.unpin( all|$)")
async def pin(event):
    to_unpin = event.reply_to_msg_id
    options = (event.pattern_match.group(1)).strip()
    if not to_unpin and options != "all":
        return await edit_delete(
            event,
            "**Reply ke Pesan untuk melepas Pin atau Gunakan** `.unpin all` **untuk melepas pin semua**",
            45,
        )
    try:
        if to_unpin and not options:
            await event.client.unpin_message(event.chat_id, to_unpin)
        elif options == "all":
            await event.client.unpin_message(event.chat_id)
        else:
            return await edit_delete(
                event,
                "**Reply ke Pesan untuk melepas pin atau gunakan** `.unpin all`",
                45,
            )
    except BadRequestError:
        return await edit_delete(event, NO_PERM, 5)
    except Exception as e:
        return await edit_delete(event, f"`{e}`", 5)
    await edit_delete(event, "`Unpinned Successfully!`", 15)
    if BOTLOG and not event.is_private:
        await event.client.send_message(
            BOTLOG_CHATID,
            f"#UNPIN\
                \n**Berhasil melepaskan pin dari Group**\
                \n👥 **CHAT:** {get_display_name(await event.get_chat())}(`{event.chat_id}`)",
        )


@register(outgoing=True, pattern=r"^\.kick(?: |$)(.*)")
async def kick(usr):
    # Admin or creator check
    chat = await usr.get_chat()
    admin = chat.admin_rights
    creator = chat.creator

    # If not admin and not creator, return
    if not admin and not creator:
        return await usr.edit(NO_ADMIN)

    user, reason = await get_user_from_event(usr)
    if not user:
        return await usr.edit("**Tidak Dapat Menemukan Pengguna.**")

    await usr.edit("`Melakukan Kick....`")

    try:
        await usr.client.kick_participant(usr.chat_id, user.id)
        await sleep(0.5)
    except Exception as e:
        return await usr.edit(NO_PERM + f"\n{str(e)}")

    if reason:
        await usr.edit(
            f"[{user.first_name}](tg://user?id={user.id}) **Telah Dikick Dari Grup**\n**Alasan:** `{reason}`"
        )
    else:
        await usr.edit(
            f"[{user.first_name}](tg://user?id={user.id}) **Telah Dikick Dari Grup**"
        )
        await sleep(5)
        await usr.delete()

    if BOTLOG:
        await usr.client.send_message(
            BOTLOG_CHATID,
            "#KICK\n"
            f"PENGGUNA: [{user.first_name}](tg://user?id={user.id})\n"
            f"GRUP: {usr.chat.title}(`{usr.chat_id}`)\n",
        )


@register(outgoing=True, groups_only=True, pattern=r"^\.undlt( -u)?(?: |$)(\d*)?")
async def _iundlt(event):
    catevent = await edit_or_reply(event, "`Searching recent actions...`")
    flag = event.pattern_match.group(1)
    if event.pattern_match.group(2) != "":
        lim = int(event.pattern_match.group(2))
        if lim > 15:
            lim = int(15)
        if lim <= 0:
            lim = int(1)
    else:
        lim = int(5)
    adminlog = await event.client.get_admin_log(
        event.chat_id, limit=lim, edit=False, delete=True
    )
    deleted_msg = f"**Recent {lim} Pesan yang dihapus di grup ini adalah:**"
    if not flag:
        for msg in adminlog:
            ruser = (
                await event.client(GetFullUserRequest(msg.old.from_id.user_id))
            ).user
            _media_type = media_type(msg.old)
            if _media_type is None:
                deleted_msg += f"\n☞ __{msg.old.message}__ **Dikirim oleh** {_format.mentionuser(ruser.first_name ,ruser.id)}"
            else:
                deleted_msg += f"\n☞ __{_media_type}__ **Dikirim oleh** {_format.mentionuser(ruser.first_name ,ruser.id)}"
        await edit_or_reply(catevent, deleted_msg)
    else:
        main_msg = await edit_or_reply(catevent, deleted_msg)
        for msg in adminlog:
            ruser = (
                await event.client(GetFullUserRequest(msg.old.from_id.user_id))
            ).user
            _media_type = media_type(msg.old)
            if _media_type is None:
                await main_msg.reply(
                    f"{msg.old.message}\n**Dikirim oleh** {_format.mentionuser(ruser.first_name ,ruser.id)}"
                )
            else:
                await main_msg.reply(
                    f"{msg.old.message}\n**Dikirim oleh** {_format.mentionuser(ruser.first_name ,ruser.id)}",
                    file=msg.old.media,
                )


async def get_user_from_event(
    event, manevent=None, secondgroup=None, nogroup=False, noedits=False
):
    if manevent is None:
        manevent = event
    if nogroup is False:
        if secondgroup:
            args = event.pattern_match.group(2).split(" ", 1)
        else:
            args = event.pattern_match.group(1).split(" ", 1)
    extra = None
    try:
        if args:
            user = args[0]
            if len(args) > 1:
                extra = "".join(args[1:])
            if user.isnumeric() or (user.startswith("-") and user[1:].isnumeric()):
                user = int(user)
            if event.message.entities:
                probable_user_mention_entity = event.message.entities[0]
                if isinstance(probable_user_mention_entity, MessageEntityMentionName):
                    user_id = probable_user_mention_entity.user_id
                    user_obj = await event.client.get_entity(user_id)
                    return user_obj, extra
            if isinstance(user, int) or user.startswith("@"):
                user_obj = await event.client.get_entity(user)
                return user_obj, extra
    except Exception as e:
        LOGS.error(str(e))
    try:
        if nogroup is False:
            if secondgroup:
                extra = event.pattern_match.group(2)
            else:
                extra = event.pattern_match.group(1)
        if event.is_private:
            user_obj = await event.get_chat()
            return user_obj, extra
        if event.reply_to_msg_id:
            previous_message = await event.get_reply_message()
            if previous_message.from_id is None:
                if not noedits:
                    await edit_delete(
                        manevent, "**ERROR: Dia adalah anonymous admin!**", 60
                    )
                return None, None
            user_obj = await event.client.get_entity(previous_message.sender_id)
            return user_obj, extra
        if not args:
            if not noedits:
                await edit_delete(
                    manevent,
                    "**Berikan Username, user id, atau reply pesan pengguna!**",
                    60,
                )
            return None, None
    except Exception as e:
        LOGS.error(str(e))
    if not noedits:
        await edit_delete(
            manevent, "**ERROR:** __Gagal Mendapatkan history nama orang ini__", 30
        )
    return None, None


async def get_user_from_id(user, event):
    if isinstance(user, str):
        user = int(user)

    try:
        user_obj = await event.client.get_entity(user)
    except (TypeError, ValueError) as err:
        return await event.edit(str(err))

    return user_obj


async def get_userdel_from_event(event):
    args = event.pattern_match.group(1).split(" ", 1)
    extra = None
    if event.reply_to_msg_id and len(args) != 2:
        previous_message = await event.get_reply_message()
        user_obj = await event.client.get_entity(previous_message.from_id)
        extra = event.pattern_match.group(1)
    elif args:
        user = args[0]
        if len(args) == 2:
            extra = args[1]

        if user.isnumeric():
            user = int(user)

        if not user:
            return await event.edit("`Ketik username Atau Balas Ke Pesan Pengguna!`")

        if event.message.entities is not None:
            probable_user_mention_entity = event.message.entities[0]

            if isinstance(probable_user_mention_entity, MessageEntityMentionName):
                user_id = probable_user_mention_entity.user_id
                user_obj = await event.client.get_entity(user_id)
                return user_obj
        try:
            user_obj = await event.client.get_entity(user)
        except (TypeError, ValueError) as err:
            return await event.edit(str(err))

    return user_obj, extra


async def get_userdel_from_id(user, event):
    if isinstance(user, str):
        user = int(user)

    try:
        user_obj = await event.client.get_entity(user)
    except (TypeError, ValueError) as err:
        return await event.edit(str(err))

    return user_obj


def media_type(message):
    if message and message.photo:
        return "Photo"
    if message and message.audio:
        return "Audio"
    if message and message.voice:
        return "Voice"
    if message and message.video_note:
        return "Round Video"
    if message and message.gif:
        return "Gif"
    if message and message.sticker:
        return "Sticker"
    if message and message.video:
        return "Video"
    if message and message.document:
        return "Document"
    return None


CMD_HELP.update(
    {
        "admin": "**Plugin : **`admin`\
        \n\n  •  **Syntax :** `.promote <username/reply> <nama title (optional)>`\
        \n  •  **Function : **Mempromosikan member sebagai admin.\
        \n\n  •  **Syntax :** `.demote <username/balas ke pesan>`\
        \n  •  **Function : **Menurunkan admin sebagai member.\
        \n\n  •  **Syntax :** `.ban <username/balas ke pesan> <alasan (optional)>`\
        \n  •  **Function : **Membanned Pengguna dari grup.\
        \n\n  •  **Syntax :** `.unban <username/reply>`\
        \n  •  **Function : **Unbanned pengguna jadi bisa join grup lagi.\
        \n\n  •  **Syntax :** `.dmute <username/reply> <alasan (optional)>`\
        \n  •  **Function : **Membisukan Seseorang Di Grup dengan menghapus pesannya, Bisa Ke Admin Juga.\
        \n\n  •  **Syntax :** `.undmute <username/reply>`\
        \n  •  **Function : **Membuka bisu orang yang dibisukan.\
        \n  •  **Function : ** Membuka global mute orang yang dibisukan.\
        \n\n  •  **Syntax :** `.setgpic <balas ke gambar>`\
        \n  •  **Function : **Mengganti foto profil grup.\
        \n\n  •  **Syntax :** `.all`\
        \n  •  **Function : **Tag semua member dalam grup.\
        \n\n  •  **Syntax :** `.admins`\
        \n  •  **Function : **Melihat daftar admin di grup.\
    "
    }
)


CMD_HELP.update(
    {
        "zombies": "**Plugin : **`zombies`\
        \n\n  •  **Syntax :** `.zombies`\
        \n  •  **Function : **Untuk mencari akun terhapus dalam grup\
        \n\n  •  **Syntax :** `.zombies clean`\
        \n  •  **Function : **untuk menghapus Akun Terhapus dari grup.\
    "
    }
)


CMD_HELP.update(
    {
        "gmute": "**Plugin : **`gmute`\
        \n\n  •  **Syntax :** `.gmute` <username/reply> <alasan (optional)>\
        \n  •  **Function : **Membisukan Pengguna ke semua grup yang kamu punya sebagai admin.\
        \n\n  •  **Syntax :** `.ungmute` <username/reply>\
    "
    }
)
