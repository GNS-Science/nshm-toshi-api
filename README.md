# nshm-tosh-api
Where all out tests and outputs are buried  - like so much old fashioned, tedious tosh.


# serverless setup


following guidance here:

https://www.serverless.com/blog/flask-python-rest-api-serverless-lambda-dynamodb/


pre-requisites: 
 - nodejs
 - npm (the node package manager

```
sudo npm install -g serverless

```



## OPTION A openapi-generator

`npx @openapitools/openapi-generator-cli generate -i swagger.yaml -g python-flask -o openapi`

