from lumavate_service_util import lumavate_route, lumavate_manage_route, SecurityType, RequestType
from flask import render_template, request, g
from behavior import Service

@lumavate_route('/', ['GET'], RequestType.page, [SecurityType.jwt])
def root():
  return render_template('home.html', logo='/{}/{}/discover/icons/microservice.png'.format(g.integration_cloud, g.widget_type))


@lumavate_manage_route('/files', ['POST', 'GET'], RequestType.api, [SecurityType.jwt], required_roles=['admin', 'collaborator'])
def files():
  if request.method == 'GET':
    return Service().get_all()
  else:
    return Service().post()

@lumavate_manage_route('/', ['GET'], RequestType.page, [SecurityType.jwt], required_roles=['admin', 'collaborator'])
def manage():
  return render_template('manage.html')

@lumavate_route('/discover/manage', ['GET'], RequestType.system, [SecurityType.jwt])
def discover_manage():
  return {
    'context': ['experience', 'studio']
  }

@lumavate_manage_route('/files/<path:path>', ['DELETE', 'GET', 'PUT'], RequestType.api, [SecurityType.jwt], required_roles=['admin', 'collaborator'])
def manage_file(path):
  if request.method == 'DELETE':
    return Service().delete(path)
  elif request.method == 'GET':
    return path
  else:
    return Service().put(path)

@lumavate_manage_route('/files/<path:path>/delete-marker', ['DELETE'], RequestType.api, [SecurityType.jwt], required_roles=['admin', 'collaborator'])
def clear_delete_marker(path):
  return Service().clear_delete_marker(path)

@lumavate_manage_route('/on-publish', ['POST'], RequestType.api, [SecurityType.jwt], required_roles=['admin', 'collaborator'])
def publish():
  return Service().publish()

@lumavate_manage_route('/files/<path:path>/draft', ['GET'], RequestType.page, [SecurityType.jwt], required_roles=['admin', 'collaborator'])
def draft(path):
  return Service().get_contents(path, 'draft')

@lumavate_manage_route('/files/<path:path>/production', ['GET'], RequestType.page, [SecurityType.jwt], required_roles=['admin', 'collaborator'])
def production(path):
  return Service().get_contents(path, 'production')

@lumavate_route('/discover/properties', ['GET'], RequestType.system, [SecurityType.jwt])
def properties():
  return Service().do_properties()

@lumavate_route('/files', ['GET'], RequestType.api, [SecurityType.jwt])
def files(path):
  return None

@lumavate_route('/<path:path>', ['GET'], RequestType.page, [SecurityType.jwt])
def file(path):
  return Service().get_contents(path, 'draft')
