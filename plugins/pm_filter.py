# Kanged From @nishn_ea
import asyncio
import re
import ast

from pyrogram.errors.exceptions.bad_request_400 import MediaEmpty, PhotoInvalidDimensions, WebpageMediaEmpty
from Script import script
import pyrogram
from database.connections_mdb import active_connection, all_connections, delete_connection, if_active, make_active, \
    make_inactive
from info import ADMINS, AUTH_CHANNEL, AUTH_USERS, CUSTOM_FILE_CAPTION, AUTH_GROUPS, DELETE_TIME, P_TTI_SHOW_OFF, IMDB, REDIRECT_TO, \
    SINGLE_BUTTON, SPELL_CHECK_REPLY, IMDB_TEMPLATE, START_IMAGE_URL, UNAUTHORIZED_CALLBACK_TEXT, redirected_env
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram import Client, filters
from pyrogram.errors import FloodWait, UserIsBlocked, MessageNotModified, PeerIdInvalid
from utils import get_size, is_subscribed, get_poster, search_gagala, temp, get_settings, save_group_settings
from database.users_chats_db import db
from database.ia_filterdb import Media, get_file_details, get_search_results
from database.filters_mdb import (
    del_all,
    find_filter,
    get_filters,
)
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)

BUTTONS = {}
SPELL_CHECK = {}


@Client.on_message((filters.group | filters.private) & filters.text & ~filters.edited & filters.incoming)
async def give_filter(client, message):
    k = await manual_filters(client, message)
    if k == False:
        await auto_filter(client, message)


@Client.on_callback_query(filters.regex(r"^next"))
async def next_page(bot, query):
    ident, req, key, offset = query.data.split("_")
    if int(req) not in [query.from_user.id, 0]:
        return await query.answer(UNAUTHORIZED_CALLBACK_TEXT, show_alert=True)
    try:
        offset = int(offset)
    except:
        offset = 0
    search = BUTTONS.get(key)
    if not search:
        await query.answer("You Are Using My Old Messages🥲,Try Asking Again 🤠", show_alert=True)#Techno Mindz
        return

    files, n_offset, total = await get_search_results(search, offset=offset, filter=True)
    try:
        n_offset = int(n_offset)
    except:
        n_offset = 0

    if not files:
        return
    settings = await get_settings(query.message.chat.id)
    pre = 'Chat' if settings['redirect_to'] == 'Chat' else 'files'

    if settings['button']:
        btn = [
            [
                InlineKeyboardButton(
                    text=f"📂 [{get_size(file.file_size)}] {file.file_name}", callback_data=f'{pre}#{file.file_id}#{query.from_user.id}'
                )
            ] 
            for file in files
        ]
    else:
        btn = [        
            [
                InlineKeyboardButton(
                    text=f"{file.file_name}", callback_data=f'{pre}#{file.file_id}#{query.from_user.id}'
                ),
                InlineKeyboardButton(
                    text=f"📂[{get_size(file.file_size)}]",
                    callback_data=f'{pre}_#{file.file_id}#{query.from_user.id}',
                )
            ] 
            for file in files
        ]

    btn.insert(0,
            [
                InlineKeyboardButton("🎭 ᴍᴏᴠɪᴇs", url="https://t.me/CinemaVeed"),
                InlineKeyboardButton("📢 ᴄʜᴀɴɴᴇʟ", url="https://t.me/CinemaVeedMovies")
            ])

    btn.insert(0, [
        InlineKeyboardButton("📥 ʜᴏᴡ ᴛᴏ ᴅᴏᴡɴʟᴏᴀᴅ 📥", url="https://t.me/tmmainchannel/4")#Vintage Botz
    ])

    if 0 < offset <= 10:
        off_set = 0
    elif offset == 0:
        off_set = None
    else:
        off_set = offset - 10
    if n_offset == 0:
        btn.append(
            [InlineKeyboardButton("⏪ ʙᴀᴄᴋ", callback_data=f"next_{req}_{key}_{off_set}"),
             InlineKeyboardButton(f"📃 ᴘᴀɢᴇs {round(int(offset) / 10) + 1} / {round(total / 10)}",
                                  callback_data="pages")]
        )
    elif off_set is None:
        btn.append(
            [InlineKeyboardButton(f"🗓 {round(int(offset) / 10) + 1} / {round(total / 10)}", callback_data="pages"),
             InlineKeyboardButton("ɴᴇxᴛ ⏩", callback_data=f"next_{req}_{key}_{n_offset}")])#Techno Mindz
    else:
        btn.append(
            [
                InlineKeyboardButton("⏪ ʙᴀᴄᴋ", callback_data=f"next_{req}_{key}_{off_set}"),
                InlineKeyboardButton(f"🗓 {round(int(offset) / 10) + 1} / {round(total / 10)}", callback_data="pages"),
                InlineKeyboardButton("ɴᴇxᴛ ⏩", callback_data=f"next_{req}_{key}_{n_offset}")
            ],
        )
    try:
        await query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup(btn)
        )
    except MessageNotModified:
        pass
    await query.answer()


@Client.on_callback_query(filters.regex(r"^spolling"))
async def advantage_spoll_choker(bot, query):
    _, user, movie_ = query.data.split('#')
    if int(user) != 0 and query.from_user.id != int(user):
        return await query.answer("Check Your Own Request 😡 ", show_alert=True)
    if movie_ == "close_spellcheck":
        return await query.message.delete()
    movies = SPELL_CHECK.get(query.message.reply_to_message.message_id)
    if not movies:
        return await query.answer("You Are Using My Old Messages🥲,Try Asking Again 🤠 ", show_alert=True)#Techno Mindz
    movie = movies[(int(movie_))]
    await query.answer('just a second...searching....🧐 ')#TechnoMindz
    k = await manual_filters(bot, query.message, text=movie)
    if k == False:
        files, offset, total_results = await get_search_results(movie, offset=0, filter=True)
        if files:
            k = (movie, files, offset, total_results)
            await auto_filter(bot, query, k)
        else:
            one_button = InlineKeyboardMarkup([[InlineKeyboardButton("🥲 𝗢𝗪𝗡𝗘𝗥 🔥", url="https://t.me/TechnoKillerBot"), InlineKeyboardButton("🤕 𝗚𝗢𝗢𝗚𝗟𝗘 🤒", url="https://www.google.com/")]])
            k = await msg.reply_video(video="https://telegra.ph//file/d90256b1575c7aaadccc5.mp4", caption="Hey, 𝐒𝐨𝐫𝐫𝐲, 𝐍𝐨 𝐌𝐨𝐯𝐢𝐞/𝐒𝐞𝐫𝐢𝐞𝐬 𝐑𝐞𝐥𝐚𝐭𝐞𝐝 𝐓𝐨 𝐓𝐡𝐞 𝐆𝐢𝐯𝐞𝐧 𝐖𝐨𝐫𝐝 𝐖𝐚𝐬 𝐅𝐨𝐮𝐧𝐝 🥺\n\n𝙿𝚘𝚜𝚜𝚒𝚋𝚕𝚎 𝙲𝚊𝚞𝚜𝚎𝚜 : 🤔\n\n⭕️ 𝐍𝐨𝐭 𝐑𝐞𝐥𝐞𝐚𝐬𝐞𝐝 𝐘𝐞𝐭\n⭕️ 𝐈𝐧𝐜𝐨𝐫𝐫𝐞𝐜𝐭 𝐒𝐩𝐞𝐥𝐥𝐢𝐧𝐠\n⭕ 𝐍𝐨𝐭 𝐔𝐩𝐥𝐨𝐚𝐝𝐞𝐝 𝐁𝐲 𝐎𝐰𝐧𝐞𝐫\n\n👉Contact To My Owner👇", reply_markup = one_button)#Spell check reply
            await asyncio.sleep(20)
            await k.delete()
            await msg.delete()


@Client.on_callback_query()
async def cb_handler(client: Client, query: CallbackQuery):
    if query.data == "close_data":
        await query.message.delete()
    elif query.data == "delallconfirm":
        userid = query.from_user.id
        chat_type = query.message.chat.type

        if chat_type == "private":
            grpid = await active_connection(str(userid))
            if grpid is not None:
                grp_id = grpid
                try:
                    chat = await client.get_chat(grpid)
                    title = chat.title
                except:
                    await query.message.edit_text("Make sure I'm present in your group!! 🥴 \n\n@TmMainChannel", quote=True)
                    return await query.answer('⏳Loading...')
            else:
                await query.message.edit_text(
                    "I'm not connected to any groups!\nCheck /connections or connect to any groups 🥴 ",
                    quote=True
                )
                return await query.answer('⏳Loading...')

        elif chat_type in ["group", "supergroup"]:
            grp_id = query.message.chat.id
            title = query.message.chat.title

        else:
            return await query.answer('𝗌𝖺𝗇𝗍𝗁𝗈𝗌𝗁𝖺𝗆 𝖺𝗅𝗅𝖾')

        st = await client.get_chat_member(grp_id, userid)
        if (st.status == "creator") or (str(userid) in ADMINS):
            await del_all(query.message, grp_id, title)
        else:
            await query.answer("You need to be Group Owner or an Auth User to do that! 😠 \n\n@TmMainChannel", show_alert=True)
    elif query.data == "delallcancel":
        userid = query.from_user.id
        chat_type = query.message.chat.type

        if chat_type == "private":
            await query.message.reply_to_message.delete()
            await query.message.delete()

        elif chat_type in ["group", "supergroup"]:
            grp_id = query.message.chat.id
            st = await client.get_chat_member(grp_id, userid)
            if (st.status == "creator") or (str(userid) in ADMINS):
                await query.message.delete()
                try:
                    await query.message.reply_to_message.delete()
                except:
                    pass
            else:
                await query.answer("That's not for you!! 🤐 ", show_alert=True)
    elif "groupcb" in query.data:
        await query.answer()

        group_id = query.data.split(":")[1]

        act = query.data.split(":")[2]
        hr = await client.get_chat(int(group_id))
        title = hr.title
        user_id = query.from_user.id

        if act == "":
            stat = "CONNECT"
            cb = "connectcb"
        else:
            stat = "DISCONNECT"
            cb = "disconnect"

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(f"{stat}", callback_data=f"{cb}:{group_id}"),
             InlineKeyboardButton("🗑️ ᴅᴇʟᴇᴛᴇ", callback_data=f"deletecb:{group_id}")],
            [InlineKeyboardButton("⏮️ ʙᴀᴄᴋ", callback_data="backcb")]
        ])

        await query.message.edit_text(
            f"Group Name : **{title}**\nGroup ID : `{group_id}`",
            reply_markup=keyboard,
            parse_mode="md"
        )
        return await query.answer('⏳Loading...')
    elif "connectcb" in query.data:
        await query.answer()

        group_id = query.data.split(":")[1]

        hr = await client.get_chat(int(group_id))

        title = hr.title

        user_id = query.from_user.id

        mkact = await make_active(str(user_id), str(group_id))

        if mkact:
            await query.message.edit_text(
                f"Connected to **{title}**",
                parse_mode="md"
            )
        else:
            await query.message.edit_text('Some error occurred!!', parse_mode="md")
        return await query.answer('⏳Loading...')
    elif "disconnect" in query.data:
        await query.answer()

        group_id = query.data.split(":")[1]

        hr = await client.get_chat(int(group_id))

        title = hr.title
        user_id = query.from_user.id

        mkinact = await make_inactive(str(user_id))

        if mkinact:
            await query.message.edit_text(
                f"Disconnected from **{title}**",
                parse_mode="md"
            )
        else:
            await query.message.edit_text(
                f"Some error occurred!!",
                parse_mode="md"
            )
        return await query.answer('⏳Loading...')
    elif "deletecb" in query.data:
        await query.answer()

        user_id = query.from_user.id
        group_id = query.data.split(":")[1]

        delcon = await delete_connection(str(user_id), str(group_id))

        if delcon:
            await query.message.edit_text(
                "Successfully deleted connection"
            )
        else:
            await query.message.edit_text(
                f"Some error occurred!!",
                parse_mode="md"
            )
        return await query.answer('⏳Loading...')
    elif query.data == "backcb":
        await query.answer()

        userid = query.from_user.id

        groupids = await all_connections(str(userid))
        if groupids is None:
            await query.message.edit_text(
                "There are no active connections!! Connect to some groups first.",
            )
            return await query.answer('⏳Loading...')
        buttons = []
        for groupid in groupids:
            try:
                ttl = await client.get_chat(int(groupid))
                title = ttl.title
                active = await if_active(str(userid), str(groupid))
                act = " - ACTIVE" if active else ""
                buttons.append(
                    [
                        InlineKeyboardButton(
                            text=f"{title}{act}", callback_data=f"groupcb:{groupid}:{act}"
                        )
                    ]
                )
            except:
                pass
        if buttons:
            await query.message.edit_text(
                "Your connected group details ;\n\n",
                reply_markup=InlineKeyboardMarkup(buttons)
            )
    elif "alertmessage" in query.data:
        grp_id = query.message.chat.id
        i = query.data.split(":")[1]
        keyword = query.data.split(":")[2]
        reply_text, btn, alerts, fileid = await find_filter(grp_id, keyword)
        if alerts is not None:
            alerts = ast.literal_eval(alerts)
            alert = alerts[int(i)]
            alert = alert.replace("\\n", "\n").replace("\\t", "\t")
            await query.answer(alert, show_alert=True)
    if query.data.startswith("file"):
        ident, file_id, rid = query.data.split("#")

        if int(rid) not in [query.from_user.id, 0]:
            return await query.answer(UNAUTHORIZED_CALLBACK_TEXT, show_alert=True)

        files_ = await get_file_details(file_id)
        if not files_:
            return await query.answer('No such file exist.')#After joining the forecesub (Refreshing) 
        files = files_[0]
        title = files.file_name
        size = get_size(files.file_size)
        mention = query.from_user.mention
        f_caption = files.caption
        settings = await get_settings(query.message.chat.id)
        if CUSTOM_FILE_CAPTION:
            try:
                f_caption = CUSTOM_FILE_CAPTION.format(file_name='' if title is None else title,
                                                       file_size='' if size is None else size,
                                                       file_caption='' if f_caption is None else f_caption)                                                      
            except Exception as e:
                logger.exception(e)
            f_caption = f_caption
        if f_caption is None:
            f_caption = f"{files.file_name}"

        try:
            if AUTH_CHANNEL and not await is_subscribed(client, query):
                await query.answer(url=f"https://t.me/{temp.U_NAME}?start={ident}_{file_id}")
                return
            elif settings['botpm']:
                await query.answer(url=f"https://t.me/{temp.U_NAME}?start={ident}_{file_id}")
                return
            else:
                await client.send_cached_media(
                    chat_id=query.from_user.id,
                    file_id=file_id,
                    caption=f_caption,
                    protect_content=True if ident == "filep" else False 
                )
                await query.answer('𝖢𝗁𝖾𝖼𝗄 𝗆𝗒 𝗉𝗆 🤠 , I have sent you 😉', show_alert=True)#if Pm Mode ON 
        except UserIsBlocked:
            await query.answer('Unblock the bot mahn ! 🤬🤬 ', show_alert=True)
        except PeerIdInvalid:
            await query.answer(url=f"https://t.me/{temp.U_NAME}?start={ident}_{file_id}")
        except Exception as e:
            await query.answer(url=f"https://t.me/{temp.U_NAME}?start={ident}_{file_id}")
    
    elif query.data.startswith("Chat"):
        ident, file_id, rid = query.data.split("#")

        if int(rid) not in [query.from_user.id, 0]:
            return await query.answer(UNAUTHORIZED_CALLBACK_TEXT, show_alert=True)

        files_ = await get_file_details(file_id)
        if not files_:
            return await query.answer('No such file exist.')
        files = files_[0]
        title = files.file_name
        size = get_size(files.file_size)
        mention = query.from_user.mention
        f_caption = files.caption
        settings = await get_settings(query.message.chat.id)
        if CUSTOM_FILE_CAPTION:
            try:
                f_caption = CUSTOM_FILE_CAPTION.format(file_name='' if title is None else title,
                                                       file_size='' if size is None else size,
                                                       file_caption='' if f_caption is None else f_caption)
            except Exception as e:
                logger.exception(e)
            f_caption = f_caption
            size = size
            mention = mention
        if f_caption is None:
            f_caption = f"{files.file_name}"
            size = f"{files.file_size}"
            mention = f"{query.from_user.mention}"
        try:
            invite_link = await client.create_chat_invite_link(int(AUTH_CHANNEL))
        except ChatAdminRequired:
            logger.error("Make sure I'm admin in Forcesub channel")
            return
        try:
            msg = await client.send_cached_media(
                chat_id=AUTH_CHANNEL,
                file_id=file_id,
                caption=f'<b>Hi 👋 {query.from_user.mention} \n☵☵☵☵☵☵☵☵☵☵☵☵☵\n\n</b>\n 📁 ➜ [VBOTz] <code> {title}</code>\n\n⚠️ This file will be deleted from here within 5 minute as it has copyright ... !!!\n\nകോപ്പിറൈറ്റ് ഉള്ളതുകൊണ്ട് ഫയൽ 5 മിനിറ്റിനുള്ളിൽ ഇവിടെനിന്നും ഡിലീറ്റ് ആകുന്നതാണ് അതുകൊണ്ട് ഇവിടെ നിന്നും മറ്റെവിടെക്കെങ്കിലും മാറ്റിയതിന് ശേഷം ഡൗൺലോഡ് ചെയ്യുക!\n\n⚡Requested Group {query.message.chat.titl',#Custom Caption
                protect_content=True if ident == "filep" else False 
            )
            msg1 = await query.message.reply(
                f'<b> Hi 👋 {query.from_user.mention} </b>😍\n\n<b>📫 Your File is Ready</b>\n\n'           
                f'<b>🦋 Fɪʟᴇ Nᴀᴍᴇ</b> : [@TmMainChannel]<code> {title}</code>\n\n'              
                f'<b>⚙️ Fɪʟᴇ Sɪᴢᴇ</b> : <b>{size}</b>',
                True,
                'html',
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton('🦋 𝐃𝐎𝐖𝐍𝐋𝐎𝐀𝐃 𝐋𝐈𝐍𝐊 🦋', url = msg.link)
                        ],                       
                        [
                            InlineKeyboardButton("✧🎀𝐂𝐀𝐍'𝐓 𝐀𝐂𝐂𝐄𝐒𝐒❓ 𝐂𝐋𝐈𝐂𝐊 𝐇𝐄𝐑𝐄🎀✧", url=f'https://t.me/+AhuGzoZgPdEzMTBl')#Add Your url where the file need to come
                        ]
                    ]
                )
            )
            await query.answer('𓂀 ℂℍ𝔼ℂ𝕂 𝕀ℕ 𝕋ℍ𝔼 ℂℍ𝔸𝕋 𓂀',)
            await asyncio.sleep(300)
            await msg1.delete()
            await msg.delete()
            del msg1, msg
        except Exception as e:
            logger.exception(e, exc_info=True)
            await query.answer(f"Encountering Issues", True)

    elif query.data.startswith("checksub"):
        if AUTH_CHANNEL and not await is_subscribed(client, query):
            await query.answer("🐐 🎀 𝐼 𝐿𝒾𝓀𝑒 𝒴💗𝓊𝓇 𝒮𝓂𝒶𝓇𝓉𝓃𝑒𝓈𝓈, 𝐵𝓊𝓉 𝒟☯𝓃'𝓉 𝐵𝑒 🍬𝓋𝑒𝓇𝓈𝓂𝒶𝓇𝓉 🎀 🐐", show_alert=True)
            return
        ident, file_id = query.data.split("#")
        files_ = await get_file_details(file_id)
        if not files_:
            return await query.answer('No such file exist.')
        files = files_[0]
        title = files.file_name
        size = get_size(files.file_size)
        mention = query.from_user.mention
        f_caption = files.caption
        if CUSTOM_FILE_CAPTION:
            try:
                f_caption = CUSTOM_FILE_CAPTION.format(file_name='' if title is None else title,
                                                       file_size='' if size is None else size,
                                                       file_caption='' if f_caption is None else f_caption)
            except Exception as e:
                logger.exception(e)
                f_caption = f_caption
                size = size
                mention = mention
        if f_caption is None:
            f_caption = f"{title}"
        if size is None:
            size = f"{size}"
        if mention is None:
            mention = f"{mention}"

        await query.answer()
        await client.send_cached_media(
            chat_id=query.from_user.id,
            file_id=file_id,
            caption=f_caption,
            protect_content=True if ident == 'checksubp' else False
        )
    elif query.data == "pages":
        await query.answer()
        
    elif query.data == "start":
        await query.message.delete()
        await query.message.reply_sticker(
            'CAACAgIAAxkBAALfhWKhyQAB6dM3e7xjAzNaNkDcJvRusAAChxUAAj0PUEnem2b91sejvx4E',
            reply_markup=InlineKeyboardMarkup(
                [[
                    InlineKeyboardButton('🎀𝑀𝒜𝐼𝒩 𝒞𝐻𝒜𝒩𝒩𝐸𝐿🎀', url='https://t.me/Tmmainchannel')
                ],[
                    InlineKeyboardButton('𓂀 𝕐𝕆𝕌𝕋𝕌𝔹𝔼 𓂀', url='https://www.youtube.com/c/TechnoMindz'),
                    InlineKeyboardButton('📢 𝓒𝓗𝓐𝓣𝓣𝓘𝓝𝓖', url='https://t.me/Technomindzchat')
                ],[
                    InlineKeyboardButton('🔍 𝒮𝐸𝒜𝑅𝒞𝐻', switch_inline_query_current_chat='')
                ],[
                    InlineKeyboardButton('𝐻𝐸𝐿𝒫', callback_data='help'),
                    InlineKeyboardButton('😊 𝓐𝓑𝓞𝓤𝓣', callback_data='about')
                ],[
                    InlineKeyboardButton('❌𝐂𝐋𝐎𝐒𝐄❌', callback_data='close')
                ]]
            )
        )
        await query.answer('Lᴏᴀᴅɪɴɢ..........')

        
    elif query.data == "help":
        await query.message.delete()
        await query.message.reply_sticker(
            'CAACAgIAAxkBAALfAAFioLs6ludC4125M0m5V9LqfQY6jQAC_RkAAmzaUUlkoYIx4TqiCh4E',
            reply_markup=InlineKeyboardMarkup(
                [[
            InlineKeyboardButton('ғᴇᴀᴛᴜᴇs✨', callback_data='featuresS'),
            InlineKeyboardButton('ᴛᴏᴏʟs🛠', callback_data='toolsjns')
            ],[     
            InlineKeyboardButton('ミ★𝘉𝘈𝘊𝘒★彡', callback_data='start'),
            InlineKeyboardButton('ʜᴏᴍᴇ🏕', callback_data='start'),
            InlineKeyboardButton('❌𝐂𝐋𝐎𝐒𝐄❌', callback_data='close_data')
            ]]
            )
        )
        await query.answer('Lᴏᴀᴅɪɴɢ..........')

    elif query.data == "about":
        await query.message.delete()
        await query.message.reply_sticker(
            'CAACAgIAAxkBAALfA2Kgu14WszCBeoISI35WcCyUAesiAALDEwACbegQSoZjwH3h3Lo0HgQ',
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton('👉𝐎𝐏𝐄𝐍👈', callback_data='about_menu1')
                    ],
                    [
                        InlineKeyboardButton('ミ★𝘉𝘈𝘊𝘒★彡', callback_data='start'),
                        InlineKeyboardButton('❌𝐂𝐋𝐎𝐒𝐄❌', callback_data='close')
                    ]
                ]
            )
        )
        await query.answer('ᴀʙᴏᴜᴛ.......')

    elif query.data == "about_menu1":
        await query.message.delete()
        await query.message.reply_sticker(
            'CAACAgIAAxkBAALfCGKgu_iyutqTf1v25x4ZW9QfoxrLAAKgFwAC37QgSSCArCK7IMbJHgQ',
            reply_markup=InlineKeyboardMarkup(
                [[
                    InlineKeyboardButton('👑 ᴅᴇᴠ 👑', callback_data='dev_dk'),
                ],
                [
                    InlineKeyboardButton('⚙️ Mᴀɪɴᴛᴀɪɴᴇᴅ Bʏ ⚙️', callback_data='jns_maintains')
                ],
                [
                    InlineKeyboardButton('❤️‍🔥ᴛᴇᴄʜɴᴏ ᴍɪɴᴅᴢ❤️‍🔥', url=f'https://t.me/TmMainChannel'),
                    InlineKeyboardButton('💾ᴍᴏᴠɪᴇs💾', url=f'https://t.me/Technomoviescollection')
                ],
                [
                    InlineKeyboardButton('ミ★𝘉𝘈𝘊𝘒★彡', callback_data='start')
                ]
                ]
            )
        )
        await query.answer('ᴀʙᴏᴜᴛ.......')
        
    elif query.data == "dev_dk":
        await query.message.delete()
        await query.message.reply_sticker(
            'CAACAgUAAxkBAAEBGXJii6mtRyOdw_xwn73fNjpiO-EqcwACjAYAAlJuWVZyrxMDtBmVryQE',
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton('🎈𝐁𝐎𝐒𝐒🎈', url=f'https://t.me/technomindzyt'),
                        InlineKeyboardButton('📯𝐒𝐔𝐏𝐏𝐎𝐑𝐓📯', url=f'https://t.me/technomindzchat')
                    ],
                    [
                        InlineKeyboardButton('ミ★𝘉𝘈𝘊𝘒★彡', callback_data='about_menu1'),
                        InlineKeyboardButton('❌𝐂𝐋𝐎𝐒𝐄❌', callback_data='close')
                    ]
                ]
            )
        )   
    elif query.data == "dev_all1":
        await query.message.delete()
        await query.message.reply_sticker(
            'CAACAgUAAxkBAAEBH0hinPbKkK2Q1dNeMLOBxzDTaxk7XAAC5AIAAgX8WFYr5CVXDF0kuCQE',
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton('𓂀 𝕆𝕎ℕ𝔼ℝ 𓂀', url=f'http://t.me/TECHNOMINDZYT')
                    ],
                    [
                        InlineKeyboardButton('🤠DEVS🤠', url=f'https://t.me/TECHNOMINDZCHAT'),
                        InlineKeyboardButton('🤠ᴛᴇᴄʜɴᴏ ᴍɪɴᴅᴢ🤠', url=f'https://t.me/Tmmainchannel')
                    ],
                    [
                        InlineKeyboardButton('ミ★𝘉𝘈𝘊𝘒★彡', callback_data='about_menu1'),
                        InlineKeyboardButton('❌𝐂𝐋𝐎𝐒𝐄❌', callback_data='close')
                    ]
                ]
            )
        ) 
        
        
    elif query.data == "jns_maintains":
        await query.message.delete()
        await query.message.reply_sticker(
            'CAACAgIAAxkBAALdzGKbdOHcsMpnikpRm99pIAH_U0tYAALoFgAC_YsQStr2Fln0t1FAHgQ',
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton('🎀𝑀𝒜𝐼𝒩 𝒞𝐻𝒜𝒩𝒩𝐸𝐿🎀', url='https://t.me/Tmmainchannel')
                    ],
                    [
                        InlineKeyboardButton('𓂀𝕄𝕆𝕍𝕀𝔼𝕊𓂀', url='https://t.me/technomoviescollection'),
                        InlineKeyboardButton('📢𝓒𝓗𝓐𝓣𝓣𝓘𝓝𝓖', url='https://t.me/Technomindzchat')
                    ],
                    [
                        InlineKeyboardButton('𓂀 𝕐𝕆𝕌𝕋𝕌𝔹𝔼 𓂀', url='https://www.youtube.com/c/TechnoMindz')
                    ],
                    [
                        InlineKeyboardButton('ミ★𝘉𝘈𝘊𝘒★彡', callback_data='about_menu1'),
                        InlineKeyboardButton('❌𝐂𝐋𝐎𝐒𝐄❌', callback_data='close')
                    ]
                ]
            )
        ) 
    elif query.data == "bros":
        await query.message.delete()
        await query.message.reply_sticker(
            'CAACAgUAAxkBAAEBGbZii8_lHTfWP78_U9HRRldy7EyA-QACKAUAAtE4WFQTdpC1zu7ZOSQE',
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton('TM Elsa Bot', url=f'http://t.me/tmelsarobot')
                    ],
                    [
                        InlineKeyboardButton('TM Owner Bot', url=f'https://t.me/technokillerbot')
                    ],                    
                    [
                        InlineKeyboardButton('ミ★𝘉𝘈𝘊𝘒★彡', callback_data='jns_maintains'),
                        InlineKeyboardButton('❌𝐂𝐋𝐎𝐒𝐄❌', callback_data='close')
                    ]
                ]
            )
        ) 
    elif query.data == "featuresS":
        await query.message.delete()
        await query.message.reply_sticker(
            'CAACAgIAAxkBAALfNmKgx1wwiYezOlyTmo9JzaU0xgFDAAICFQACOsFQSbdMkgm_6KgTHgQ',
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton('⏳ғɪʟᴛᴇʀ', callback_data='filter1'),
                        InlineKeyboardButton('ᴄᴏɴɴᴇᴄᴛɪᴏɴ🧩', callback_data='coct')
                    ],
                    [
                        InlineKeyboardButton('🤐ᴍᴜᴛᴇ', callback_data='mute'),
                        InlineKeyboardButton('ʙᴀɴ🙅🏻‍♀️', callback_data='ban'),
                        InlineKeyboardButton('🔮 𝓢𝓣𝓐𝓣𝓤𝓢', callback_data='stats')
                    ],
                    [
                        InlineKeyboardButton('ミ★𝘉𝘈𝘊𝘒★彡', callback_data='help'),
                        InlineKeyboardButton('❌𝐂𝐋𝐎𝐒𝐄❌', callback_data='close')
                    ]
                ]
            )
        )
        await query.answer('ᴍᴀᴊᴏʀ ғᴇᴀᴛᴜʀᴇs..')
        
    elif query.data == "filter1":
        await query.message.delete()
        await query.message.reply_sticker(
            'CAACAgIAAxkBAALfOWKgx9EcExh87ecSmF1jFmUMuMv7AAJiFQACIqPBSfvS-zntbkh-HgQ',
            reply_markup=InlineKeyboardMarkup(
                [[
            InlineKeyboardButton('𝑀𝒜𝒩𝒩𝒰𝒜𝐿 𝐹𝐼𝐿𝒯𝐸𝑅', callback_data='manuelfilter'),
            InlineKeyboardButton('𝒜𝒰𝒯𝒪 𝐹𝐼𝐿𝒯𝐸𝑅', callback_data='autofilter')
            ],[
            InlineKeyboardButton('彡[ᴄᴏɴɴᴇᴄᴛɪᴏɴꜱ]彡', callback_data='coct'),
            InlineKeyboardButton('𝓔𝓧𝓣𝓡𝓐𝓢', callback_data='extra')
            ],[
            InlineKeyboardButton('🏠 𝓗𝓞𝓜𝓔', callback_data='featuresS'),
            InlineKeyboardButton('🔮 𝓢𝓣𝓐𝓣𝓤𝓢', callback_data='stats')
            ],[
            InlineKeyboardButton('❌𝐂𝐋𝐎𝐒𝐄❌', callback_data='close_data')
        ]]
            )
        )
        await query.answer('ᴡᴇ ʜᴀᴠᴇ 2 ғɪʟᴛᴇʀ ᴏᴘᴛɪᴏɴs..')
        
    elif query.data == "manual":
        buttons = [[
            InlineKeyboardButton('ミ★𝘉𝘈𝘊𝘒★彡', callback_data='filter1'),
            InlineKeyboardButton('⏹️ Buttons', callback_data='button')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.delete()
        await query.message.reply(
            text=script.MANUELFILTER_TXT.format(temp.B_NAME),
            reply_markup=reply_markup,
            parse_mode='html',
            disable_web_page_preview=True
        )
        await query.answer('ᴍᴀɴᴜᴀʟ ғɪʟᴛᴇʀ ᴛᴏᴏʟs.......')

    elif query.data == "button":
        buttons = [[
            InlineKeyboardButton('ミ★𝘉𝘈𝘊𝘒★彡', callback_data='manual')
        ]]
        r=await query.message.reply_text('▣▣▢▢▢▢')
        a=await r.edit('▣▣▣▢▢▢')
        v=await a.edit('▣▣▣▣▢▢')
        i=await v.edit('▣▣▣▣▣▢')
        n=await i.edit('▣▣▣▣▣▣')
        await asyncio.sleep(1)
        await n.delete()
        await query.answer("Loading Buttons Module...")
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.BUTTON_TXT,
            reply_markup=reply_markup,
            parse_mode='html'
        )
      
    elif query.data == "autofilter":
        buttons = [[
            InlineKeyboardButton('ミ★𝘉𝘈𝘊𝘒★彡', callback_data='filter1')
        ]]
        r=await query.message.reply_text('▣▣▢▢▢▢')
        a=await r.edit('▣▣▣▢▢▢')
        v=await a.edit('▣▣▣▣▢▢')
        i=await v.edit('▣▣▣▣▣▢')
        n=await i.edit('▣▣▣▣▣▣')
        await asyncio.sleep(1)
        await n.delete()
        await query.answer("Loading AutoFilter...")
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.AUTOFILTER_TXT,
            reply_markup=reply_markup,
            parse_mode='html'
        )
        
    elif query.data == "stats":
        await query.answer("Let Me Check Out My Status 😌")
        buttons = [[
            InlineKeyboardButton('ミ★𝘉𝘈𝘊𝘒★彡', callback_data='featuresS'),
            InlineKeyboardButton('♻️ʀᴇғʀᴇsʜ♻️', callback_data='rfrsh')
        ]]
        r=await query.message.reply_text('▣▣▢▢▢▢')
        a=await r.edit('▣▣▣▢▢▢')
        v=await a.edit('▣▣▣▣▢▢')
        i=await v.edit('▣▣▣▣▣▢')
        n=await i.edit('▣▣▣▣▣▣')
        await asyncio.sleep(1)
        await n.delete()
        await query.answer("Checking My Status...")
        reply_markup = InlineKeyboardMarkup(buttons)
        total = await Media.count_documents()
        users = await db.total_users_count()
        chats = await db.total_chat_count()
        monsize = await db.get_db_size()
        free = 536870912 - monsize
        monsize = get_size(monsize)
        free = get_size(free)
        await query.message.delete()
        await query.message.reply(
            text=script.STATUS_TXT.format(total, users, chats, monsize, free),
            reply_markup=reply_markup,
            parse_mode='html'
        )

    elif query.data == "rfrsh":
        await query.answer("ᴀɢᴀɪɴ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ᴄʜᴇᴄᴋ 😰")
        buttons = [[
            InlineKeyboardButton('ミ★𝘉𝘈𝘊𝘒★彡', callback_data='featuresS'),
            InlineKeyboardButton('♻️ʀᴇғʀᴇsʜ♻️', callback_data='rfrsh')
        ]]
        r=await query.message.reply_text('▣▣▢▢▢▢')
        a=await r.edit('▣▣▣▢▢▢')
        v=await a.edit('▣▣▣▣▢▢')
        i=await v.edit('▣▣▣▣▣▢')
        n=await i.edit('▣▣▣▣▣▣')
        await asyncio.sleep(1)
        await n.delete()
        await query.answer("Loading...")
        reply_markup = InlineKeyboardMarkup(buttons)
        total = await Media.count_documents()
        users = await db.total_users_count()
        chats = await db.total_chat_count()
        monsize = await db.get_db_size()
        free = 536870912 - monsize
        monsize = get_size(monsize)
        free = get_size(free)
        await query.message.edit_text(
            text=script.STATUS_rfrsh_TXT.format(total, users, chats, monsize, free),
            reply_markup=reply_markup,
            parse_mode='html'
      )
    elif query.data == "mute":
        await query.message.delete()
        await query.message.reply_sticker(
            'CAACAgIAAxkBAALfPGKgyZ0zLniiuZXy0_I-8vBgty4ZAAJiFQACfZpQSbTG3o8XjtAyHgQ',
            reply_markup=InlineKeyboardMarkup(
                [[
            InlineKeyboardButton('🎀𝒟𝐸𝒯𝒜𝐼𝐿𝒮🎀', callback_data='mute_inside')
            ],[
            InlineKeyboardButton('★彡[ʙᴀᴄᴋ]彡★', callback_data='featuresS'),
            InlineKeyboardButton('❌𝐂𝐋𝐎𝐒𝐄❌', callback_data='close_data')
        ]]
            )
        )
        await query.answer('ᴍᴜᴛᴇ ᴏᴘᴛɪᴏɴs....')
        
    elif query.data == "mute_inside":
        buttons = [[
            InlineKeyboardButton('ミ★𝘉𝘈𝘊𝘒★彡', callback_data='featuresS')
        ]]
        r=await query.message.reply_text('▣▣▢▢▢▢')
        a=await r.edit('▣▣▣▢▢▢')
        v=await a.edit('▣▣▣▣▢▢')
        i=await v.edit('▣▣▣▣▣▢')
        n=await i.edit('▣▣▣▣▣▣')
        await asyncio.sleep(1)
        await n.delete()
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.delete()
        await query.message.reply(
            text=script.MUTE_TXT,
            reply_markup=reply_markup,
            parse_mode='html',
            disable_web_page_preview=True
        )
        await query.answer('ᴏᴘᴇɴɪɴɢ ᴍᴜᴛᴇ ʜᴇʟᴘ....')
    
    elif query.data == "ban":
        await query.message.delete()
        await query.message.reply_sticker(
            'CAACAgIAAxkBAALfP2Kgyb9QEon1SefCbXdHwY8kOr6YAAIKFQACX_PBSXY0jOxE9_h_HgQ',
            reply_markup=InlineKeyboardMarkup(
                [[
            InlineKeyboardButton('🙇🏻𝐃𝐄𝐓𝐀𝐈𝐋𝐒', callback_data='ban_inside')
            ],[
            InlineKeyboardButton('ミ★𝘉𝘈𝘊𝘒★彡', callback_data='featuresS'),
            InlineKeyboardButton('❌𝐂𝐋𝐎𝐒𝐄❌', callback_data='close_data')
        ]]
            )
        )
        await query.answer('ʙᴀɴ ᴏᴘᴛɪᴏɴs....')
        
    elif query.data == "ban_inside":
        buttons = [[
            InlineKeyboardButton('ミ★𝘉𝘈𝘊𝘒★彡', callback_data='featuresS')
        ]]
        r=await query.message.reply_text('▣▣▢▢▢▢')
        a=await r.edit('▣▣▣▢▢▢')
        v=await a.edit('▣▣▣▣▢▢')
        i=await v.edit('▣▣▣▣▣▢')
        n=await i.edit('▣▣▣▣▣▣')
        await asyncio.sleep(1)
        await n.delete()
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.delete()
        await query.message.reply(
            text=script.BAN_TXT,
            reply_markup=reply_markup,
            parse_mode='html',
            disable_web_page_preview=True
        )
        await query.answer('ᴏᴘᴇɴɪɴɢ ʙᴀɴ ʜᴇʟᴘ....')
             
    elif query.data == "coct":
        buttons = [[
            InlineKeyboardButton('ミ★𝘉𝘈𝘊𝘒★彡', callback_data='featuresS')
        ]]
        r=await query.message.reply_text('▣▣▢▢▢▢')
        a=await r.edit('▣▣▣▢▢▢')
        v=await a.edit('▣▣▣▣▢▢')
        i=await v.edit('▣▣▣▣▣▢')
        n=await i.edit('▣▣▣▣▣▣')
        await asyncio.sleep(1)
        await n.delete()
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.delete()
        await query.message.reply(
            text=script.CONNECTION_TXT,
            reply_markup=reply_markup,
            parse_mode='html',
            disable_web_page_preview=True
        )
        await query.answer('ᴏᴘᴇɴɪɴɢ ᴄᴏɴɴᴇᴄᴛᴏɴ ʜᴇʟᴘ..')
        
        
    elif query.data == "toolsjns":
        await query.message.delete()
        await query.message.reply_sticker(
            'CAACAgIAAxkBAALfQmKgyeuyvxZ9cOqJGt0bPop1lk4rAALLFAAC3bBRSUxgbDQypB1hHgQ',
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton('🎞𝐈𝐌𝐃𝐁', callback_data='imbd'),
                        InlineKeyboardButton('𝐈𝐍𝐅𝐎😀', callback_data='info')
                    ],
                    [
                        InlineKeyboardButton('🗃𝐂𝐀𝐑𝐁𝐎𝐍', callback_data='carbon'),
                        InlineKeyboardButton('Uʀʟ sʜᴏʀᴛ 🔗', callback_data='urlshrt')
                    ],
                    [
                        InlineKeyboardButton('ミ★𝘉𝘈𝘊𝘒★彡', callback_data='help'),
                        InlineKeyboardButton('❌𝐂𝐋𝐎𝐒𝐄❌', callback_data='close')
                    ]
                ]
            )
        )
        await query.answer('ᴍᴀᴊᴏʀ ᴛᴏᴏʟs...')
        
    elif query.data == "imbd":
        buttons = [[
            InlineKeyboardButton('ミ★𝘉𝘈𝘊𝘒★彡', callback_data='toolsjns')
        ]]
        r=await query.message.reply_text('▣▣▢▢▢▢')
        a=await r.edit('▣▣▣▢▢▢')
        v=await a.edit('▣▣▣▣▢▢')
        i=await v.edit('▣▣▣▣▣▢')
        n=await i.edit('▣▣▣▣▣▣')
        await asyncio.sleep(1)
        await n.delete()
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.delete()
        await query.message.reply(
            text=script.IMBD_TXT,
            reply_markup=reply_markup,
            parse_mode='html',
            disable_web_page_preview=True
        )
        await query.answer("ɪᴍᴅʙ ᴛᴏᴏʟs........")
        
    elif query.data == "carbon":
        buttons = [[
            InlineKeyboardButton('ミ★𝘉𝘈𝘊𝘒★彡', callback_data='toolsjns')
        ]]
        r=await query.message.reply_text('▣▣▢▢▢▢')
        a=await r.edit('▣▣▣▢▢▢')
        v=await a.edit('▣▣▣▣▢▢')
        i=await v.edit('▣▣▣▣▣▢')
        n=await i.edit('▣▣▣▣▣▣')
        await asyncio.sleep(1)
        await n.delete()
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.delete()
        await query.message.reply(
            text=script.CARBON_TXT,
            reply_markup=reply_markup,
            parse_mode='html',
            disable_web_page_preview=True
        )
        await query.answer("ᴛᴏᴏʟs ᴏᴘᴇɴɪɴɢ........")
        
    elif query.data == "info":
        buttons = [[
            InlineKeyboardButton('ミ★𝘉𝘈𝘊𝘒★彡', callback_data='toolsjns')
        ]]
        r=await query.message.reply_text('▣▣▢▢▢▢')
        a=await r.edit('▣▣▣▢▢▢')
        v=await a.edit('▣▣▣▣▢▢')
        i=await v.edit('▣▣▣▣▣▢')
        n=await i.edit('▣▣▣▣▣▣')
        await asyncio.sleep(1)
        await n.delete()
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.delete()
        await query.message.reply(
            text=script.INFO_TXT,
            reply_markup=reply_markup,
            parse_mode='html',
            disable_web_page_preview=True
        )
        await query.answer("ᴛᴏᴏʟs ᴏᴘᴇɴɪɴɢ........")
        
    elif query.data == "urlshrt":
        buttons = [[
            InlineKeyboardButton('ミ★𝘉𝘈𝘊𝘒★彡', callback_data='toolsjns')
        ]]
        r=await query.message.reply_text('▣▣▢▢▢▢')
        a=await r.edit('▣▣▣▢▢▢')
        v=await a.edit('▣▣▣▣▢▢')
        i=await v.edit('▣▣▣▣▣▢')
        n=await i.edit('▣▣▣▣▣▣')
        await asyncio.sleep(1)
        await n.delete()
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.delete()
        await query.message.reply(
            text=script.SHORT_TXT,
            reply_markup=reply_markup,
            parse_mode='html',
            disable_web_page_preview=True
        )
        await query.answer("ᴛᴏᴏʟs ᴏᴘᴇɴɪɴɢ........")

    elif query.data.startswith("setgs"):
        ident, set_type, status, grp_id = query.data.split("#")
        grpid = await active_connection(str(query.from_user.id))

        if str(grp_id) != str(grpid):
            await query.message.edit("Your Active Connection Has Been Changed. Go To /settings.")
            return await query.answer('✅Changed...')

        if status == "True" or status == "Chat":
            await save_group_settings(grpid, set_type, False)
        else:
            await save_group_settings(grpid, set_type, True)

        settings = await get_settings(grpid)

        if settings is not None:
            buttons = [
                [
                    InlineKeyboardButton('Filter Button',
                                         callback_data=f'setgs#button#{settings["button"]}#{str(grp_id)}'),
                    InlineKeyboardButton('Single' if settings["button"] else 'Double',
                                         callback_data=f'setgs#button#{settings["button"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton( 'Redirect To',
                                         callback_data=f'setgs#redirect_to#{settings["redirect_to"]}#{grp_id}',),
                    InlineKeyboardButton('👤 PM' if settings["redirect_to"] == "PM" else '📄 Chat',
                                         callback_data=f'setgs#redirect_to#{settings["redirect_to"]}#{grp_id}',),
                ],
                [
                    InlineKeyboardButton('Bot PM', callback_data=f'setgs#botpm#{settings["botpm"]}#{str(grp_id)}'),
                    InlineKeyboardButton('✅ Yes' if settings["botpm"] else '❌ No',
                                         callback_data=f'setgs#botpm#{settings["botpm"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('File Secure',
                                         callback_data=f'setgs#file_secure#{settings["file_secure"]}#{str(grp_id)}'),
                    InlineKeyboardButton('✅ Yes' if settings["file_secure"] else '❌ No',
                                         callback_data=f'setgs#file_secure#{settings["file_secure"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('IMDB', callback_data=f'setgs#imdb#{settings["imdb"]}#{str(grp_id)}'),
                    InlineKeyboardButton('✅ Yes' if settings["imdb"] else '❌ No',
                                         callback_data=f'setgs#imdb#{settings["imdb"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('Spell Check',
                                         callback_data=f'setgs#spell_check#{settings["spell_check"]}#{str(grp_id)}'),
                    InlineKeyboardButton('✅ Yes' if settings["spell_check"] else '❌ No',
                                         callback_data=f'setgs#spell_check#{settings["spell_check"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('Welcome', callback_data=f'setgs#welcome#{settings["welcome"]}#{str(grp_id)}'),
                    InlineKeyboardButton('✅ Yes' if settings["welcome"] else '❌ No',
                                         callback_data=f'setgs#welcome#{settings["welcome"]}#{str(grp_id)}')
                ]
            ]
            reply_markup = InlineKeyboardMarkup(buttons)
            await query.message.edit_reply_markup(reply_markup)
    elif query.data == "close":
        await query.message.delete()
    elif query.data == 'tips':
        await query.answer("=> 𝖲𝖾𝗇𝖽 𝖼𝗈𝗋𝗋𝖾𝖼𝗍 𝖬𝗈𝗏𝗂𝖾/𝗌𝖾𝗋𝗂𝖾𝗌 𝖭𝖺𝗆𝖾\n=>𝖳𝗈 𝖦𝖾𝗍 𝖡𝖾𝗍𝗍𝖾𝗋 𝗋𝖾𝗌𝗎𝗅𝗍 𝖥𝗈𝗋 movies include year and language along with movie name \n\n=>Made By Techno Mindz", True)
    elif query.data == 'moviesheading':
        await query.answer("=>This is your search results, if is there any changes in result kindly follow the tips ☺️ ", True)
    elif query.data == 'filenos':
        await query.answer("=>I have only this much files 😰 \n To get more results do request as per tips 👉🏻 ", True)
    elif query.data == 'inform':
        await query.answer("⚠︎ Information ⚠︎\n\nAfter 5 minutes this message will be automatically deleted\n\nIf you do not see the requested movie / series file, look at the next page\n\nⒸ @TmMainChannel", True)
    try: await query.answer('⏳Loading...') 
    except: pass


async def auto_filter(client, msg: pyrogram.types.Message, spoll=False):
    if not spoll:
        message = msg
        settings = await get_settings(message.chat.id)
        if message.text.startswith("/"): return  # ignore commands
        if re.findall("((^\/|^,|^!|^\.|^[\U0001F600-\U000E007F]).*)", message.text):
            return
        if 2 < len(message.text) < 100:
            search = message.text
            files, offset, total_results = await get_search_results(search.lower(), offset=0, filter=True)
            if not files:
                if settings["spell_check"]:
                    return await advantage_spell_chok(msg)
                else:
                    return
        else:
            return
    else:
        settings = await get_settings(msg.message.chat.id)
        message = msg.message.reply_to_message  # msg will be callback query
        search, files, offset, total_results = spoll
    
    pre = 'filep' if settings['file_secure'] else 'file'
    pre = 'Chat' if settings['redirect_to'] == 'Chat' else pre

    if settings["button"]:
        btn = [
            [
                InlineKeyboardButton(
                        text=f"🦋[{get_size(file.file_size)}]{file.file_name}", 
                        callback_data=f'{pre}#{file.file_id}#{msg.from_user.id if msg.from_user is not None else 0}'
                )
            ] 
            for file in files
        ]
    else:
        btn = [
            [
                InlineKeyboardButton(
                    text=f"{file.file_name}",
                    callback_data=f'{pre}#{file.file_id}#{msg.from_user.id if msg.from_user is not None else 0}',
                ),
                InlineKeyboardButton(
                    text=f"🦋[{get_size(file.file_size)}]",
                    callback_data=f'{pre}_#{file.file_id}#{msg.from_user.id if msg.from_user is not None else 0}',
                )
            ]
            for file in files
        ]

    btn.insert(0,
            [
                InlineKeyboardButton("𓂀𝕄𝕆𝕍𝕀𝔼𝕊𓂀", url="https://t.me/technomoviesCollection"),
                InlineKeyboardButton("彡ᴄʜᴀɴɴᴇʟ彡", url="https://t.me/TMmainchannel")
            ])

    btn.insert(0, [
        InlineKeyboardButton("🤖𓂀ℍ𝕆𝕎 𝕋𝕆 𝔻𝕆𝕎ℕ𝕃𝕆𝔸𝔻𓂀🤖", url="https://t.me/tmmainchannel/29")
    ])

    if offset != "":
        key = f"{message.chat.id}-{message.message_id}"
        BUTTONS[key] = search
        req = message.from_user.id if message.from_user else 0
        btn.append(
            [InlineKeyboardButton(text=f"🗓 1/{round(int(total_results) / 10)}", callback_data="pages"),
             InlineKeyboardButton(text="𝓝𝓔𝓧𝓣 ⏩", callback_data=f"next_{req}_{key}_{offset}")]
        )
    else:
        btn.append(
            [InlineKeyboardButton(text="🗓 1/1", callback_data="pages")]
        )
    imdb = await get_poster(search, file=(files[0]).file_name) if settings["imdb"] else None
    TEMPLATE = settings['template']
    if imdb:
        cap = TEMPLATE.format(
            query=search,
            mention_bot=temp.MENTION,
            mention_user=message.from_user.mention if message.from_user else message.sender_chat.title,
            title=imdb['title'],
            votes=imdb['votes'],
            aka=imdb["aka"],
            seasons=imdb["seasons"],
            box_office=imdb['box_office'],
            localized_title=imdb['localized_title'],
            kind=imdb['kind'],
            imdb_id=imdb["imdb_id"],
            cast=imdb["cast"],
            runtime=imdb["runtime"],
            countries=imdb["countries"],
            certificates=imdb["certificates"],
            languages=imdb["languages"],
            director=imdb["director"],
            writer=imdb["writer"],
            producer=imdb["producer"],
            composer=imdb["composer"],
            cinematographer=imdb["cinematographer"],
            music_team=imdb["music_team"],
            distributors=imdb["distributors"],
            release_date=imdb['release_date'],
            year=imdb['year'],
            genres=imdb['genres'],
            poster=imdb['poster'],
            plot=imdb['plot'],
            rating=imdb['rating'],
            url=imdb['url'],
            **locals()
        )
    else:
        cap = f"<b>💖<STRONG>{search}</STRONG>💝\n𝗨𝗣𝗟𝗢𝗔𝗗𝗘𝗗 𝗕𝗬 ♪♪\n✨@TechnoMoviesCollection\n\n⚙️ Nᴏᴛᴇ:→𝗧𝗵𝗶𝘀 𝗠𝗲𝘀𝘀𝗮𝗴𝗲 𝗪𝗶𝗹𝗹 𝗕𝗲 𝗔𝘂𝘁𝗼-𝗗𝗲𝗹𝗲𝘁𝗲𝗱 𝗔𝗳𝘁𝗲𝗿 5 𝗠𝗶𝗻𝘂𝘁𝗲 𝗧𝗼 𝗔𝘃𝗼𝗶𝗱 𝗖𝗼𝗽𝘆𝗿𝗶𝗴𝗵𝘁 𝗜𝘀𝘀𝘂𝗲𝘀.\n\n➥ 𝗝𝗼𝗶𝗻 ➼ 🔗@TmMainChannel</b> "
    if imdb and imdb.get('poster'):
        try:
            fmsg = await message.reply_photo(photo=imdb.get('poster'), caption=cap[:1024],#Imdb Poster Code
                                      reply_markup=InlineKeyboardMarkup(btn))
        except (MediaEmpty, PhotoInvalidDimensions, WebpageMediaEmpty):
            pic = imdb.get('poster')
            poster = pic.replace('.jpg', "._V1_UX360.jpg")
            fmsg = await message.reply_photo(photo=poster, caption=cap[:1024], reply_markup=InlineKeyboardMarkup(btn))#Imdb Poster Code
        except Exception as e:
            logger.exception(e)
            fmsg = await message.reply_photo(photo='https://telegra.ph/file/95909c55bee8db79f7b9a.jpg', caption=cap, reply_markup=InlineKeyboardMarkup(btn))# fmsg = await message.reply_text(cap, reply_markup=InlineKeyboardMarkup(btn)) Use This code if you need only caption
    else:
        fmsg = await message.reply_photo(photo='https://telegra.ph/file/95909c55bee8db79f7b9a.jpg', caption=cap, reply_markup=InlineKeyboardMarkup(btn))# fmsg = await message.reply_text(cap, reply_markup=InlineKeyboardMarkup(btn)) Use This code if you need only caption
    
    await asyncio.sleep(DELETE_TIME)
    await fmsg.delete()
    await client.send_video(
                chat_id=message.chat.id,
                video="https://telegra.ph/file/0cddf1c687a0dbc256313.mp4",
                caption=f"📢 Fɪʟᴛᴇʀ Fᴏʀ <code>{search}</code>\nBʏ <spoiler>{message.from_user.mention}</spoiler>\nIs Now Cʟᴏꜱᴇᴅ 😀\n\n@TmMainChannel",
                reply_to_message_id=message.message_id
            )
    await msg.delete()

    if spoll:
        await msg.message.delete()


async def advantage_spell_chok(msg):
    query = re.sub(
        r"\b(pl(i|e)*?(s|z+|ease|se|ese|(e+)s(e)?)|((send|snd|giv(e)?|gib)(\sme)?)|movie(s)?|new|latest|br((o|u)h?)*|^h(e|a)?(l)*(o)*|mal(ayalam)?|t(h)?amil|file|that|find|und(o)*|kit(t(i|y)?)?o(w)?|thar(u)?(o)*w?|kittum(o)*|aya(k)*(um(o)*)?|full\smovie|any(one)|with\ssubtitle(s)?)",
        "", msg.text, flags=re.IGNORECASE)  # plis contribute some common words
    query = query.strip() + " movie"
    g_s = await search_gagala(query)
    g_s += await search_gagala(msg.text)
    gs_parsed = []
    if not g_s:
        one_button = InlineKeyboardMarkup([[InlineKeyboardButton("🥲 𝗢𝗪𝗡𝗘𝗥 🔥", url="https://t.me/TechnoKillerBot"), InlineKeyboardButton("🤕 𝗚𝗢𝗢𝗚𝗟𝗘 🤒", url="https://www.google.com/")]])
        k = await msg.reply_video(video="https://telegra.ph//file/d90256b1575c7aaadccc5.mp4", caption="Hey, 𝐒𝐨𝐫𝐫𝐲, 𝐍𝐨 𝐌𝐨𝐯𝐢𝐞/𝐒𝐞𝐫𝐢𝐞𝐬 𝐑𝐞𝐥𝐚𝐭𝐞𝐝 𝐓𝐨 𝐓𝐡𝐞 𝐆𝐢𝐯𝐞𝐧 𝐖𝐨𝐫𝐝 𝐖𝐚𝐬 𝐅𝐨𝐮𝐧𝐝 🥺\n\n𝙿𝚘𝚜𝚜𝚒𝚋𝚕𝚎 𝙲𝚊𝚞𝚜𝚎𝚜 : 🤔\n\n⭕️ 𝐍𝐨𝐭 𝐑𝐞𝐥𝐞𝐚𝐬𝐞𝐝 𝐘𝐞𝐭\n⭕️ 𝐈𝐧𝐜𝐨𝐫𝐫𝐞𝐜𝐭 𝐒𝐩𝐞𝐥𝐥𝐢𝐧𝐠\n⭕ 𝐍𝐨𝐭 𝐔𝐩𝐥𝐨𝐚𝐝𝐞𝐝 𝐁𝐲 𝐎𝐰𝐧𝐞𝐫\n\n👉Contact To My Owner👇", reply_markup = one_button)
        await asyncio.sleep(15)
        await k.delete()
        await msg.delete()
        return
    regex = re.compile(r".*(imdb|wikipedia).*", re.IGNORECASE)  # look for imdb / wiki results
    gs = list(filter(regex.match, g_s))
    gs_parsed = [re.sub(
        r'\b(\-([a-zA-Z-\s])\-\simdb|(\-\s)?imdb|(\-\s)?wikipedia|\(|\)|\-|reviews|full|all|episode(s)?|film|movie|series)',
        '', i, flags=re.IGNORECASE) for i in gs]
    if not gs_parsed:
        reg = re.compile(r"watch(\s[a-zA-Z0-9_\s\-\(\)]*)*\|.*",
                         re.IGNORECASE)  # match something like Watch Niram | Amazon Prime
        for mv in g_s:
            match = reg.match(mv)
            if match:
                gs_parsed.append(match.group(1))
    user = msg.from_user.id if msg.from_user else 0
    movielist = []
    gs_parsed = list(dict.fromkeys(gs_parsed))  # removing duplicates https://stackoverflow.com/a/7961425
    if len(gs_parsed) > 3:
        gs_parsed = gs_parsed[:3]
    if gs_parsed:
        for mov in gs_parsed:
            imdb_s = await get_poster(mov.strip(), bulk=True)  # searching each keyword in imdb
            if imdb_s:
                movielist += [movie.get('title') for movie in imdb_s]
    movielist += [(re.sub(r'(\-|\(|\)|_)', '', i, flags=re.IGNORECASE)).strip() for i in gs_parsed]
    movielist = list(dict.fromkeys(movielist))  # removing duplicates
    if not movielist:
        one_button = InlineKeyboardMarkup([[InlineKeyboardButton("🥲 𝗢𝗪𝗡𝗘𝗥 🔥", url="https://t.me/TechnoKillerBot"), InlineKeyboardButton("🤕 𝗚𝗢𝗢𝗚𝗟𝗘 🤒", url="https://www.google.com/")]])
        k = await msg.reply_video(video="https://telegra.ph//file/d90256b1575c7aaadccc5.mp4", caption="Hey, 𝐒𝐨𝐫𝐫𝐲, 𝐍𝐨 𝐌𝐨𝐯𝐢𝐞/𝐒𝐞𝐫𝐢𝐞𝐬 𝐑𝐞𝐥𝐚𝐭𝐞𝐝 𝐓𝐨 𝐓𝐡𝐞 𝐆𝐢𝐯𝐞𝐧 𝐖𝐨𝐫𝐝 𝐖𝐚𝐬 𝐅𝐨𝐮𝐧𝐝 🥺\n\n𝙿𝚘𝚜𝚜𝚒𝚋𝚕𝚎 𝙲𝚊𝚞𝚜𝚎𝚜 : 🤔\n\n⭕️ 𝐍𝐨𝐭 𝐑𝐞𝐥𝐞𝐚𝐬𝐞𝐝 𝐘𝐞𝐭\n⭕️ 𝐈𝐧𝐜𝐨𝐫𝐫𝐞𝐜𝐭 𝐒𝐩𝐞𝐥𝐥𝐢𝐧𝐠\n⭕ 𝐍𝐨𝐭 𝐔𝐩𝐥𝐨𝐚𝐝𝐞𝐝 𝐁𝐲 𝐎𝐰𝐧𝐞𝐫\n\n👉Contact To My Owner👇", reply_markup = one_button)
        await asyncio.sleep(20)
        await k.delete()
        await msg.delete()
        return
    SPELL_CHECK[msg.message_id] = movielist
    btn = [[
        InlineKeyboardButton(
            text=movie.strip(),
            callback_data=f"spolling#{user}#{k}",
        )
    ] for k, movie in enumerate(movielist)]
    btn.append([InlineKeyboardButton(text="Close", callback_data=f'spolling#{user}#close_spellcheck')])
    one_button = InlineKeyboardMarkup([[InlineKeyboardButton("🥲 𝗢𝗪𝗡𝗘𝗥 🔥", url="https://t.me/TechnoKillerBot"), InlineKeyboardButton("🤕 𝗚𝗢𝗢𝗚𝗟𝗘 🤒", url="https://www.google.com/")]])
    k = await msg.reply_video(video="https://telegra.ph//file/d90256b1575c7aaadccc5.mp4", caption="Hey, 𝐒𝐨𝐫𝐫𝐲, 𝐍𝐨 𝐌𝐨𝐯𝐢𝐞/𝐒𝐞𝐫𝐢𝐞𝐬 𝐑𝐞𝐥𝐚𝐭𝐞𝐝 𝐓𝐨 𝐓𝐡𝐞 𝐆𝐢𝐯𝐞𝐧 𝐖𝐨𝐫𝐝 𝐖𝐚𝐬 𝐅𝐨𝐮𝐧𝐝 🥺\n\n𝙿𝚘𝚜𝚜𝚒𝚋𝚕𝚎 𝙲𝚊𝚞𝚜𝚎𝚜 : 🤔\n\n⭕️ 𝐍𝐨𝐭 𝐑𝐞𝐥𝐞𝐚𝐬𝐞𝐝 𝐘𝐞𝐭\n⭕️ 𝐈𝐧𝐜𝐨𝐫𝐫𝐞𝐜𝐭 𝐒𝐩𝐞𝐥𝐥𝐢𝐧𝐠\n⭕ 𝐍𝐨𝐭 𝐔𝐩𝐥𝐨𝐚𝐝𝐞𝐝 𝐁𝐲 𝐎𝐰𝐧𝐞𝐫\n\n👉Contact To My Owner👇", reply_markup = one_button)
    await asyncio.sleep(20)
    await k.delete()
    await msg.delete()
    
    
async def manual_filters(client, message, text=False):
    group_id = message.chat.id
    name = text or message.text
    reply_id = message.reply_to_message.message_id if message.reply_to_message else message.message_id
    keywords = await get_filters(group_id)
    for keyword in reversed(sorted(keywords, key=len)):
        pattern = r"( |^|[^\w])" + re.escape(keyword) + r"( |$|[^\w])"
        if re.search(pattern, name, flags=re.IGNORECASE):
            reply_text, btn, alert, fileid = await find_filter(group_id, keyword)

            if reply_text:
                reply_text = reply_text.replace("\\n", "\n").replace("\\t", "\t")

            if btn is not None:
                try:
                    if fileid == "None":
                        if btn == "[]":
                            fmsg = await client.send_message(group_id, reply_text, disable_web_page_preview=True)
                        else:
                            button = eval(btn)
                            fmsg = await client.send_message(
                                group_id,
                                reply_text,
                                disable_web_page_preview=True,
                                reply_markup=InlineKeyboardMarkup(button),
                                reply_to_message_id=reply_id
                            )
                    elif btn == "[]":
                        fmsg = await client.send_cached_media(
                            group_id,
                            fileid,
                            caption=reply_text or "",
                            reply_to_message_id=reply_id
                        )
                    else:
                        button = eval(btn)
                        fmsg = await message.reply_cached_media(
                            fileid,
                            caption=reply_text or "",
                            reply_markup=InlineKeyboardMarkup(button),
                            reply_to_message_id=reply_id
                        )
                        
                    await asyncio.sleep(DELETE_TIME)
                    await fmsg.delete()
                    
                except Exception as e:
                    logger.exception(e)
                break
    else:
        return False
