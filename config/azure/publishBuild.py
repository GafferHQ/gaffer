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
from azure.storage.blob import BlockBlobService

import argparse
import datetime
import os
import subprocess
import sys

# A script to publish an archive to an Azure blob store and create a commit
# status linking to the download on the source commit.

parser = argparse.ArgumentParser()

parser.add_argument(
	"--repo",
	required = True,
	help = "The GitHub organisation/repo to post the build link to."
)

parser.add_argument(
	"--commit",
	required = True,
	help = "The hash for the commit to publish the build link to."
)

parser.add_argument(
	"--context",
	help = "The context to associate the build link to. There can only be "
	       "one status for each context on a commit. eg: 'CI Linux Release'"
)

parser.add_argument(
	"--description",
	default = "Download available",
	help = "The description to appear in the commit status message."
)

parser.add_argument(
	"--archive",
	dest = "archive",
	required = True,
	help = "The path to the build archive to publish."
)

parser.add_argument(
	"--azure-account",
	dest = "azureAccount",
	default = "gafferhq",
	help = "The Storage Account name to upload the archive to."
)

parser.add_argument(
	"--azure-container",
	dest = "azureContainer",
	default = "builds",
	help = "The storage container to upload the archive to."
)

parser.add_argument(
	"--github-access-token",
	dest = "githubAccessToken",
	default = os.environ.get( 'GITHUB_ACCESS_TOKEN', None ),
	help = "A suitable access token to authenticate the GitHub API."
)

parser.add_argument(
	"--azure-access-token",
	dest = "azureAccessToken",
	default = os.environ.get( 'AZURE_ACCESS_TOKEN', None ),
	help = "A suitable access token to authenticate the Azure Blob Store API."
)

args = parser.parse_args()

if not args.azureAccessToken :
	parser.exit( 1, "No --azure-access-token/AZURE_ACCESS_TOKEN set")

if not args.githubAccessToken :
	parser.exit( 1, "No --github-access-token/GITHUB_ACCESS_TOKEN set")


formatVars = {
	"buildTypeSuffix" : " Debug" if os.environ.get( "BUILD_TYPE", "" ) == "DEBUG" else "",
	"platform" : "MacOS" if sys.platform == "darwin" else "Linux",
}

if not args.context :
	args.context = "CI Build ({platform}{buildTypeSuffix})".format( **formatVars )

if not os.path.exists( args.archive ) :
	parser.exit( 1, "The specified archive '%s' does not exist." % args.archive )

# Post our archive to blob storage

blobStore = BlockBlobService(
	account_name=args.azureAccount,
	account_key=args.azureAccessToken
)

print( "Uploading {archive} to {account}/{container}".format(
	archive = args.archive,
	account = args.azureAccount,
	container = args.azureContainer
) )

def uploadProcess( current, total ) :
	print( "Upload process: %s of %s bytes" % ( current, total ) )

archiveFilename = os.path.basename( args.archive )

blobStore.create_blob_from_path(
	args.azureContainer,
	archiveFilename,
	args.archive,
	progress_callback=uploadProcess
)
downloadURL = blobStore.make_blob_url( args.azureContainer, archiveFilename )

print( "Available at %s" % downloadURL )

# Publish a commit status to our source commit

print( "Publishing build link to status on {commit} in {repo}: {context} {description}".format(
	commit = args.commit,
	repo = args.repo,
	context = args.context,
	description = args.description
) )

githubClient = github.Github( args.githubAccessToken )
repo = githubClient.get_repo( args.repo )
commit = repo.get_commit( args.commit )

commit.create_status( "success", downloadURL, args.description, args.context )

