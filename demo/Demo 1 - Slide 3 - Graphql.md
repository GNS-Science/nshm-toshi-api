# Graphql

 - We've chosen [Graphql](https://graphql.org/) after also 
   revisiting REST using [swagger/openapi](https://swagger.io/docs/specification/about/).
 - Graphql because:
     - client queries can define fields and relations & the servive 'resolves' them
     - stable mature API schemas and implementations in all major languages
     - (micro)service composition (future)
     - subscriptions (future)
 - Implemented in **python 3** using **[Graphene](https://docs.graphene-python.org/)** and **[Flask](https://flask.palletsprojects.com)** 
 - a python class based schema management -> the code builds the docs.
 - client-side we'll use python **[gql](https://gql.readthedocs.io/en/latest/index.html)** for simple service clients and CLI scripts
 - **Relay** graphql standard provides pagination and nodeIds patterns.




