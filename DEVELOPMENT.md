# Development

Pre-requisites on your development machine:

 - Python3
 - virtualenv
 - NodeJS & the serverless framework, 
   https://www.serverless.com/framework/docs/providers/aws/guide/quick-start
 
And for actual AWS use 
 - an S3 'free tier' account
 - an S3 role ready for SLS deployment, 
   https://www.serverless.com/framework/docs/providers/aws/guide/credentials/
 
 

for new developers getting started...
## 1. Clone repo, create & activate the python3 virtualenv

```
git clone git@github.com:GNS-Science/nshm-toshi-api.git
virtualenv -p python3 nshm-toshi-api
cd nshm-toshi-api/
source bin/activate
```

## 2. setup serverless using NPM

In the project root folder, run `npm install`.

This installs the serverless plugin devDependencies defined in `package.json`.


