# Demo 1 - Slide N

## API current features:

 - **Task** (interface) is designed to handle custom schema implementations
 - one custom schema for **opensha rupture generation tasks** ruptureGeneration
 - data handlers for **Amazon S3** bucket storage
 - **File** class with upload/download contents via S3 **presigned url** GET/POST methods
 - some testing examples with **mocked S3** calls
 - **TaskFile** objects for File<-N-to-N->Task relationships
 - simple **authorisation** via header token X-API-KEY
 - **automated AWS deployment** defined in serverless.yml



