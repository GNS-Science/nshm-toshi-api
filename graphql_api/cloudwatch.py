#!cloudwatch

import datetime
import boto3
from api.config import REGION, IS_OFFLINE

# initialize our Cloudwatch client
client = boto3.client('cloudwatch', region_name=REGION)

class ServerlessMetricWriter():

    def __init__(self, lambda_name, metric_name, resolution=60):
        self._lambda_name = lambda_name
        self._metric_name = metric_name
        self._resolution = resolution # 1=high, or 60

    def put_duration(self, package, operation, duration):

        if isinstance(duration, datetime.timedelta):
            duration = float(duration.seconds/1e6 + (duration.microseconds/1e3))

        rec = dict(
            Namespace=f'AWS/Lambda/{self._lambda_name}',
            MetricData=[
                {
                    'MetricName':  self._metric_name,
                    'Dimensions': [
                        {'Name': 'Package', 'Value': package },
                        {'Name': 'Operation', 'Value': operation }
                    ],
                    'Timestamp': datetime.datetime.now(),
                    'Value': duration,
                    'Unit': 'Milliseconds',
                    'StorageResolution': self._resolution
                }
            ]
        )
        if IS_OFFLINE:
            print("CW: ", rec)
        else:
            client.put_metric_data(**rec)
