#Example hacked from https://flask-restful.readthedocs.io/en/latest/quickstart.html
from flask import Flask
from flask_restful import (reqparse, abort, Api, Resource, 
                           fields, marshal_with) 

from flasgger import Swagger

app = Flask(__name__)
api = Api(app)

swagger_config = {
    'uiversion': 3,
    "headers": [],
    "swagger": "2.0",
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
}

#note pinned at 3.25.5 as newer versions of 3 are breaking
swagger_config['swagger_ui_bundle_js'] = '//unpkg.com/swagger-ui-dist@3.25.5/swagger-ui-bundle.js'
swagger_config['swagger_ui_standalone_preset_js'] = '//unpkg.com/swagger-ui-dist@3.25.5/swagger-ui-standalone-preset.js'
swagger_config['swagger_ui_css'] = '//unpkg.com/swagger-ui-dist@3.25.5/swagger-ui.css'
swagger_config['jquery_js'] = '//unpkg.com/jquery@2.2.4/dist/jquery.min.js'


template = {
  "info": {
    "title": "NSHM Tosh API",
    "description": "API for tests, outputs, stuff and heiroglyphs",
    "contact": {
      "responsibleOrganization": "GNS Science",
      "responsibleDeveloper": "NSHM Service Delivery Team",
      "email": "nshm-service-delivery@gns.cri.nz",
      "url": "https://www.gns.cri.nz",
    },
    "version": "0.0.2"
  },
  "schemes": [
    "http",
    "https"
  ]
}

#  "host": "mysite.com",  # overrides localhost:500
#  "basePath": "/api",  # base bash for blueprint registration

swagger = Swagger(app, template=template, config=swagger_config)

tosh_fields = dict(
    name=fields.String,
    date_created = fields.DateTime,
    date_updated = fields.DateTime,

    )
    
TOSHES = {
    'tosh1': {'name': 'build an API'},
    'tosh2': {'name': '?????'},
    'tosh3': {'name': 'profit!'},
}

def abort_if_tosh_doesnt_exist(tosh_id):
    if tosh_id not in TOSHES:
        abort(404, message="Tosh {} doesn't exist".format(tosh_id))

parser = reqparse.RequestParser()
parser.add_argument('name')


# Tosh
# shows a single tosh item and lets you delete a tosh item
class Tosh(Resource):
    
    @marshal_with(tosh_fields)
    def get(self, tosh_id):
        """
        get a tosh Resource
        ---
        tags:
          - restful
        parameters:
         - in: path
           name: tosh_id
           type: string
           required: true
        responses:
          200:
           description: A single tosh item
           schema:
             id: Tosh
             properties:
               name:
                 type: string
                 description: The name of the tosh
                 default: Steven Wilson
        """        
        abort_if_tosh_doesnt_exist(tosh_id)
        return TOSHES[tosh_id]

    def delete(self, tosh_id):
        abort_if_tosh_doesnt_exist(tosh_id)
        del TOSHES[tosh_id]
        return '', 204
    
    @marshal_with(tosh_fields)
    def put(self, tosh_id):
        abort_if_tosh_doesnt_exist(tosh_id)
        args = parser.parse_args()
        tosh = {'name': args['name']}
        TOSHES[tosh_id] = tosh
        return tosh, 201


# ToshList
# shows a list of all toshs, and lets you POST to add new tasks
class ToshList(Resource):
    def get(self):
        return TOSHES
    
    #@marshal_with(tosh_fields)
    def post(self):
        """
        create a new tosh Resource
        ---
        tags:
          - restful
        parameters:
          - in: body
            name: body
            schema:
              $ref: '#/definitions/Tosh'
        responses:
          201:
            description: The tosh has been created
            schema:
              $ref: '#/definitions/Tosh'
        """          
        args = parser.parse_args()
        print('args:', args)
        tosh_id = int(max(TOSHES.keys()).lstrip('tosh')) + 1
        tosh_id = 'tosh%i' % tosh_id
        TOSHES[tosh_id] = {'name': args['name']}
        return TOSHES[tosh_id], 201

##
## Actually setup the Api resource routing here
##
api.add_resource(ToshList, '/tosh')
api.add_resource(Tosh, '/tosh/<tosh_id>')


if __name__ == '__main__':
    app.run(debug=True)