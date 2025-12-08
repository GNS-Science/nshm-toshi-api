import datetime
import hashlib
import io
import json
from unittest.mock import MagicMock

import pytest
import requests
from graphql_relay import from_global_id
from moto import mock_aws

import graphql_api.data.data_manager  # for monkeypatch
from graphql_api.config import ES_ENDPOINT, REGION, S3_BUCKET_NAME
from graphql_api.dynamodb.models import migrate


@pytest.fixture(autouse=True)
def patch_the_search(monkeypatch):
    monkeypatch.setattr(graphql_api.data.data_manager.dm_instance, '_search_manager', MagicMock())


@pytest.mark.parametrize(
    "upload_option, message",
    [
        (0, "boto3"),
        (1, "requests"),
    ],
)
@mock_aws()
def test_create_rupture_set_and_upload_file_using_method(
    upload_option, message, graphql_client, s3_client, rupture_generation_task, create_rupture_set_mutation
):

    # sanity check our setup
    print("*" * 40)
    print(f"REGION: {REGION}")
    print(f"S3_BUCKET_NAME: {S3_BUCKET_NAME}")
    print(f"ES_ENDPOINT: {ES_ENDPOINT}")
    print("*" * 40)

    # prepare the fake rupture file
    file_name = "a_line_or_two.txt"
    file_content = "a line\nor two\n"
    filedata = io.BytesIO(file_content.encode())
    digest = hashlib.sha256(filedata.read()).hexdigest()
    filedata.seek(0)  # important!
    size = len(filedata.read())
    filedata.seek(0)  # important!

    # Now create the Rupture Generation task
    executed = graphql_client.execute(
        create_rupture_set_mutation,
        variable_values=dict(
            created=datetime.datetime.now(datetime.UTC),
            md5_digest=digest,
            file_name=file_name,
            file_size=size,
            produced_by=rupture_generation_task['id'],
            metrics=[{"k": "some_metric", "v": "20"}],
            arguments=[dict(k="random_arg", v="A")],
            fault_models=["ModelA", "ModelB"],
        ),
    )

    rupture_set = executed['data']['create_rupture_set']['rupture_set']

    # get the post_url metadata returned by the API mutation, there are two versions
    # becuase this test needs data that was not return in the orignal `post_url`
    #
    post_url = json.loads(rupture_set["post_url"])
    post_url_v2 = rupture_set["post_url_v2"]
    post_data_v2 = json.loads(rupture_set["post_data_v2"])

    print(post_url_v2)
    assert post_url == post_data_v2

    # We use a pre-authorised post_url because our serverless API will not support large file upload via the API
    # instead, we create a temporary pre-authorized upload URL that the API client can use to upload.
    #
    # In the first example our S3 client has the same AccessAuthority as the API server, so it can use the S3 client directly
    # but this will not be the case in wild.
    #
    # In the second example we use the pre-signed URL just as the toshi client does.

    if upload_option == 0:
        #  Use the authorized boto3 `s3_client` (which is NOT available to a real-world ToshiAPI client) to
        #  upload the file content directly.
        s3_client.put_object(Bucket=S3_BUCKET_NAME, Key=post_url['key'], Body=filedata)

    elif upload_option == 1:
        # Use `requests` library to perform the multi-part form upload to the pre-signed URL
        # Moto mocking intercepts this request and processes it locally.
        files = {'file': filedata}
        response = requests.post(post_url_v2, data=post_data_v2, files=files)
        assert response.status_code == 204  # AWS S3 returns a 204 on successful POST upload

    else:
        raise NotImplementedError(f"no implementation for upload_option: {upload_option}")

    # Verify the object exists and has the correct content in the mock S3
    # we should get the same result using either method
    response = s3_client.get_object(Bucket=S3_BUCKET_NAME, Key=post_url['key'])
    content = response['Body'].read()
    assert content.decode('utf-8') == file_content
