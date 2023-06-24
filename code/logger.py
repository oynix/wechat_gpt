from flask import request
from utils import Utils
import os
import time


def log_info(msg):
    environ = os.environ.get('ENVIRON')
    if not environ:
        print(msg)
        return

    info_format = '{0} {1} {2} {3}\n'
    request_id = request.environ.get('Request-Id', 'app')
    log_file_path = Utils.get_log_file_name(request_id)
    if not os.path.exists(log_file_path):
        parent = os.path.dirname(log_file_path)
        if not os.path.exists(parent):
            os.makedirs(parent, exist_ok=True)
    with open(log_file_path, mode='a') as f:
        log_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        tag = request_id
        level = '[INFO]'
        f.write(info_format.format(log_time, tag, level, msg))
