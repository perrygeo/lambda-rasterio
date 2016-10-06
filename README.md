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

In this followup, there are two new approaches that can help us

* **Docker** allows us to run CentOS locally in a container.
* **Manylinux Wheels** are now provided by Rasterio, Numpy and other C deps. These come with batteries included meaning libgdal is bundled. No need to install system depenencies from source.

We still need a Centos Linux container, though theoretcially any linux would work if you had a compatible python and used only manylinux wheels. This is solely for the purpose of constructing a virtualenv on the linux platform. Manylinux wheels get pulled from pypi and unpacked in site-packages. If pip had a `--pretend-to-be-linux-and-only-download-manylinux-wheels` option in the future, you could just build the venv on your local platform of choice.

Unlike my previous example, the manylinux wheels mean no mucking with `LD_LIBRARY_PATH` and spawning subprocesses - just `import rasterio` and do your thing.

## Rough outline

1. I suggest starting with the web console and a bare-bones Lambda in order to get the plumbing working and make sure you know what message structure to expect from SNS or whatever event you're subcribing to.
2. Copy that example message locally and use it to write a handler (see `src/handler.py`). Use a `requirements.txt` file in a fresh venv to gather your dependencies.
3. Run the Docker script (see `make build` and `scripts/build.sh`) to create a linux venv with those requirements. You'll get a build directory with all the python modules at its root.
4. Build a zip file which gathers your application code and the requirements into a zip file. Run `make dist.zip`.
5. Upload that zip file to s3. Then in your web console, choose "Upload a file from Amazon S3" and give it the https link to your zip file.

## potential next steps

There's still parts about this that make me cringe. Testing locally is different than running on Lambda. Debugging is a pain. Uploading a 65+ MB zipfile for every change in your python file is glaringly inefficient. It might be possible to ditch the linux container if you manually downloaded all your wheel-based python modules unzipped them in the right place. Lots to explore.

