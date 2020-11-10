# Toshi python client (nshm-toshi-client)

 - simple integration with your tasks using python
 - install with `pip install -U git+https://github.com/GNS-Science/nshm-toshi-client#egg=nshm_toshi_client`
 - save the API KEY to your environment `export TOSHI_API_KEY_DEV=yadayada`
 - now, in your code.....
 
```
import os
from nshm_toshi_client.rupture_generation_task import RuptureGenerationTask 

S3_URL = "https://nshm-tosh-api-dev.s3.amazonaws.com/" 
API_URL = "https://k6lrxgwqj9.execute-api.ap-southeast-2.amazonaws.com/dev/graphql"
API_KEY = "TOSHI_API_KEY_DEV"

# initialise the client
headers={"x-api-key":os.getenv(API_KEY)}
ruptgen_api = RuptureGenerationTask(API_URL, S3_URL, None, with_schema_validation=True, headers=headers)

#create the new task
task_id = ruptgen_api.create_task(create_args)

#upload a task-file 
file = "file/to/your/file.txt"
ruptgen_api.upload_task_file(task_id, conf_file, 'READ') #one of WRITE, READ. READ_WRITE
```
