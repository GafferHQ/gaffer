#! /bin/bash
##########################################################################
#
#  Copyright (c) 2018, Image Engine Design Inc. All rights reserved.
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
#      * Neither the name of John Haddon nor the names of
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

# Figure out where we'll be making the build

gafferMilestoneVersion=`grep "gafferMilestoneVersion = " SConstruct | cut -d" " -f 3`
gafferMajorVersion=`grep "gafferMajorVersion = " SConstruct | cut -d" " -f 3`
gafferMinorVersion=`grep "gafferMinorVersion = " SConstruct | cut -d" " -f 3`
gafferPatchVersion=`grep "gafferPatchVersion = " SConstruct | cut -d" " -f 3`

if [[ `uname` = "Linux" ]] ; then
	platform=linux
else
	platform=osx
fi

# The first argument can be used to specify a directory to install to
buildDir=${1:-"build/gaffer-$gafferMilestoneVersion.$gafferMajorVersion.$gafferMinorVersion.$gafferPatchVersion-$platform"}

# Get the prebuilt dependencies package and unpack it into the build directory

dependenciesVersion="0.54.0.0"
dependenciesVersionSuffix="-rc2"
dependenciesFileName="gafferDependencies-$dependenciesVersion-$platform.tar.gz"
downloadURL="https://github.com/GafferHQ/dependencies/releases/download/$dependenciesVersion$dependenciesVersionSuffix/$dependenciesFileName"

echo "Downloading dependencies \"$downloadURL\""
curl -L $downloadURL > $dependenciesFileName

mkdir -p $buildDir
tar xf $dependenciesFileName -C $buildDir --strip-components=1
