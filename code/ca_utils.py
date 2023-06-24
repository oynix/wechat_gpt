import os
import base64
import requests
from qcloud_cos import CosConfig, CosS3Auth
from logger import log_info


# content auditing 内容审核
ca_app_id = os.environ.get('CA_APP_ID', '')
ca_secret_id = os.environ.get('CA_SECRET_ID', '')
ca_secret_key = os.environ.get('CA_SECRET_KEY', '')
ca_bucket = os.environ.get('CA_BUCKET', '')
ca_region = os.environ.get('CA_BUCKET_REGION', '')
ca_config = CosConfig(Region=ca_region, SecretId=ca_secret_id, SecretKey=ca_secret_key, Token=None, Scheme='https')

#  1:porn, 2:terrorist, 4:politics, 8:ads, 16: Illegal, 32:Abuse
ca_request_format = """<Request>
  <Input>
    <Content>{0}</Content>
  </Input>
  <Conf>
    <DetectType>Porn,Politics,Illegal,Abuse</DetectType>
    <Callback></Callback>
    <BizType></BizType>
  </Conf>
</Request>"""


def content_audit(content):
    body = ca_request_format.format(str(base64.b64encode(content.encode('utf-8')), 'utf-8'))
    # host: <BucketName-APPID>.ci.<Region>.myqcloud.com
    host = '{0}-{1}.ci.{2}.myqcloud.com'.format(ca_bucket, ca_app_id, ca_region)
    url = 'https://{0}/text/auditing'.format(host)
    path = '/text/auditing'
    headers = {'Content-Type': 'application/xml', 'Host': host}
    resp = requests.post(url, data=body, headers=headers, auth=CosS3Auth(ca_config, path))
    log_info('ci body:{}'.format(body))
    log_info('ci resp:{}'.format(resp.text))
    return resp

