# BuildTarget: images/exampleMacbethChart.png

import os
import tempfile
import sys
if os.name == 'posix' and sys.version_info[0] < 3:
	import subprocess32 as subprocess
else:
	import subprocess
import imath
import IECore

import Gaffer
import GafferUI

# Create a random directory in `/tmp` for the dispatcher's `jobsDirectory`, so we don't clutter the user's `~gaffer` directory
__temporaryDirectory = tempfile.mkdtemp( prefix = "gafferDocs" )

def __dispatchScript( script, tasks, settings ) :
	command = "gaffer dispatch -script {} -tasks {} -dispatcher Local -settings {} -dispatcher.jobsDirectory '\"{}/dispatcher/local\"'".format(
		script,
		" ".join( tasks ),
		" ".join( settings ),
		__temporaryDirectory
		)
	subprocess.check_call( command, shell=True )

# Example: Macbeth Chart
__dispatchScript(
	script = os.path.abspath( "../../../examples/rendering/macbethChart.gfr" ),
	tasks = [ "AppleseedRender" ],
	settings = [
		"-StandardOptions.options.renderResolution.enabled True",
		"-StandardOptions.options.renderResolution.value.x '270'",
		"-StandardOptions.options.renderResolution.value.y '240'",
		"-AppleseedOptions.options.maxAASamples.enabled True",
		"-AppleseedOptions.options.maxAASamples.value '0'",
		"-AppleseedOptions.options.aaBatchSampleSize.enabled True",
		"-AppleseedOptions.options.aaBatchSampleSize.value '64'",
		"-Outputs.outputs.output2.fileName '\"{}\"'".format( os.path.abspath( "images/exampleMacbethChart.png" ) ),
		"-Outputs.outputs.output2.type '\"png\"'",
		"-Outputs.outputs.output1.active False"
		]
	)
