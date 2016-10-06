# Lambda-Rasterio

A rough template for deploying Rasterio applications (and apps with Python C extension modules) 
on AWS Lambda. A Dockerized, manylinux-enabled follow up to http://www.perrygeo.com/running-python-with-compiled-code-on-aws-lambda.html

## The problem

AWS Lambda runs on a Centos(ish) Linux environment with Python 2.7.
You can't install system libs or python modules - you must supply everything in one big .zip file.
Any modules with C extensions must be compatible with CentOS and have the shared libs available


## The solution

In my previous [blog post](http://www.perrygeo.com/running-python-with-compiled-code-on-aws-lambda.html
), I ssh'd into an EC2 instance and built libgdal etc from source.

In this followup, there are three new approaches that can help us

* **Docker** allows us to run CentOS locally in a container.
* **Manylinux Wheels** are now provided by Rasterio, Numpy and other C deps. These come with batteries included meaning libgdal is bundled. No need to install system depenencies from source.
* Rasterio can **read from s3** directly without the need for downloading locally.

We still need a Centos Linux container, though theoretcially any linux would work if you had a compatible python and used only manylinux wheels. This is solely for the purpose of constructing a virtualenv on the linux platform. Manylinux wheels get pulled from pypi and unpacked in site-packages. If pip had a `--pretend-to-be-linux-and-only-download-manylinux-wheels` option in the future, you could just build the venv on your local platform of choice.

Unlike my previous example, the manylinux wheels mean no mucking with `LD_LIBRARY_PATH` and spawning subprocesses - just `import rasterio` and do your thing.

## Example

This Lambda handler listens for an SNS message coming from an S3 object, opens it with Rasterio using an `s3://` URI, and prints some metadata:

```
from __future__ import print_function
import rasterio

def parse_sns(event):
    sns_message = json.loads(event['Records'][0]['Sns']['Message'])
    s3_event = sns_message['Records'][0]['s3']
    bucket = s3_event['bucket']['name']
    key = s3_event['object']['key']
    return bucket, key

def lambda_handler(event, context):
    bucket, key = parse_sns(event)

    with rasterio.open('s3://{}/{}'.format(bucket, key)) as src:
        print("This raster has {} bands".format(src.count))
```

You can use something like [s3touch](https://github.com/mapbox/s3touch) to trigger messages on any arbitrary S3 object

```
$ s3touch --topic arn:aws:sns:us-east-1:123456789:your-sns-topic s3://landsat-pds/L8/046/028/LC80460282016193LGN00/LC80460282016193LGN00_B4.TIF
```

## Rough outline

1. I suggest starting with the web console and a bare-bones Lambda function in order to get the plumbing working and make sure you know what message structure to expect from SNS or whatever event you're subcribing to.
2. Copy that example message locally and use it to write a handler (see `src/handler.py`). Use a `requirements.txt` file in a fresh venv to gather your dependencies.
3. Run the Docker script (see `make build` and `scripts/build.sh`) to create a linux venv with those requirements. You'll get a build directory with all the python modules at its root.
4. Gathers your application code and the requirements into a zip file. Run `make dist.zip`.
5. Upload that zip file to s3. Then in your web console, choose "Upload a file from Amazon S3" and give it the https link to your zip file.

## potential next steps

There's still parts about this that make me cringe. Testing locally is different than running on Lambda. Debugging is a pain. Uploading a 65+ MB zipfile for every change in your python file is glaringly inefficient. It might be possible to ditch the linux container if you manually downloaded all your wheel-based python modules unzipped them in the right place. Or have pip do it for you. Building the zip file on continuous integration and uploading directly to s3 would be neat. Lots to explore.

