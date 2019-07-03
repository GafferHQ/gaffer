#!/usr/bin/env python
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

import datetime
import os
import sys

def getCommitHash() :
	commit = os.environ.get( 'BUILD_SOURCEVERSION', '' )
	if os.environ.get( 'BUILD_REASON', 'Manual' ) == 'PullRequest' :
		commit = os.environ.get( 'SYSTEM_PULLREQUEST_SOURCECOMMITID', '' )
	return commit

formatVars = {
	"buildType" : os.environ.get( "BUILD_TYPE", "UNKNOWN" ).title(),
	"platform" : "MacOS" if sys.platform == "darwin" else "Linux",
	"timestamp" : datetime.datetime.now().strftime( "%Y%m%d%H%M" ),
	"pullRequest" : os.environ.get( "SYSTEM_PULLREQUEST_PULLREQUESTNUMBER", "UNKNOWN" ),
	"commit" : getCommitHash()
}

nameFormats = {
	"default" : "gaffer-{timestamp}-{commit}-{platform}-{type}",
	"PullRequest" : "gaffer-PR{pullRequest}-{commit}-{platform}-{type}"
}

trigger = os.environ.get( 'BUILD_REASON', 'Manual' )
buildName = nameFormats.get( trigger, nameFormats['default'] ).format( **formatVars )

print( "Setting $(buildName) to %s" % buildName )
print( "##vso[task.setvariable variable=buildName;]%s" % buildName )

# To make sure our publish always matches the one we use in the build name
print( "Setting $(buildSourceCommit) to %s" % formatVars['commit'] )
print( "##vso[task.setvariable variable=buildSourceCommit;]%s" % formatVars['commit'] )

