# Demo 1 - Slide 2

## Serverless Architecture

Here we look at the technical choices used to meet these requirements

 - [X] it is low-cost, for both development and operational dimensions
 - [ ] API is extensible, so new data can be readily included
 - [ ] schema controls to provide validations as required
 - [X] data is equally available to internal and external (to GNS) users and systems
 - [X] easy to integrate for both automated tasks and web applications
 - [ ] authorisations provided via standard Oauth2 JWT-token services


Choices:

 - the [serverless.com](https://www.serverless.com) development framework to bootstrap and standardise serverless architectures.
    **DEMO** a fresh deployment to the AW cloud showing the artefacts created.
 - **AWS Lambda** and **AWS S3** (plus API GW, Cloud\*) are all free-tier AWS services. The entire product is
   able to be run for < a few cent's per day.
 - Using S3 natively provides a ubiquitous data storage service, and  nough metadata is stored directly in S3 to make it feasible to use the data independently of the API layer.
   **DEMO** take a look at the S3 object naming and json contents.
 - Many styles of API are feasible using this architecure, we've chosen Graphql...
