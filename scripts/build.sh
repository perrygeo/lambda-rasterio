#!/bin/bash
/opt/python/cp27-cp27mu/bin/pip install -r /app/requirements.txt

mkdir -p /app/build
cp -r /opt/python/cp27-cp27mu/lib/python2.7/site-packages/* /app/build
