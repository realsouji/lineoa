# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import errno
import os
import sys
import tempfile
import time, random, json, codecs, shutil ,threading, glob, re, base64, string, os, requests, urllib, urllib.parse, atexit, asyncio, traceback, sys, argparse
from argparse import ArgumentParser

from flask import Flask, request, abort

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
    SourceUser, SourceGroup, SourceRoom,
    TemplateSendMessage, ConfirmTemplate, MessageTemplateAction,
    ButtonsTemplate, ImageCarouselTemplate, ImageCarouselColumn, URITemplateAction,
    PostbackTemplateAction, DatetimePickerTemplateAction,
    CarouselTemplate, CarouselColumn, PostbackEvent,
    StickerMessage, StickerSendMessage, LocationMessage, LocationSendMessage,
    ImageMessage, VideoMessage, AudioMessage, FileMessage, AudioSendMessage,
    UnfollowEvent, FollowEvent, JoinEvent, LeaveEvent, BeaconEvent
)

app = Flask(__name__)

# get channel_secret and channel_access_token from your environment variable

line_bot_api = LineBotApi(
    'fPPAhV2RUmIjNddnQUtbGtjT5/ltdynnbuO70jiwk2RqV9mWS5arLVFQYconUHzYwBmpdMQ0pClErRsoRgXO13CzJtCmMIsBAFnUwaa5jid+NtLY7NwB6M4EcJUlVRw3QRab80quYrgbpJWkn2ApgwdB04t89/1O/w1cDnyilFU=')
handler = WebhookHandler('580eb174fc72a0c0c071f78402170d63')

static_tmp_path = os.path.join(os.path.dirname(__file__), 'static', 'tmp')

apiKey = "p4HvBwnz-n9C"

# function for create tmp dir for download content
def command(text):
    cmd = text.lower()
    return cmd
    
def removeCmd(cmd, text):
	rmv = len(cmd) + 1
	return text[rmv:]

def make_static_tmp_dir():
    try:
        os.makedirs(static_tmp_path)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(static_tmp_path):
            pass
        else:
            raise


@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'


@handler.add(MessageEvent, message=TextMessage)
def handle_text_message(event):
    text = event.message.text #simplify for receove message
    sender = event.source.user_id #get user_id
    gid = event.source.sender_id #get group_id
    cmd = command(text)
    if cmd == 'profile':
        if isinstance(event.source, SourceUser):
            profile = line_bot_api.get_profile(event.source.user_id)
            line_bot_api.reply_message(
                event.reply_token, [
                    TextSendMessage(
                        text='Display name: ' + profile.display_name
                    ),
                    TextSendMessage(
                        text='Status message: ' + profile.status_message
                    )
                ]
            )
        else:
            line_bot_api.reply_message(
                event.reply_token,
                TextMessage(text="Bot can't use profile API without user ID"))
    elif cmd.startswith('joox '):
        hasil = removeCmd("joox", text)
        count = hasil.split("-")
        print(count)
        search = str(count[0])
        headers = {"apiKey": apiKey}
        r = requests.get("https://beapi.me/joox?search="+search,headers=headers)
        print(r)
        data = json.loads(r.text)
        if len(count) == 1:            
            no = 0
            ret_ = "「 JOOX LIST 」"
            for aa in data["result"]:
                no += 1
                ret_ += "\n{}. {} - {}".format(no,aa["msinger"],aa["msong"])
            ret_ += "\n「 Joox {}-number 」".format(str(search))
            line_bot_api.reply_message(
                event.reply_token,
                TextMessage(text=ret_))
        elif len(count) == 2:
            num = int(count[1])
            print(num)
            leng = len(data["result"])
            path = data["result"][num - 1]["m4aUrl"]
            audio_message = AudioSendMessage(
                original_content_url=path,
                duration=240000
            )
            line_bot_api.reply_message(
                event.reply_token, audio_message)
    elif cmd == 'bye':
        if isinstance(event.source, SourceGroup):
            line_bot_api.reply_message(
                event.reply_token, TextMessage(text='Leaving group'))
            line_bot_api.leave_group(event.source.group_id)
        elif isinstance(event.source, SourceRoom):
            line_bot_api.reply_message(
                event.reply_token, TextMessage(text='Leaving group'))
            line_bot_api.leave_room(event.source.room_id)
        else:
            line_bot_api.reply_message(
                event.reply_token,
                TextMessage(text="Bot can't leave from 1:1 chat"))
   


@handler.add(MessageEvent, message=LocationMessage)
def handle_location_message(event):
    line_bot_api.reply_message(
        event.reply_token,
        LocationSendMessage(
            title=event.message.title, address=event.message.address,
            latitude=event.message.latitude, longitude=event.message.longitude
        )
    )


@handler.add(MessageEvent, message=StickerMessage)
def handle_sticker_message(event):
    line_bot_api.reply_message(
        event.reply_token,
        StickerSendMessage(
            package_id=event.message.package_id,
            sticker_id=event.message.sticker_id)
    )


# Other Message Type
@handler.add(MessageEvent, message=(ImageMessage, VideoMessage, AudioMessage))
def handle_content_message(event):
    if isinstance(event.message, ImageMessage):
        ext = 'jpg'
    elif isinstance(event.message, VideoMessage):
        ext = 'mp4'
    elif isinstance(event.message, AudioMessage):
        ext = 'm4a'
    else:
        return

    message_content = line_bot_api.get_message_content(event.message.id)
    with tempfile.NamedTemporaryFile(dir=static_tmp_path, prefix=ext + '-', delete=False) as tf:
        for chunk in message_content.iter_content():
            tf.write(chunk)
        tempfile_path = tf.name

    dist_path = tempfile_path + '.' + ext
    dist_name = os.path.basename(dist_path)
    os.rename(tempfile_path, dist_path)

    line_bot_api.reply_message(
        event.reply_token, [
            TextSendMessage(text='Save content.'),
            TextSendMessage(text=request.host_url +
                            os.path.join('static', 'tmp', dist_name))
        ])


@handler.add(MessageEvent, message=FileMessage)
def handle_file_message(event):
    message_content = line_bot_api.get_message_content(event.message.id)
    with tempfile.NamedTemporaryFile(dir=static_tmp_path, prefix='file-', delete=False) as tf:
        for chunk in message_content.iter_content():
            tf.write(chunk)
        tempfile_path = tf.name

    dist_path = tempfile_path + '-' + event.message.file_name
    dist_name = os.path.basename(dist_path)
    os.rename(tempfile_path, dist_path)

    line_bot_api.reply_message(
        event.reply_token, [
            TextSendMessage(text='Save file.'),
            TextSendMessage(text=request.host_url +
                            os.path.join('static', 'tmp', dist_name))
        ])


@handler.add(FollowEvent)
def handle_follow(event):
    line_bot_api.reply_message(
        event.reply_token, TextSendMessage(text='Got follow event'))


@handler.add(UnfollowEvent)
def handle_unfollow():
    app.logger.info("Got Unfollow event")


@handler.add(JoinEvent)
def handle_join(event):
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text='Joined this ' + event.source.type))


@handler.add(LeaveEvent)
def handle_leave():
    app.logger.info("Got leave event")


@handler.add(PostbackEvent)
def handle_postback(event):
    if event.postback.data == 'ping':
        line_bot_api.reply_message(
            event.reply_token, TextSendMessage(text='pong'))
    elif event.postback.data == 'datetime_postback':
        line_bot_api.reply_message(
            event.reply_token, TextSendMessage(text=event.postback.params['datetime']))
    elif event.postback.data == 'date_postback':
        line_bot_api.reply_message(
            event.reply_token, TextSendMessage(text=event.postback.params['date']))


@handler.add(BeaconEvent)
def handle_beacon(event):
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(
            text='Got beacon event. hwid={}, device_message(hex string)={}'.format(
                event.beacon.hwid, event.beacon.dm)))


if __name__ == "__main__":
    make_static_tmp_dir()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
