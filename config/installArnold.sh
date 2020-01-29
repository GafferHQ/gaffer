#! /bin/bash

set -e

arnoldVersion=6.0.1.0

if [[ `uname` = "Linux" ]] ; then
	arnoldPlatform=linux
else
	arnoldPlatform=darwin
fi

# Check required vars are set, and if they are, aren't inadvertently unexpanded
# vars from anywhere (which we've seen with Azure, and not been able to find a
# syntax that just sets them empty if they're not set in the pipeline, despite
# what the docs say).

if [ -z "${ARNOLD_LOGIN}" ] || [ "${ARNOLD_LOGIN:0:1}" == "$" ] ; then
	echo "Error: ARNOLD_LOGIN not set, unable to install Arnold"
	exit 1
fi

if [ -z "${ARNOLD_PASSWORD}" ] || [ "${ARNOLD_PASSWORD:0:1}" == "$" ] ; then
	echo "Error: ARNOLD_PASSWORD not set, unable to install Arnold"
	exit 1
fi

mkdir -p arnoldRoot && cd arnoldRoot

url=downloads.solidangle.com/arnold/Arnold-${arnoldVersion}-${arnoldPlatform}.tgz

echo Downloading Arnold "https://${url}"

curl https://${ARNOLD_LOGIN}:${ARNOLD_PASSWORD}@${url} > Arnold-${arnoldVersion}-${arnoldPlatform}.tgz
tar -xzf Arnold-${arnoldVersion}-${arnoldPlatform}.tgz
