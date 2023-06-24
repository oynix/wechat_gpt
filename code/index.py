import os
import time

import xml.etree.ElementTree as ET
from flask import Flask, request, Response, abort
from utils import Utils, UserProfile, load, dump
from logger import log_info
from response_utils import send_text_response
import pdf_utils
import gpt_handler
import event_handler
import echo_handler

app = Flask(__name__)

echo_word = 'echo'

wechat_token = ''


@app.route('/', methods=['POST', 'GET'])
def index():
    fc_context = request.environ.get('fc.context')
    if fc_context:
        request.environ['Request-Id'] = fc_context.request_id

    return handle()


def handle():
    begin = time.time()

    # 公众号的验证机制，有这个参数就直接返回
    echo_str = request.args.get('echostr')
    if echo_str:
        return echo_str

    # 没有body，下面的事都不用做，直接返回
    if not request.data:
        return 'Hello World'

    action_token = request.headers.get('Action-Token')
    if action_token == 'gpt':
        return gpt_handler.handle_ask()

    body = ET.fromstring(request.data)
    if not body:
        return 'Hello World'

    log_info('request.data:{}'.format(request.data))

    msg_type = body.find('MsgType').text

    if msg_type == 'event':
        return event_handler.handle_event(body)

    user_id = body.find('FromUserName').text
    gh_id = body.find('ToUserName').text

    if msg_type != 'text' and msg_type != 'voice':
        return send_text_response(gh_id, user_id, '我只认识文字，也能听懂语音')

    if msg_type == 'text':
        msg = body.find('Content').text
    else:
        msg = body.find('Recognition').text

    if not msg:
        return send_text_response(gh_id, user_id, '再重复一下，刚刚没有听清')

    if msg == echo_word:
        return send_text_response(gh_id, user_id, echo_handler.handle_echo(user_id))

    msg_id = body.find('MsgId').text

    profile_file_name = Utils.get_user_profile_name(user_id)
    profile = load(profile_file_name, object_hook=UserProfile.from_json)
    if profile is None:
        profile = UserProfile()

    reply = 'just wait'
    # 是新消息，先去问gpt，然后去找答案，不是新消息则直接去找答案
    if not profile.msg_id:
        profile.msg_id = msg_id
        profile.msg_n = 0
        profile.last_gpt_msg_id = msg_id
        dump(profile_file_name, profile.to_dict())

        msg_chat = {'msg': msg, 'type': 'text', 'reply': '', 'prompt': msg}

        # 如果包含https和PDF关键字，则按照处理PDF文件处理
        if '@' in msg and 'http' in msg:
            pdf_index = msg.index('@')
            pdf_url = msg[:pdf_index].strip()
            question = msg[pdf_index + 1:].strip()
            file_path = pdf_utils.download_file(pdf_url, Utils.get_user_pdf_dir(user_id))
            if not file_path:
                return send_text_response(gh_id, user_id, '下载文件失败，再试一次！')
            fix_file_path = pdf_utils.fix_pdf_eof(file_path)
            if not fix_file_path:
                return send_text_response(gh_id, user_id, '这个PDF文件似乎不太能用呢')
            pdf_content = pdf_utils.extract_pdf(fix_file_path, 1000)
            msg_chat['type'] = 'pdf'
            msg_chat['prompt'] = '{0}:{1}'.format(question, pdf_content)

        dump(Utils.get_msg_chat_name(user_id, msg_id), msg_chat)
        log_info('ask response:{}'.format(gpt_handler.send_request(msg_id, user_id)))

    # 有正在处理的msg
    if profile.msg_id != msg_id:
        return send_text_response(gh_id, user_id, '上个问题我还没想出来，查看答案回复【{0}】'.format(echo_word))

    # wechat在重试
    profile.msg_n += 1
    dump(profile_file_name, profile.to_dict())

    reply = get_msg_reply(profile.msg_n, begin, user_id, msg_id)
    if reply is not None:
        log_info('get msg success, msg={0},reply={1}'.format(msg, reply))
        profile.msg_id = ''
        dump(profile_file_name, profile.to_dict())
        return send_text_response(gh_id, user_id, reply)

    log_info('get msg timeout, n={0},id={1}'.format(profile.msg_n, profile.msg_id))
    if profile.msg_n >= 3:  # 没机会了，接受现实吧，让用户自己去重试
        profile.msg_id = ''
        reply = '这个问题太难了，还需要点时间，等下回复【{0}】查看我想到的答案'.format(echo_word)
        dump(profile_file_name, profile.to_dict())
        return send_text_response(gh_id, user_id, reply)

    # 还有机会，直接abort，wechat会再重试
    abort(500)


def get_msg_reply(msg_n, begin, user_id, msg_id):
    threshold = 2.5 if msg_n > 2 else 4
    msg_chat = load(Utils.get_msg_chat_name(user_id, msg_id))
    while True:
        if msg_chat.get('reply'):
            if msg_chat.get('permit', False):
                return msg_chat['reply']
            else:
                return '这个问题我不便回答'
        time.sleep(0.5)
        if time.time() - begin >= threshold:
            return None
