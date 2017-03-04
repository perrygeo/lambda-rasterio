from __future__ import division
from rasterio.io import MemoryFile
import boto3
import json
import rasterio


def read_data(baseurl, dtype='float32'):
    urls = {
        'nir': baseurl + '_B5.TIF.ovr',
        'red': baseurl + '_B4.TIF.ovr'}

    # Download bands and load as Numpy arrays
    bands = {}
    for name, url in urls.items():
        print("Downloading {}".format(name))
        with rasterio.open(url) as src:
            profile = src.profile.copy()
            bands[name] = src.read(1).astype(dtype)

    return bands, profile


def calc_ndvi(bands):
    return ((bands['nir'] - bands['red']) /
            (bands['nir'] + bands['red']))


def create_ndvi_array(path, row, sceneid):
    base = (
        'https://landsat-pds.s3.amazonaws.com/L8/'
        '{path}/{row}/{sceneid}/{sceneid}'.format(
            path=path, row=row, sceneid=sceneid))

    # Read Landsat Bands from s3 pds
    dtype = 'float32'
    bands, profile = read_data(base, dtype=dtype)
    profile['dtype'] = dtype

    # Calculation
    return calc_ndvi(bands), profile


def write_s3(ndvi, output, profile):
    # Write numpy array to s3
    s3 = boto3.client('s3')
    with MemoryFile() as memfile:
        with memfile.open(**profile) as dst:
            dst.write(ndvi, 1)
        s3.put_object(
            Body=memfile,
            Bucket='perrygeo-test',
            Key=output
        )


def parse_key(key):
    # L8/139/033/LC81390332016285LGN00/index.html
    _, path, row, sceneid, fname = key.split('/')
    return path, row, sceneid


def parse_s3_event(event):
    sns_message = json.loads(event['Records'][0]['Sns']['Message'])
    s3_event = sns_message['Records'][0]['s3']
    bucket = s3_event['bucket']['name']
    key = s3_event['object']['key']
    return bucket, key


def lambda_handler(event, context):
    # Get information from message
    bucket, key = parse_s3_event(event)
    path, row, sceneid = parse_key(key)

    # Calculate NDVI
    ndvi, profile = create_ndvi_array(path, row, sceneid)

    # Write it to S3 as GeoTiff
    output = 'ndvi/{}_ndvi.tif'.format(sceneid)
    write_s3(ndvi, output, profile)
