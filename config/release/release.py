#!/usr/bin/env python 

import os
import re
import sys
import json
import urllib
import argparse
import subprocess

parser = argparse.ArgumentParser()
parser.add_argument( "--tag", type=str, required=True )
args = parser.parse_args()

def __query( url ) :

	result = []

	while url is not None :

		l = urllib.urlopen( url )
		result.extend( json.load( l ) )
		
		h = dict( l.info() )
		if "link" in h :
			s = re.search( "^<(.*)>; rel=\"next\"", h["link"] )
			url = s.group( 1 ) if s is not None else None
		else :
			url = None
			
	return result

# check we have a token available for the upload

if "GITHUB_RELEASE_TOKEN" not in os.environ	:
	raise Exception( "GITHUB_RELEASE_TOKEN environment variable not set" )

# get tag and corresponding release

tags = __query( "https://johnhaddon:abracadabra1@api.github.com/repos/ImageEngine/gaffer/tags" )
tag = next( ( t for t in tags if t["name"] == args.tag ), None )

if tag is None :
	raise Exception( "Tag \"%s\" does not exist" % args.tag )

releases = __query( "https://johnhaddon:abracadabra1@api.github.com/repos/ImageEngine/gaffer/releases" )
release = next( ( r for r in releases if r["tag_name"] == args.tag ), None )

if release is None :
	raise Exception( "Release for tag \"%s\" does not exist" % args.tag )

# download source code from tag

sys.stderr.write( "Downloading source \"%s\"\n" % tag["tarball_url"] ) 

sourceDirName = "gaffer-%s-source" % args.tag
tarFileName = sourceDirName + ".tar.gz"
tarFileName, headers = urllib.urlretrieve( tag["tarball_url"] )

sys.stderr.write( "Decompressing source to \"%s\"\n" % sourceDirName ) 

os.makedirs( sourceDirName )
os.system( "tar xf %s -C %s --strip-components=1" % ( tarFileName, sourceDirName ) )
os.chdir( sourceDirName )

# download precompiled dependencies

platform = "osx" if sys.platform == "darwin" else "linux"
buildDir = "build/gaffer-%s-%s" % ( args.tag, platform )
installDir = "install/gaffer-%s-%s" % ( args.tag, platform )
os.makedirs( buildDir )

dependenciesReleases = __query( "https://api.github.com/repos/johnhaddon/gafferDependencies/releases" )
dependenciesRelease = next( r for r in dependenciesReleases if len( r["assets"] ) )
dependenciesAsset = next( a for a in dependenciesRelease["assets"] if platform in a["name"] )
 
sys.stderr.write( "Downloading dependencies \"%s\"\n" % dependenciesAsset["browser_download_url"] ) 

dependenciesTarFileName, headers = urllib.urlretrieve( dependenciesAsset["browser_download_url"] )

sys.stderr.write( "Decompressing dependencies to \"%s\"\n" % buildDir ) 

os.system( "tar xf %s -C %s --strip-components=1" % ( dependenciesTarFileName, buildDir ) )

# do the build

buildCommand = "scons package BUILD_DIR=%s INSTALL_DIR=%s ENV_VARS_TO_IMPORT=PATH RMAN_ROOT=$DELIGHT ARNOLD_ROOT=$ARNOLD_ROOT" % ( buildDir, installDir )
sys.stderr.write( buildCommand + "\n" )

subprocess.check_call( buildCommand, shell=True )

packageFileName = installDir + ".tar.gz"

uploadCommand = ( 'curl -H "Authorization: token %s" -H "Accept: application/vnd.github.manifold-preview" -H "Content-Type: application/zip" --data-binary @%s "%s=%s"' %
	( os.environ["GITHUB_RELEASE_TOKEN"], packageFileName, release["upload_url"], os.path.basename( packageFileName ) )
)

sys.stderr.write( "Uploading package \"%s\"\n" % packageFileName )

subprocess.check_call( uploadCommand, shell=True )
