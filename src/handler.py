from __future__ import print_function
import os
import uuid
import json

import boto3
import rasterio


s3_client = boto3.client('s3')


def parse_s3_event(event):
    sns_message = json.loads(event['Records'][0]['Sns']['Message'])
    s3_event = sns_message['Records'][0]['s3']

    bucket = s3_event['bucket']['name']
    key = s3_event['object']['key']
    return bucket, key


def lambda_handler(event, context):
    bucket, key = parse_s3_event(event)
    print('INPUT', bucket, key)

    base = os.path.split(key)[1]
    output_bucket = "perrygeo-test"
    output_key = "{}_profile.json".format(base)
    print('OUTPUT', output_bucket, output_key)

    json_path = "/tmp/{}_{}_profile.json".format(uuid.uuid4(), base)

    with rasterio.open('s3://{}/{}'.format(bucket, key)) as src:
        with open(json_path, 'w') as dst:
            profile = dict({k: v for k, v in src.profile.items() if k != 'crs'})
            dst.write(json.dumps(profile))
        print("Rasterio read completed")

    # Upload the output of the worker to S3
    s3_client.upload_file(json_path, output_bucket, output_key)
    print("Result uploaded to s3")
