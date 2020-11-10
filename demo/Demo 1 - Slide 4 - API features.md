# API current features:

 - **Task** (interface) is designed to handle custom schema implementations
     - custom schema for **opensha RuptureGenerationTask** 
     - next ??
 - **File** class with upload/download contents via S3 **presigned url** GET/POST methods
 - some testing examples with **mocked S3** calls
 - **TaskFile** objects for File<-N-to-N->Task relationships
 - simple **authorisation** via header token X-API-KEY
 
## Task 
 - **id** the unique task id
 - **started** - iso8601 timestamp
 - **result** - one of (FAILURE, SUCCESS, UNDEFINED)
 - **state** - one of (SCHEDULED, STARTED, DONE, UNDEFINED)
 - **duration** time in seconds
 
## RuptureGenerationTask
 - **arguments** - the parameters passed to each task (.e.g. max jump distance)
 - **metrics** - metadata collected from the task process (e.g number of ruptures
 - **gitrefs** - version(s) of sofware used to reproduce
 - **files** - inputs and outputs

