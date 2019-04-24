from lumavate_service_util import lumavate_route, lumavate_manage_route, SecurityType, RequestType
from flask import render_template, g, request, make_response
from behavior import Service

import boto3
import os
import json
import base64
import datetime

@lumavate_route('/', ['GET'], RequestType.page, [SecurityType.jwt])
def root():
  return render_template('home.html', logo='/{}/{}/discover/icons/microservice.png'.format(g.integration_cloud, g.widget_type))

@lumavate_manage_route('/files', ['POST', 'GET'], RequestType.api, [SecurityType.jwt], required_roles=[])
def files():
  if request.method == 'GET':
    files = []
    prefix = str(g.token_data.get('orgId')) + '/' + g.token_data.get('namespace') + '/'
    s3 = boto3.resource('s3')
    bucket = s3.Bucket(name=os.environ.get('BUCKET_NAME'))
    for obj in bucket.objects.filter(Prefix=prefix):
      file = obj.key.rstrip('/').lstrip(prefix)
      if file != '' and not (file.endswith('/draft') or file.endswith('/production')):
        files.append({'name': file})

    return files
  else:
    prefix = str(g.token_data.get('orgId')) + '/' + g.token_data.get('namespace') + '/'
    file = prefix + request.get_json()['file'] + '/'
    s3 = boto3.resource('s3')
    s3.Object(os.environ.get('BUCKET_NAME'), file).put()
    s3.Object(os.environ.get('BUCKET_NAME'), file + 'draft').put(Body=b'')
    s3.Object(os.environ.get('BUCKET_NAME'), file + 'production').put(Body=b'')
    return file

@lumavate_manage_route('/', ['GET'], RequestType.page, [SecurityType.jwt], required_roles=[])
def manage():
  return render_template('manage.html')

@lumavate_route('/discover/manage', ['GET'], RequestType.system, [SecurityType.jwt])
def discover_manage():
  return {
    'context': ['experience']
  }

@lumavate_manage_route('/files/<path:path>', ['DELETE', 'GET', 'PUT'], RequestType.api, [SecurityType.jwt], required_roles=[])
def file(path):
  print(path, flush=True)
  if request.method == 'DELETE':
    s3 = boto3.resource('s3')
    prefix = str(g.token_data.get('orgId')) + '/' + g.token_data.get('namespace') + '/'
    file = prefix + path + '/'
    s3.Object(os.environ.get('BUCKET_NAME'), file).delete()
    s3.Object(os.environ.get('BUCKET_NAME'), file + 'draft').delete()
    s3.Object(os.environ.get('BUCKET_NAME'), file + 'production').delete()
    return path
  elif request.method == 'GET':
    return path
  else:
    data = request.get_json()
    contents = data.get('contents')
    print(data, flush=True)

    if contents is not None:
      content_type = 'binary/octet-stream'
      if ',' in contents:
        content_type = contents.split(',')[0].split(':')[1].split(';')[0]
        contents = contents.split(',')[1]

      bytes = base64.b64decode(contents)
      prefix = str(g.token_data.get('orgId')) + '/' + g.token_data.get('namespace') + '/'
      file = prefix + path + '/'
      s3 = boto3.resource('s3')
      metadata = {'Author': 'j.lawrence@lumavate.com'}
      print(file, flush=True)
      s3.Object(os.environ.get('BUCKET_NAME'), file + 'draft').put(Body=bytes, Metadata=metadata, ContentType=content_type)

    return 'Ok'

@lumavate_manage_route('/files/<path:path>/draft', ['GET'], RequestType.page, [SecurityType.jwt], required_roles=[])
def draft(path):
  s3 = boto3.resource('s3')
  prefix = str(g.token_data.get('orgId')) + '/' + g.token_data.get('namespace') + '/'
  file = prefix + path + '/draft'

  obj = s3.Object(os.environ.get('BUCKET_NAME'), file).get()
  contents = obj['Body'].read(obj['ContentLength'])
  r = make_response(contents)
  r.headers["Content-Type"] = obj['ContentType']
  return r

@lumavate_manage_route('/files/<path:path>/production', ['GET'], RequestType.page, [SecurityType.jwt], required_roles=[])
def production(path):
  s3 = boto3.resource('s3')
  prefix = str(g.token_data.get('orgId')) + '/' + g.token_data.get('namespace') + '/'
  file = prefix + path + '/production'

  obj = s3.Object(os.environ.get('BUCKET_NAME'), file).get()
  contents = obj['Body'].read(obj['ContentLength'])
  r = make_response(contents)
  r.headers["Content-Type"] = obj['ContentType']
  return r

@lumavate_route('/discover/properties', ['GET'], RequestType.system, [SecurityType.jwt])
def properties():
  return Service().do_properties()
