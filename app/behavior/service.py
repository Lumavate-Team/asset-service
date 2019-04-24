from flask import g
from lumavate_service_util import get_lumavate_request, LumavateRequest, SecurityAssertion
from lumavate_properties import Properties, Components
from lumavate_exceptions import ApiException

class Service():
  def do_properties(self, ic='ic', url_ref='ms'):
    props = []
    props.append(Properties.Property('Microservice','Microservice Settings', 'adminUI', 'Admin', 'admin-launcher', options=[{'status': ''}]))
    return [x.to_json() for x in props]
