# Demo 1 - Slide 3

## Graphql Architecture

 - [ ] it is low-cost, for both development and operational dimensions
 - [X] API is extensible, so new data can be readily included
 - [X] schema controls to provide validations as required
 - [ ] data is equally available to internal and external (to GNS) users and systems
 - [X] easy to integrate for both automated tasks and web applications
 - [ ] authorisations provided via standard Oauth2 JWT-token services


**Choices made:**

 - Many styles of API are feasible using this architecure, we've chosen [Graphql](https://graphql.org/) after also 
   revisiting REST using [swagger/openapi](https://swagger.io/docs/specification/about/).
 - Graphql because:
     - client queries can define fields and relations & the servive 'resolves' them
     - stable mature API schemas and implementations in all major languages
     - (micro)service composition (future)
     - subscriptions (future)
 - Graphql in [python 3] using [Graphene](https://docs.graphene-python.org/) and [Flask](https://flask.palletsprojects.com) provide a python class based schema management -> the code builds the docs.
 - client-side there are many graphql libraries and tools to choose from. We'll use python [gql](https://gql.readthedocs.io/en/latest/index.html) for service clients and CLI scripts
 - We're using the Relay graphql extensions to provide pagination and patterns for relational joins.




