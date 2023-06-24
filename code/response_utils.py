import time
from flask import Response
from logger import log_info


text_resp_format = """<xml>
<ToUserName><![CDATA[{0}]]></ToUserName>
<FromUserName><![CDATA[{1}]]></FromUserName>
<CreateTime>{2}</CreateTime>
<MsgType><![CDATA[text]]></MsgType>
<Content><![CDATA[{3}]]></Content>
</xml>"""

img_resp_format = """<xml>
<ToUserName><![CDATA[{0}]]></ToUserName>
<FromUserName><![CDATA[{1}]]></FromUserName>
<CreateTime>{2}</CreateTime>
<MsgType><![CDATA[image]]></MsgType>
<Image>
    <MediaId><![CDATA[{3}]]></MediaId>
</Image>
</xml>"""


def send_text_response(gh_id: str, user_id: str, msg: str):
    resp_body = text_resp_format.format(user_id, gh_id, int(time.time()), msg)
    return send_response(resp_body, headers={'Content-Type': 'text/xml'})


def send_img_response(gh_id: str, user_id: str, media_id: str):
    resp_body = img_resp_format.format(user_id, gh_id, int(time.time()), media_id)
    return send_response(resp_body, headers={'Content-Type': 'text/xml'})


def send_response(body, status_code=200, headers=None):
    resp = Response(body, status_code, headers)
    log_info('resp headers:{}'.format(resp.headers))
    log_info('resp_body:{}'.format(body))
    return resp
