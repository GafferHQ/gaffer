#! /bin/bash

set -e

arnoldVersion=5.3.1.0

if [[ `uname` = "Linux" ]] ; then
	arnoldPlatform=linux
else
	arnoldPlatform=darwin
fi

mkdir -p arnoldRoot && cd arnoldRoot

curl https://${ARNOLD_LOGIN}:${ARNOLD_PASSWORD}@downloads.solidangle.com/arnold/Arnold-${arnoldVersion}-${arnoldPlatform}.tgz > Arnold-${arnoldVersion}-${arnoldPlatform}.tgz
tar -xzf Arnold-${arnoldVersion}-${arnoldPlatform}.tgz
