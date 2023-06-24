import json
import os
import time
import xml.etree.ElementTree as ET

import openai
import requests
from flask import request

from logger import log_info
from utils import Utils, load, dump
from ca_utils import content_audit

fc_trigger_url = os.environ.get('FUNC_TRIGGER_URL')

# model_engine = 'text-davinci-003'
model_engine = os.environ.get('OPENAI_MODEL_ENGINE', 'gpt-3.5-turbo')
openai.api_key = os.environ.get('OPENAI_API_KEY', '')  # 设置您的 API 密钥

gpt_pre_prompt = '''从现在开始，你要模拟一名普通人'''
gpt_pre_answer = '是的，我会遵守这些原则。请问您需要哪方面的帮助呢？'


def send_request(msg_id: str, user_id: str):
    ask_body = {
        'msg_id': msg_id,
        'user_id': user_id,
    }
    ask_header = {
        'x-fc-invocation-type': 'Async',
        'Action-Token': 'gpt'
    }
    ask_response = requests.post(fc_trigger_url, json=ask_body, headers=ask_header)
    return ask_response.text


def handle_ask():
    begin = int(time.time())
    body = json.loads(request.data)
    log_info('ask body:{}'.format(body))

    user_id = body['user_id']
    msg_id = body['msg_id']

    # 一问一答，称为一个chat，一个chat单独存一个文件，以msg_id命名，方便查找
    msg_chat_file_name = Utils.get_msg_chat_name(user_id, msg_id)
    msg_chat = load(msg_chat_file_name)
    if msg_chat is None:
        log_info('ask gpt, but no msg chat found for user id:{0},msg id:{1}'.format(user_id, msg_id))
        return 'success'

    prompt = msg_chat['prompt']

    messages_file_name = Utils.get_chat_messages_name(user_id)
    messages = load(messages_file_name)
    if messages is None:
        messages = []

    max_cache = 4
    if len(messages) > max_cache:
        backup = messages[0:-max_cache]
        dump(Utils.get_messages_back_name(user_id, begin), backup)
        messages = messages[-max_cache:]

    append_prompt(messages, prompt)
    dump(messages_file_name, messages)

    # 为了确保gpt不乱说话，需要在最前面加入一组预设好的条件(gpt_pre_prompt, gpt_pre_answer)
    # 如果是PDF，则不用
    conversation = []
    if msg_chat['type'] == 'text':
        append_prompt(conversation, gpt_pre_prompt)
        append_answer(conversation, gpt_pre_answer)
    conversation.extend(messages)
    log_info('conversation:{}'.format(conversation))
    try:
        chat = openai.ChatCompletion.create(
            model=model_engine,
            messages=conversation,
            max_tokens=2048,
            n=1,
            stop=None,
            temperature=1
        )
        log_info('gpt response, elapsed:{0:.2f}s,result:{1}'.format((time.time() - begin), chat))
        answer = chat.choices[0].message.content.strip()

        # 得到回答后，拿去审核
        ci_resp = content_audit(answer)
        job_details = ET.fromstring(ci_resp.text).find('JobsDetail')
        ci_result = int(job_details.find('Result').text)
        permit = True if ci_result == 0 else False

        # 审核通过则把回答也加进去，没通过则把问题移除
        if permit:
            append_answer(messages, answer)
        else:
            last_msg = messages.pop()
            log_info('ci not permit, removed:{}'.format(last_msg))
        dump(messages_file_name, messages)

        msg_chat['reply'] = answer
        msg_chat['permit'] = permit
        msg_chat['ci'] = ci_resp.text
    except Exception as e:
        log_info('gpt error:{0}'.format(e))
        msg_chat['reply'] = 'gpt error:{0}'.format(e)
        msg_chat['permit'] = False
        msg_chat['ci'] = ''

    dump(msg_chat_file_name, msg_chat)

    return 'success'


def append_answer(messages, answer):
    messages.append({'role': 'assistant', 'content': answer})


def append_prompt(messages, prompt):
    messages.append({'role': 'user', 'content': prompt})


def get_answer_from_openai(conversation, stream=False):
    begin = int(time.time())
    chat = openai.ChatCompletion.create(
        model=model_engine,
        messages=conversation,
        max_tokens=2048,
        n=1,
        stop=None,
        temperature=1,
        stream=stream,
    )
    if not stream:
        log_info('open-ai gpt response, elapsed:{0:.2f}s,result:{1}'.format((time.time() - begin), chat))
        answer = chat.choices[0].message.content.strip()
        return answer
    resp = {}
    for r in chat:
        delta = r.choices[0].delta
        for k, v in delta.items():
            print(k, v)
            value = resp.get(k, '')
            resp[k] = value + v
    log_info('open-ai gpt response, elapsed:{0:.2f}s,result:{1}'.format((time.time() - begin), resp))
    return resp['content'].strip()
