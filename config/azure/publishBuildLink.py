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

import github

import argparse
import datetime
import os
import subprocess
import sys

parser = argparse.ArgumentParser()

parser.add_argument(
	"--repo",
	default = os.environ.get( 'BUILD_REPOSITORY_NAME', None ),
	help = "The GitHub organistaion/repo to post the artifact to."
)

parser.add_argument(
	"--commit",
	required = True,
	help = "The hash for the commit to publish a link to the build to."
)

parser.add_argument(
	"--url",
	required = True,
	help = "The download url to publish."
)

parser.add_argument(
	"--context",
	help = "The context to associate the artifact with."
)

parser.add_argument(
	"--description",
	default = "Download available",
	help = "The description to appear in the commit status message."
)

parser.add_argument(
	"--github-access-token",
	dest = "githubAccessToken",
	default = os.environ.get( 'GITHUB_ACCESS_TOKEN', None ),
	help = "A suitable access token to authenticate the GitHub API."
)

args = parser.parse_args()

if not args.githubAccessToken :
	parser.exit( 1, "No --github-access-token/GITHUB_ACCESS_TOKEN set")

formatVars = {
	"type" : os.environ.get( "BUILD_TYPE", "UNKNOWN" ).title(),
	"platform" : "MacOS" if sys.platform == "darwin" else "Linux",
}

if not args.context :
	args.context = "CI Build ({platform} {type})".format( **formatVars )

print( "Publishing build link to status on {commit} in {repo}:\n   {context}: {description} - {url}".format(
	commit = args.commit,
	repo = args.repo,
	context = args.context,
	description = args.description,
	url = args.url
) )

githubClient = github.Github( args.githubAccessToken )
repo = githubClient.get_repo( args.repo )
commit = repo.get_commit( args.commit )

commit.create_status( "success", args.url, args.description, args.context )

