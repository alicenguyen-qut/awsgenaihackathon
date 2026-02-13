#!/bin/bash
set -e

echo "Creating Lambda deployment package..."

cd src
mkdir -p package

pip install -r ../requirements.txt -t package/
cp lambda_function.py package/

cd package
zip -r ../lambda_deployment.zip .
cd ..

echo "Deployment package created: lambda_deployment.zip"
