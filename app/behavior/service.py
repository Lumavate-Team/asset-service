from flask import g, make_response, request, redirect
from lumavate_service_util import get_lumavate_request, LumavateRequest, SecurityAssertion
from lumavate_properties import Properties, Components
from lumavate_exceptions import ApiException, ValidationException
import boto3
import os
import json
import base64
import datetime
from ua_parser import user_agent_parser
from jinja2 import Environment, BaseLoader

class Service():
  def do_properties(self, ic='ic', url_ref='ms'):
    props = []
    #status = str(len(self.get_all())) + ' asset(s)'
    status = ''
    props.append(Properties.Property('Microservice','Microservice Settings', 'adminUI', 'Admin', 'admin-launcher', options=[{'status': status}]))
    return [x.to_json() for x in props]

  def get_s3(self):
    return boto3.resource('s3', aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'), aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'))

  def get_s3_client(self):
    return boto3.client('s3', aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'), aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'))

  def get_bucket(self):
    return os.environ.get('BUCKET_NAME')

  def get_prefix(self):
    return str(g.token_data.get('orgId')) + '/' + str(g.token_data.get('namespace')) + '/'

  def get_all(self):

    def lchop(thestring, ending):
      if thestring.startswith(ending):
        return thestring[len(ending):]
      return thestring

    def rchop(thestring, ending):
      if thestring.endswith(ending):
        return thestring[:-len(ending)]
      return thestring

    files = []
    prefix = self.get_prefix()
    s3 = self.get_s3()
    bucket = s3.Bucket(name=self.get_bucket())
    for obj in bucket.objects.filter(Prefix=prefix):
      raw_file = lchop(obj.key.rstrip('/'), prefix)
      file = rchop(rchop(raw_file, '/draft'), '/production')

      if file == '':
        continue

      file_record = next((x for x in files if x['name'] == file), None)
      if file_record is None:
        file_record = {'name': file, 'isDeleted': False,
          "draft":      {'contentLength': 0, 'etag': "", 'author': "", 'lastModified': ""},
          "production": {'contentLength': 0, 'etag': "", 'author': "", 'lastModified': ""}
        }
        files.append(file_record)

      file_record['url'] = '/ic/assets/' + file

      if raw_file.endswith('/draft'):
        o = s3.Object(self.get_bucket(), obj.key).get()
        file_record['isDeleted'] = o['Metadata'].get('isdeleted', 'false').lower() == 'true'
        file_record['draft'] = {'contentLength': o['ContentLength'], 'etag': o['ETag'], 'author': o['Metadata']['author'], 'lastModified': o['LastModified'].isoformat()}

      if raw_file.endswith('/production'):
        o = s3.Object(self.get_bucket(), obj.key).get()
        file_record['production'] = {'contentLength': o['ContentLength'], 'etag': o['ETag'], 'author': o['Metadata']['author'], 'lastModified': o['LastModified'].isoformat()}


    return files

  def read_content(self):
    data = request.get_json()

    contents = data.get('contents')
    if contents is None:
      raise ValidationException('file must be uploaded as base-64 data', api_field='contents')

    content_type = 'binary/octet-stream'
    content = b''

    if ',' in contents:
      content_type = contents.split(',')[0].split(':')[1].split(';')[0]
      contents = contents.split(',')[1]

    content = base64.b64decode(contents)

    return content, content_type

  def post(self):
    prefix = self.get_prefix()
    file = prefix + request.get_json()['file'] + '/'
    files = self.get_all()
    if next((x for x in files if x['name'] == request.get_json()['file']), None) is not None:
      raise ValidationException('File already exists')

    content, content_type = self.read_content()
    s3 = self.get_s3()

    metadata = {
      'author': g.token_data.get('user'),
      'containerversionid': str(g.token_data.get('containerVersionId'))
    }
    s3.Object(self.get_bucket(), file).put()
    s3.Object(self.get_bucket(), file + 'draft').put(Body=content, Metadata=metadata, ContentType=content_type)
    s3.Object(self.get_bucket(), file + 'production').put(Body=b'', Metadata=metadata, ContentType=content_type)
    return file

  def set_delete_flag(self, path, flag):
    s3 = self.get_s3()
    prefix = self.get_prefix()
    file = prefix + path + '/'
    s3_object = s3.Object(self.get_bucket(), file + 'draft')
    metadata = {
      'author': s3_object.get()['Metadata'].get('author'),
      'containerversionid': str(g.token_data.get('containerVersionId')),
      'isdeleted': str(flag).lower()
    }
    s3_object.copy_from(CopySource={'Bucket':self.get_bucket(), 'Key':file + 'draft'}, Metadata=metadata, MetadataDirective='REPLACE')

  def clear_delete_marker(self, path):
    self.set_delete_flag(path, False)
    return 'Ok'

  def delete(self, path):
    files = self.get_all()
    file = next((x for x in files if x['name'] == path), None)
    if file is None:
      return None

    if file['production']['contentLength'] == 0:
      s3 = self.get_s3()
      prefix = self.get_prefix()
      file = prefix + path + '/'
      s3.Object(self.get_bucket(), file).delete()
      s3.Object(self.get_bucket(), file + 'draft').delete()
      s3.Object(self.get_bucket(), file + 'production').delete()
    else:
      self.set_delete_flag(path, True)

    return file

  def publish(self):
    s3 = self.get_s3()
    prefix = self.get_prefix()
    files = self.get_all()
    for f in files:
      file = prefix + f['name'] + '/'
      if f['isDeleted']:
        s3.Object(self.get_bucket(), file).delete()
        s3.Object(self.get_bucket(), file + 'draft').delete()
        s3.Object(self.get_bucket(), file + 'production').delete()
      else:
        s3.Object(self.get_bucket(),file + 'production').copy_from(CopySource=self.get_bucket() + '/' + file + 'draft')

    return 'Ok'

  def put(self, path):
    data = request.get_json()
    content, content_type = self.read_content()
    prefix = self.get_prefix()
    file = prefix + path + '/'
    s3 = self.get_s3()
    metadata = {
      'Author': g.token_data.get('user'),
      'ContainerVersionId': str(g.token_data.get('containerVersionId'))
    }
    s3.Object(self.get_bucket(), file + 'draft').put(Body=content, Metadata=metadata, ContentType=content_type)

    return 'Ok'

  def get_presign_url(self, method, path=''):

    content_type = request.get_json()['contentType']
    prefix = self.get_prefix()
    file = ''

    if method == 'POST':
      file = prefix + request.get_json()['file'] + '/'
      files = self.get_all()
      if next((x for x in files if x['name'] == request.get_json()['file']), None) is not None:
        raise ValidationException('File already exists')
    else:
      file = prefix + path + '/'

    s3_client =  self.get_s3_client()
    metadata = {
      'author': g.token_data.get('user'),
      'containerversionid': str(g.token_data.get('containerVersionId'))
    }
    metadata_presign = {
      'x-amz-meta-author': g.token_data.get('user'),
      'x-amz-meta-containerversionid': str(g.token_data.get('containerVersionId'))
    }
    #Generate presigned post url good for 3 minutes for upload
    response = s3_client.generate_presigned_post(
        Bucket=self.get_bucket(),
        Key= file + 'draft',
        Fields=metadata_presign,
        Conditions=[
            ['eq', '$Content-Type', content_type],
            {'success_action_status':'201'},
            {'x-amz-meta-author': g.token_data.get('user')},
            {'x-amz-meta-containerversionid': str(g.token_data.get('containerVersionId'))},
        ],
        ExpiresIn=60*15)

    #go ahead and create folder and empty production version
    if method == 'POST':
      s3 = self.get_s3()
      s3.Object(self.get_bucket(), file).put()
      s3.Object(self.get_bucket(), file + 'production').put(Body=b'', Metadata=metadata, ContentType=content_type)

    return response

  def get_file(self,s3, file, max_size=5000000):
    res_file = {}
    s3_client = self.get_s3_client()
    obj = None

    try:
      obj = s3_client.head_object(Bucket=self.get_bucket(), Key=file)
    except: 
      pass

    if obj is None:
      return None
    else:
      if obj['ETag'] == request.headers.get('If-None-Match', ''):
        res_file['match'] = True
        return res_file

      if max_size is not None and obj.get('ContentLength', 0) > max_size:
        try:
          response = s3_client.generate_presigned_url('get_object',
            Params={
              'Bucket': self.get_bucket(),
              'Key': file,
            },
            HttpMethod="GET",
            ExpiresIn=30)

          res_file['url'] = response
          return res_file
        except:
          return None 
      else:
        res_file['file'] = s3.Object(self.get_bucket(), file).get()
        return res_file
    
  def get_contents(self, path, version):
    s3 = self.get_s3()
    prefix = self.get_prefix()
    file = prefix + path + '/' + version
    obj = None
    file_obj = None
    should_translate = False

    try:
      file_obj = self.get_file(s3, file)
    except:
      pass

    if file_obj is None:
      file = prefix + path + ".j2/" + version

      try:
        file_obj = self.get_file(s3, file, max_size=None)
        obj = file_obj.get('file', None)

        if file_obj.get('match', False):
          return '', 304
        else:
          contents = obj['Body'].read(obj['ContentLength']).decode('UTF-8')
          user_agent_string = request.headers.get('User-Agent')
          parsed_user_agent = user_agent_parser.Parse(user_agent_string)
          j2_dict = {}
          j2_dict['userAgent'] = parsed_user_agent
          jinja_env = Environment(loader=BaseLoader)

          
          template = jinja_env.from_string(contents)
          parsed_contents = template.render(**j2_dict)                  

          r = make_response(parsed_contents)
          r.headers["Content-Type"] = obj['ContentType']
          r.headers['ETag'] = obj['ETag']
          return r
      except Exception as e: 
        return None

    elif file_obj.get('match', False):
      return '', 304
    elif file_obj.get('url', None) is not None:
      return redirect(file_obj.get('url'), 302)
    else:
      obj= file_obj.get('file')
      contents = obj['Body'].read(obj['ContentLength'])
      r = make_response(contents)
      r.headers["Content-Type"] = obj['ContentType']
      r.headers['ETag'] = obj['ETag']
      return r
