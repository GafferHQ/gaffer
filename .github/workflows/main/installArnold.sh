#! /bin/bash
##########################################################################
#
#  Copyright (c) 2019, Cinesite VFX Ltd. All rights reserved.
#
#  Redistribution and use in source and binary forms, with or without
#  modification, are permitted provided that the following conditions are
#  met:
#
#      * Redistributions of source code must retain the above
#        copyright notice, this list of conditions and the following
#        disclaimer.
#
#      * Redistributions in binary form must reproduce the above
#        copyright notice, this list of conditions and the following
#        disclaimer in the documentation and/or other materials provided with
#        the distribution.
#
#      * Neither the name of Cinesite VFX Ltd. nor the names of
#        any other contributors to this software may be used to endorse or
#        promote products derived from this software without specific prior
#        written permission.
#
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS
#  IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
#  THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
#  PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR
#  CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
#  EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
#  PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
#  PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
#  LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
#  NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
#  SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
##########################################################################

set -e

arnoldVersion=6.2.0.1

if [[ `uname` = "Linux" ]] ; then
	arnoldPlatform=linux
else
	arnoldPlatform=darwin
fi

url=forgithubci.solidangle.com/arnold/Arnold-${arnoldVersion}-${arnoldPlatform}.tgz

# Configure the login information, if this has been supplied.
login=""
if [ ! -z "${ARNOLD_LOGIN}" ] && [ ! -z "${ARNOLD_PASSWORD}" ] ; then
	login="${ARNOLD_LOGIN}:${ARNOLD_PASSWORD}@"
fi

mkdir -p arnoldRoot && cd arnoldRoot

echo Downloading Arnold "https://${url}"
curl -L https://${login}${url} -o Arnold-${arnoldVersion}-${arnoldPlatform}.tgz

tar -xzf Arnold-${arnoldVersion}-${arnoldPlatform}.tgz
