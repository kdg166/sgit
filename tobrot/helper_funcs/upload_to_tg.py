#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# (c) Shrimadhav U K

# the logging things
import logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logging.getLogger("pyrogram").setLevel(logging.WARNING)
LOGGER = logging.getLogger(__name__)

import asyncio
import os
import re
import time
import sys, subprocess, shlex
from subprocess import call
from hachoir.metadata import extractMetadata
from hachoir.parser import createParser
from PIL import Image
from pyrogram.types import (
    InputMediaDocument,
    InputMediaVideo,
    InputMediaAudio
)
from tobrot.helper_funcs.display_progress import (
    progress_for_pyrogram,
    humanbytes
)
from tobrot.helper_funcs.split_large_files import split_large_files
from tobrot.helper_funcs.copy_similar_file import copy_file

from tobrot import (
    TG_MAX_FILE_SIZE,
    EDIT_SLEEP_TIME_OUT,
    DOWNLOAD_LOCATION
)


async def upload_to_tg(
    message,
    local_file_name,
    from_user,
    dict_contatining_uploaded_files,
    edit_media=False,
    custom_caption=None
):
   
    LOGGER.info(local_file_name)
    base_file_name = os.path.basename(local_file_name)
    base_new_name = os.path.splitext(base_file_name)[0]
    extension_new_name = os.path.splitext(base_file_name)[1]
    b = base_new_name
    if local_file_name.upper().endswith(("MP3", "M4A", "M4B", "FLAC", "WAV", "RAR", "7Z", "ZIP")):
      caption_str = f"<code>{base_new_name}{extension_new_name}</code>\n\n<b>{m3}</b>"
    elif b[:3] == "KDG" and local_file_name.lower().endswith(".mp4"):
      caption_str = f"<b>{base_new_name}{extension_new_name}\n\n@kdg_166 @korea_drama\n@kdgfiles</b>"
    elif b[:3] == "KDG" and local_file_name.lower().endswith(".mkv"):
      caption_str = f"<b>{base_new_name}{extension_new_name}\n\n@kdg_166 @korea_drama\n@kdgfiles\n\nMuxed English Subtitles\nPlay it via external player</b>"
    else:
      caption_str = f"{base_new_name}{extension_new_name}"
    if os.path.isdir(local_file_name):
        directory_contents = os.listdir(local_file_name)
        directory_contents.sort()
        # number_of_files = len(directory_contents)
        LOGGER.info(directory_contents)
        new_m_esg = message
        if not message.photo:
            new_m_esg = await message.reply_text(
                "Found {} files".format(len(directory_contents)),
                quote=True
                # reply_to_message_id=message.message_id
            )
        for single_file in directory_contents:
            # recursion: will this FAIL somewhere?
            await upload_to_tg(
                new_m_esg,
                os.path.join(local_file_name, single_file),
                from_user,
                dict_contatining_uploaded_files,
                edit_media,
                caption_str
            )
    else:
        if os.path.getsize(local_file_name) > TG_MAX_FILE_SIZE:
            LOGGER.info("TODO")
            d_f_s = humanbytes(os.path.getsize(local_file_name))
            i_m_s_g = await message.reply_text(
                "Telegram does not support uploading this file.\n"
                f"Detected File Size: {d_f_s} ????\n"
                "\n???? trying to split the files ????????????"
            )
            splitted_dir = await split_large_files(local_file_name)
            totlaa_sleif = os.listdir(splitted_dir)
            totlaa_sleif.sort()
            number_of_files = len(totlaa_sleif)
            LOGGER.info(totlaa_sleif)
            ba_se_file_name = os.path.basename(local_file_name)
            await i_m_s_g.edit_text(
                f"Detected File Size: {d_f_s} ????\n"
                f"<code>{ba_se_file_name}</code> splitted into {number_of_files} files.\n"
                "trying to upload to Telegram, now ..."
            )
            for le_file in totlaa_sleif:
                # recursion: will this FAIL somewhere?
                await upload_to_tg(
                    message,
                    os.path.join(splitted_dir, le_file),
                    from_user,
                    dict_contatining_uploaded_files
                )
        else:
            sent_message = await upload_single_file(
                message,
                local_file_name,
                caption_str,
                from_user,
                edit_media
            )
            if sent_message is not None:
                dict_contatining_uploaded_files[os.path.basename(local_file_name)] = sent_message.message_id
    # await message.delete()
    return dict_contatining_uploaded_files


async def upload_single_file(message, local_file_name, caption_str, from_user, edit_media):
    await asyncio.sleep(EDIT_SLEEP_TIME_OUT)
    sent_message = None
    start_time = time.time()
    #
    thumbnail_location = os.path.join(
        DOWNLOAD_LOCATION,
        "thumbnails",
        str(from_user) + ".jpg"
    )
    LOGGER.info(thumbnail_location)
    #
    try:
        message_for_progress_display = message
        if not edit_media:
            message_for_progress_display = await message.reply_text(
                "starting upload of {}".format(os.path.basename(local_file_name))
            )
        if local_file_name.upper().endswith(("WEBM","MP4")) and not local_file_name.upper().startswith(("KDG")):
            metadata = extractMetadata(createParser(local_file_name))
            duration = 0
            if metadata.has("duration"):
                duration = metadata.get('duration').seconds
            #
            width = 0
            height = 0
            thumb_image_path = None
            if os.path.exists(thumbnail_location):
                thumb_image_path = await copy_file(
                    thumbnail_location,
                    os.path.dirname(os.path.abspath(local_file_name))
                )
            else:
                thumb_image_path = None
            thumb = None
            if thumb_image_path is not None and os.path.isfile(thumb_image_path):
                thumb = thumb_image_path
            # send video
            if edit_media and message.photo:
                sent_message = await message.edit_media(
                    media=InputMediaVideo(
                        media=local_file_name,
                        thumb=thumb,
                        caption=caption_str,
                        parse_mode="html",
                        width=width,
                        height=height,
                        duration=duration,
                        supports_streaming=True
                    )
                    # quote=True,
                )
            else:
                sent_message = await message.reply_video(
                    video=local_file_name,
                    # quote=True,
                    caption=caption_str,
                    parse_mode="html",
                    duration=duration,
                    width=width,
                    height=height,
                    thumb=thumb,
                    supports_streaming=True,
                    disable_notification=True,
                    # reply_to_message_id=message.reply_to_message.message_id,
                    progress=progress_for_pyrogram,
                    progress_args=(
                        "trying to upload",
                        message_for_progress_display,
                        start_time
                    )
                )
            if thumb is not None:
                os.remove(thumb)
        elif local_file_name.upper().endswith(("MP3", "M4A", "M4B", "FLAC", "WAV")):
            metadata = extractMetadata(createParser(local_file_name))
            duration = 0
            title = ""
            artist = ""
            if metadata.has("duration"):
                duration = metadata.get('duration').seconds
            if metadata.has("title"):
                title = metadata.get("title")
            if metadata.has("artist"):
                artist = metadata.get("artist")
            thumb_image_path = None
            if os.path.isfile(thumbnail_location):
                thumb_image_path = await copy_file(
                    thumbnail_location,
                    os.path.dirname(os.path.abspath(local_file_name))
                )
            thumb = None
            if thumb_image_path is not None and os.path.isfile(thumb_image_path):
                thumb = thumb_image_path
            # send audio
            if edit_media and message.photo:
                sent_message = await message.edit_media(
                    media=InputMediaAudio(
                        media=local_file_name,
                        thumb=thumb,
                        caption=caption_str,
                        parse_mode="html",
                        duration=duration,
                        performer=artist,
                        title=title
                    )
                    # quote=True,
                )
            else:
                sent_message = await message.reply_audio(
                    audio=local_file_name,
                    # quote=True,
                    caption=caption_str,
                    parse_mode="html",
                    duration=duration,
                    performer=artist,
                    title=title,
                    thumb=thumb,
                    disable_notification=True,
                    # reply_to_message_id=message.reply_to_message.message_id,
                    progress=progress_for_pyrogram,
                    progress_args=(
                        "trying to upload",
                        message_for_progress_display,
                        start_time
                    )
                )
            if thumb is not None:
                os.remove(thumb)
        else:
            base_file_name=os.path.basename(local_file_name)
            base_new_name = os.path.splitext(base_file_name)[0]
            extension_new_name = os.path.splitext(base_file_name)[1]
            thumb_image_path = None
            if os.path.isfile(thumbnail_location):
                thumb_image_path = await copy_file(
                    thumbnail_location,
                    os.path.dirname(os.path.abspath(local_file_name))
                )
            # if a file, don't upload "thumb"
            # this "diff" is a major derp -_- ????????????
            thumb = None
            if thumb_image_path is not None and os.path.isfile(thumb_image_path):
                thumb = thumb_image_path
            #
            # send document
            if edit_media and message.photo:
                sent_message = await message.edit_media(
                    media=InputMediaDocument(
                        media=local_file_name,
                        thumb=thumb,
                        caption=caption_str,
                        parse_mode="html"
                    )
                    # quote=True,
                )
            else:
                  sent_message = await message.reply_document(
                    document=local_file_name,
                    # quote=True,
                    thumb=thumb,
                    caption=caption_str,
                    parse_mode="html",
                    disable_notification=True,
                    # reply_to_message_id=message.reply_to_message.message_id,
                    progress=progress_for_pyrogram,
                    progress_args=(
                        "trying to upload",
                        message_for_progress_display,
                        start_time
                    )
                    
                  )
                  
            if thumb is not None:
                os.remove(thumb)
    except Exception as e:
        await message_for_progress_display.edit_text("**FAILED**\n" + str(e))
    else:
        if message.message_id != message_for_progress_display.message_id:
            await message_for_progress_display.delete()
    os.remove(local_file_name)
    return sent_message

