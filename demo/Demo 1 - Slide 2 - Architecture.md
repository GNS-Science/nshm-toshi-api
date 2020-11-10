# Serverless Architecture

To meet these requirements

 - [X] it is low-cost, for both development and operational dimensions
 - [X] data is equally available to internal and external (to GNS) users and systems
 - [X] easy to integrate for both automated tasks and web applications

Solution:

 - **[serverless.com](https://www.serverless.com)** framework to bootstrap and standardise serverless architectures.
      - **DEMO** `sls info --stage dev --aws-profile tosh-api`
 - Harness the **free-tier AWS services**,so the entire stack will cost < a few cent's per day.
 - **AWS S3** provides cloud data storage, and all the metadata is stored as json files in S3.
      - **DEMO** the S3 object backet naming and json contents.
 - **AWS Lambda** is their *serverless function* - here we're running a python Flask web server as a 'function'   
 - API standard = **Graphql + Relay** 
