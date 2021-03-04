import os
import sys
import json
import subprocess

# This builds a compile_commands.json file in the format
# required by run-clang-tidy.py. It is expected to be run
# from the root of the gaffer repository, after doing a
# successful scons build.
#
# Example usage :
#
# > python contrib/scripts/buildCompileCommands.py
# > run-clang-tidy.py -header-filter='.*' -checks='-*,modernize-use-override' -fix

# Make SCons tell us everything it would do to build Gaffer

subprocess.check_call( [ "scons", "--clean" ] )
sconsOutput = subprocess.check_output( [ "scons", "build", "--dry-run", "--no-cache" ], universal_newlines = True )

# Write that into a "compile_commands.json" file

data = []

for line in sconsOutput.split( "\n" ) :

	line = line.strip()
	if not line.endswith( ".cpp" ) :
		continue

	file = line.split()[-1]
	data.append(
		{
			"directory" : os.getcwd(),
			"command" : line,
			"file" : file,
		}
	)

with open( "compile_commands.json", "w" ) as f :

	json.dump( data, f )
