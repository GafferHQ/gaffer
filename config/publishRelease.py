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

# A script to publish a build to a GitHub Release

parser = argparse.ArgumentParser()

parser.add_argument(
	"--repo",
	required = True,
	help = "The GitHub organisation/repo to post the build link to."
)

parser.add_argument(
	"--releaseId",
	type = int,
	required = True,
	help = "The release ID to publish the asset to."
)

parser.add_argument(
	"--archive",
	dest = "archive",
	required = True,
	help = "The path to the build archive to publish."
)

parser.add_argument(
	"--github-access-token",
	dest = "githubAccessToken",
	default = os.environ.get( 'GITHUB_ACCESS_TOKEN', None ),
	help = "A suitable access token to authenticate the GitHub API."
)

args = parser.parse_args()

if not args.githubAccessToken :
	parser.exit( 1, "No --github-access-token/GITHUB_ACCESS_TOKEN set" )

if not os.path.exists( args.archive ) :
	parser.exit( 1, "The specified archive '%s' does not exist." % args.archive )

githubClient = github.Github( args.githubAccessToken )
repo = githubClient.get_repo( args.repo )

release = repo.get_release( args.releaseId )
if not release :
	parser.exit( 1, "Unable to find GitHub Release %s" % args.releaseId )

print( "Uploading '%s' to release %s" % ( args.archive, args.releaseId ) )
asset = release.upload_asset( args.archive, content_type="application/gzip" )

print( "Success, %s available at %s" % ( args.archive, asset.browser_download_url ) )

