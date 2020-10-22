# Example hacked from https://flask-restful.readthedocs.io/en/latest/quickstart.html
# and https://github.com/flasgger/flasgger/blob/master/examples/restful.py

from flask import Flask
from . import resources
from flask_restful import Api 
from flasgger import Swagger

app = Flask(__name__)
api = Api(app)

swagger_config = {
    'uiversion': 3,
    "headers": [],
    "openapi": "3.0.1",
    "specs": [
        {
            "endpoint": "swagger",
            "route": "/apidocs/swagger.json",
            "rule_filter": lambda rule: True,  # all in
            "model_filter": lambda tag: True,  # all in
        }
    ],
    "static_url_path": "/apidocs/static",
    "swagger_ui": True,
    "specs_route": "/apidocs/",
    "servers": [
        {
            "url": "http://127.0.0.1:5000/",
            "description": "local Sandbox server (uses test data)"
        },
        {
            "url": "https://r8kvgr6g09.execute-api.ap-southeast-2.amazonaws.com/dev/",
            "description": "AWS dev  (uses test data)"
        }
    ],
    "schemes": [
        "http",
        "https"
    ],
    "components": {
        'schemas': {
            'Tosh': {
                'type': 'object',
                'properties': {
                    'name': {
                        'type': 'string'
                    }
                }
            },
            'ToshList': {
                'type': 'object',
                'properties': {
                    'tosh_id': { 
                        'type': 'string',
                        'properties': {},
                        'tosh': {
                            '$ref': '#/components/schemas/Tosh'
                        },
                    }
                }
            }                
        }
    }
}

#note pinned at 3.25.5 as newer versions of 3 are breaking
# swagger_config['swagger_ui_bundle_js'] = '//unpkg.com/swagger-ui-dist@3.25.5/swagger-ui-bundle.js'
# swagger_config['swagger_ui_standalone_preset_js'] = '//unpkg.com/swagger-ui-dist@3.25.5/swagger-ui-standalone-preset.js'
# swagger_config['swagger_ui_css'] = '//unpkg.com/swagger-ui-dist@3.25.5/swagger-ui.css'
# swagger_config['jquery_js'] = '//unpkg.com/jquery@2.2.4/dist/jquery.min.js'

template = {
  "info": {
    "title": "NSHM Tosh API",
    "description": "National Seismic Hazard Model use this API to manage tests, outputs, stuff and heiroglyphs",
    "contact": {
      "email": "nshm-service-delivery@gns.cri.nz",
      "url": "https://www.gns.cri.nz",
    },
    "version": "0.0.2"
  }, 
}

#  "host": "mysite.com",  # overrides localhost:500
#  "basePath": "/api",  # base bash for blueprint registration

swagger = Swagger(app, template=template, config=swagger_config)
    
# populate some dummy data
resources.TOSHES = {
    'tosh1': {'name': 'build an API'},
    'tosh2': {'name': '?????'},
    'tosh3': {'name': 'profit!'},
}

##
## Actually setup the Api resource routing here
##
api.add_resource(resources.ToshList, '/tosh')
api.add_resource(resources.Tosh, '/tosh/<tosh_id>')


if __name__ == '__main__':
    app.run(debug=True)