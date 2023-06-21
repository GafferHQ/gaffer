#! /usr/bin/env python

import argparse
import inspect
import subprocess
import os

parser = argparse.ArgumentParser(
	description = inspect.cleandoc(
	"""
	Run a selection of Gaffer tests for a specified set of commits,
	outputting a separate json file for the tests for each commit.
	""" )
)

parser.add_argument(
	'--commits', action='store', nargs='+',
	help='Hashes of commits to build'
)

parser.add_argument(
	'--tests', action='store', nargs='+',
	help='Names of tests to run'
)

parser.add_argument(
	'--outputFolder', action='store', required = True,
	help='Folder to put output json files to'
)

args = parser.parse_args()

outputFolder = vars( args )["outputFolder"]
try:
	os.makedirs( outputFolder )
except:
	pass

currentBranch = subprocess.check_output( [ "git", "stat", "-s", "-b" ] ).splitlines()[0].split()[1]
print( currentBranch )
for c in vars( args )["commits"]:
	subprocess.check_call( [ "git", "checkout", c ] )
	subprocess.check_call( [ "scons", "-j 16", "build" ] )
	subprocess.check_call( [ "gaffer", "test" ] + vars( args )["tests"] + [ "-outputFile", "%s/%s.json" % ( outputFolder, c ) ] )

subprocess.check_call( [ "git", "checkout", currentBranch ] )
