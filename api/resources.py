from flask_restful import (Resource, reqparse, abort, fields, marshal_with) 

def abort_if_tosh_doesnt_exist(tosh_id):
    if tosh_id not in TOSHES:
        abort(404, message="Tosh {} doesn't exist".format(tosh_id))

parser = reqparse.RequestParser()
parser.add_argument('name')

tosh_fields = dict(
    name=fields.String,
    date_created = fields.DateTime,
    date_updated = fields.DateTime,
    )


# Tosh
# shows a single tosh item and lets you delete a tosh item
class Tosh(Resource):
    
    @marshal_with(tosh_fields)
    def get(self, tosh_id):
        """
        get a tosh Resource
        ---
        operationId: getTosh
        parameters:
            - name: tosh_id
              in: path
              required: true
              schema:
                type: string         
        responses:
          200:
           description: A single tosh item
           schema:
             $ref: '#/components/schemas/Tosh'
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
        """
        List all the tosh Resources
        ---
        operationId: getToshList
        responses:
          200:
            description: The tosh data
            content:
              application/json:
                schema:
                  type: array
                  items:
                    $ref: '#/components/schemas/ToshList'
        """
        return TOSHES
    
    #@marshal_with(tosh_fields)
    def post(self):
        """
        create a new tosh Resource
        ---
        summary: create a new tosh Resource
        requestBody:
          description: Tosh object that needs to be added to the store
          content:
            application/json:          
              schema:
                $ref: '#/components/schemas/Tosh'
        required: true
        responses:
          201:
            description: The tosh has been created
            content:
              application/json:            
                schema:
                  $ref: '#/components/schemas/Tosh'        
        """          
        args = parser.parse_args()
        print('args:', args)
        tosh_id = int(max(TOSHES.keys()).lstrip('tosh')) + 1
        tosh_id = 'tosh%i' % tosh_id
        TOSHES[tosh_id] = {'name': args['name']}
        return TOSHES[tosh_id], 201

