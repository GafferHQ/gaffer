# BuildTarget: images/exampleMacbethChart.png

import os
import tempfile
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
	tasks = [ "CyclesRender" ],
	settings = [
		"-StandardOptions.options.renderResolution.enabled True",
		"-StandardOptions.options.renderResolution.value.x '270'",
		"-StandardOptions.options.renderResolution.value.y '240'",
		"-background_light.parameters.exposure '1'",
		"-Outputs.outputs.output2.fileName '\"{}\"'".format( os.path.abspath( "images/exampleMacbethChart.png" ) ),
		"-Outputs.outputs.output2.type '\"png\"'",
		"-Outputs.outputs.output1.active False"
		]
	)
