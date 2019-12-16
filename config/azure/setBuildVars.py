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
import github
import os
import re
import sys

# Azure pipeline variables can be populated at run-time by echoing special
# strings to a process output. The following allows vars to be set:
#
#    ##vso[task.setvariable variable=<name>;]<value>
#
# NOTE: The variable must first be defined in the Pipeline settings and have
# the 'Settable at queue time' checkbox checked.
#
# We make use of this mechanism to allow custom logic to define the build name
# as well as determine the correct commit hash depending on the nature of the
# trigger. These variables can be referenced in a pipeline yaml file downstream
# of the step that runs this script.

## Source Commit Hash

commit = os.environ.get( 'BUILD_SOURCEVERSION' )
# Azure merges the branch into its target in PR build, so
# BUILD_SOURCEVERSION isn't correct as it references the ephemeral merge.
if os.environ.get( 'BUILD_REASON', '' ) == 'PullRequest' :
	commit = os.environ.get( 'SYSTEM_PULLREQUEST_SOURCECOMMITID' )

## Source Branches

buildBranch = os.environ.get( "BUILD_SOURCEBRANCH", "" )
sourceBranch = os.environ.get( "SYSTEM_PULLREQUEST_SOURCEBRANCH", buildBranch )

## Source Tag

tag = buildBranch.replace( "refs/tags/", "" ) if "/tags/" in buildBranch else ""

## Release ID

releaseId = ""

if tag :

	# We attempt to find the release ID so that we only publish a tag build
	# if its for a release, not all tags will have one
	githubClient = github.Github( os.environ.get( 'GITHUB_ACCESS_TOKEN' ) )
	repo = githubClient.get_repo( os.environ.get( 'BUILD_REPOSITORY_NAME' ) )

	for r in repo.get_releases() :
		if r.tag_name == tag :
			releaseId = r.id
			break

## Build Name

formatVars = {
	"buildTypeSuffix" : "-debug" if os.environ.get( "BUILD_TYPE", "" ) == "DEBUG" else "",
	"platform" : "macos" if sys.platform == "darwin" else "linux",
	"timestamp" : datetime.datetime.now().strftime( "%Y_%m_%d_%H%M" ),
	"pullRequest" : os.environ.get( "SYSTEM_PULLREQUEST_PULLREQUESTNUMBER", "UNKNOWN" ),
	"shortCommit" : commit[:8],
	"tag" : tag,
	"branch" : re.sub( r"[^a-zA-Z0-9_]", "", sourceBranch.split( "/" )[-1] )
}

nameFormats = {
	"default" : "gaffer-{timestamp}-{shortCommit}-{platform}{buildTypeSuffix}",
	"PullRequest" : "gaffer-pr{pullRequest}-{branch}-{timestamp}-{shortCommit}-{platform}{buildTypeSuffix}",
	"Release" : "gaffer-{tag}-{platform}{buildTypeSuffix}"
}

trigger = os.environ.get( 'BUILD_REASON', 'Manual' )

# If we have a releaseID (and tag) then we always use release naming conventions
# to allow manual re-runs of release builds that fail for <reasons>.
if tag and releaseId :
	print( "Have Release ID %s for tag %s, using release naming." % ( releaseId, tag ) )
	trigger = "Release"

buildName = nameFormats.get( trigger, nameFormats['default'] ).format( **formatVars )

## Azure Pipeline Vars

print( "Setting $(Gaffer.Build.Name) to %s" % buildName )
print( "##vso[task.setvariable variable=Gaffer.Build.Name;]%s" % buildName )

# To make sure our publish always matches the one we use in the build name
print( "Setting $(Gaffer.Source.Commit) to %s" % commit )
print( "##vso[task.setvariable variable=Gaffer.Source.Commit;]%s" % commit )

print( "Setting $(Gaffer.GitHub.ReleaseID) to %s" % releaseId )
print( "##vso[task.setvariable variable=Gaffer.GitHub.ReleaseID;]%s" % releaseId )

