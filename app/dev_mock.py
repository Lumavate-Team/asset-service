from lumavate_properties import Properties, Components
from lumavate_service_util import LumavateMockRequest, set_lumavate_request_factory, DevMock
from lumavate_token import AuthToken
import json

class ServiceDevMock(DevMock):
  def get_auth_token(self):
    t = super().get_auth_token()
    t.auth_url = 'http://localhost:5002/'
    return t

  def get_property_data(self):
    sd = super().get_property_data()
    return sd

  def get_auth_token(self):
    t = super().get_auth_token()
    t.company_id = 1
    return t

  def get_auth_data(self):
    return {
      'roles': [
        'Super Admin',
        'Admins'
      ],
      'status': 'active',
      'user': 'ic/magiclink|email|2'
    }
