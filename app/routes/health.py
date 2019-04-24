from flask import Blueprint, jsonify

health_blueprint = Blueprint('health_blueprint', __name__)

@health_blueprint.route('/<string:integration_cloud>/<string:widget_type>/discover/health', methods=['GET'])
def health(integration_cloud, widget_type):
  return jsonify({'status': 'Ok'})
