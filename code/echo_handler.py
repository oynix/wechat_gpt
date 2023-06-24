from utils import Utils, load, UserProfile
from logger import log_info


def handle_echo(user_id: str):
    profile_file_name = Utils.get_user_profile_name(user_id)
    profile = load(profile_file_name, object_hook=UserProfile.from_json)
    if profile is None or not profile.last_gpt_msg_id:
        return '没有历史记录'

    last_chat_file_name = Utils.get_msg_chat_name(user_id, profile.last_gpt_msg_id)
    last_chat = load(last_chat_file_name)
    if not last_chat['reply']:
        return '答案还在路上，还得再等等'

    q = last_chat['msg']
    a = last_chat['reply'] if last_chat['permit'] is True else '这个问题我不便回答'
    return '{0}\n\n{1}'.format(q, a)
