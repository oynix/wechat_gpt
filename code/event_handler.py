from xml.etree.ElementTree import Element

subscribe_resp = '欢迎关注'


def handle_event(body: Element):
    event = body.find('Event').text
    if event == 'subscribe':
        return subscribe_resp

    return 'success'
