import datetime
import hashlib
import os
import json

mount_dir = '/home/app/{0}'.format(os.getenv('MOUNT', 'dev'))


class Utils:

    @staticmethod
    def verify_signature(sig, timestamp, nonce, token):
        arr = [timestamp, nonce, token]
        arr.sort()
        sha = hashlib.sha1()
        sha.update(''.join(arr).encode())
        s = sha.hexdigest()
        return s == sig

    # @staticmethod
    # def sub_element(root, tag, text):
    #     e = ET.SubElement(root, tag)
    #     e.text = text
    #     e.tail = '\n'

    # @staticmethod
    # def sub_element_cdata(root, tag, text):
    #     t = '<![CDATA[%s]]>' % text
    #     Utils.sub_element(root, tag, t)

    @staticmethod
    def get_user_pdf_dir(user_id):
        """
        用户存储pdf文件的目录：{mount_dir}/data/pdf/{user_id}/
        """
        return '{0}/data/pdf/{1}'.format(mount_dir, user_id)

    @staticmethod
    def get_user_profile_name(user_id):
        """
        用户profile文件存储位置：{mount_dir}/data/{year}/{month}/{day}/{user_id}/profile.json
        """
        today = datetime.datetime.today()
        return '{0}/data/{1}/{2}/{3}/{4}/profile.json'.format(mount_dir, today.year, today.month, today.day, user_id)

    @staticmethod
    def get_msg_chat_name(user_id, msg_id):
        """
        消息对话文件存储位置：{mount_dir}/data/{year}/{month}/{day}/{user_id}/msg/{msg_id}.json
        """
        today = datetime.datetime.today()
        return '{0}/data/{1}/{2}/{3}/{4}/msg/{5}.json'.format(mount_dir, today.year, today.month, today.day, user_id, msg_id)

    @staticmethod
    def get_chat_messages_name(user_id):
        """
        对话上下文文件存储位置：{mount_dir}/data/{year}/{month}/{day}/{user_id}/messages.json
        """
        today = datetime.datetime.today()
        return '{0}/data/{1}/{2}/{3}/{4}/messages.json'.format(mount_dir, today.year, today.month, today.day, user_id)

    @staticmethod
    def get_messages_back_name(user_id, timestamp):
        """
        对话上下文备份存储位置：{mount_dir}/data/{year}/{month}/{day}/{user_id}/messages_backup_{timestamp}.json
        """
        today = datetime.datetime.today()
        return '{0}/data/{1}/{2}/{3}/{4}/messages_backup_{5}.json'.format(mount_dir, today.year, today.month, today.day, user_id, timestamp)

    @staticmethod
    def get_log_file_name(file_name=None):
        """
        日志文件存储位置 {mount_dir}/log/{year}/{month}/{day}/{file_name}.txt
        如果不指定，就存到app.txt文件里
        """
        today = datetime.datetime.today()
        return '{0}/log/{1}/{2}/{3}/{4}.txt'.format(mount_dir, today.year, today.month, today.day, file_name)

    @staticmethod
    def format_values(data):
        """格式化headers和params中的values为bytes"""
        for i in data:
            data[i] = Utils.to_bytes(data[i])
        return data

    @staticmethod
    def to_bytes(data):
        return data.encode('utf-8')


class UserProfile:

    def __init__(self, msg_id='', msg_n=0, last_gpt_msg_id=None):
        self.msg_id = msg_id  # 当前正在处理的消息id，等gpt返回结果
        self.msg_n = msg_n  # 一条消息最多3次，第3次的时候必须返回结果
        self.last_gpt_msg_id = last_gpt_msg_id  # 上一条问gpt的id

    def to_dict(self):
        return {'msg_id': self.msg_id, 'msg_n': self.msg_n, 'last_gpt_msg_id': self.last_gpt_msg_id}

    @staticmethod
    def from_json(d: dict):
        return UserProfile(d['msg_id'], d['msg_n'], d['last_gpt_msg_id'])


def dump(file_name, obj_dict):
    parent = os.path.dirname(file_name)
    if not os.path.exists(parent):
        os.makedirs(parent, exist_ok=True)
    with open(file_name, mode='w', encoding='utf-8') as f:
        json.dump(obj_dict, f, ensure_ascii=False)


def load(file_name, object_hook=None):
    if not os.path.exists(file_name):
        return None
    with open(file_name, mode='rt', encoding='utf-8') as f:
        return json.load(f, object_hook=object_hook)

