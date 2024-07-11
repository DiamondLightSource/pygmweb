#!/bin/bash

#Script to be called by .gitlab-ci.yml to perform container build
#Patrick Wang patrick.wang@diamond.ac.uk

echo "Building container"

GROUP=`echo $CI_PROJECT_PATH | cut -f 2 -d "/"`

#Build the container
test -z "${CI_COMMIT_TAG}" && CMD="/kaniko/executor --context $CI_PROJECT_DIR --dockerfile $CI_PROJECT_DIR/Dockerfile --destination $CI_REGISTRY/$GROUP/$CI_PROJECT_NAME:$CI_COMMIT_REF_NAME"
test -n "${CI_COMMIT_TAG}" && CMD="/kaniko/executor --context $CI_PROJECT_DIR --dockerfile $CI_PROJECT_DIR/Dockerfile --destination $CI_REGISTRY/$GROUP/$CI_PROJECT_NAME:$CI_COMMIT_TAG --destination $CI_REGISTRY/$GROUP/$CI_PROJECT_NAME:latest"
 
echo "Command to execute is..."
echo $CMD
$CMD
