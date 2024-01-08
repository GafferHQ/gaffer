##########################################################################
#
#  Copyright (c) 2011, John Haddon. All rights reserved.
#  Copyright (c) 2011-2012, Image Engine Design Inc. All rights reserved.
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

# Note: This file is generally considered private. Those wishing to launch
# gaffer should use the gaffer wrapper script (also in this directory)
# as it ensures the correct process environment is set up prior to launch.

import os
import pathlib
import re
import shutil
import sys
import signal
import tempfile
import warnings

# Get rid of the annoying signal handler which turns Ctrl-C into a KeyboardInterrupt exception
signal.signal( signal.SIGINT, signal.SIG_DFL )

# Reenable deprecation warnings - Python2.7 turns them off by default so otherwise we'd never get
# to catch all the naughty deprecated things we do.
warnings.simplefilter( "default", DeprecationWarning )

import IECore

# Increase the soft limit for file handles as high as we can - we need everything we can get for
# opening models, textures etc.
if os.name != "nt" :
	import resource
	softFileLimit, hardFileLimit = resource.getrlimit( resource.RLIMIT_NOFILE )
	if softFileLimit < hardFileLimit :
		resource.setrlimit( resource.RLIMIT_NOFILE, ( hardFileLimit, hardFileLimit ) )
		IECore.msg( IECore.Msg.Level.Debug, "Gaffer", "Increased file handle limit to {}".format( hardFileLimit ) )

# Rename the process to "gaffer".

from Gaffer._Gaffer import _nameProcess
_nameProcess()

# Add non-version-specific startup location to `GAFFER_STARTUP_PATHS`. Historically Gaffer saved
# preferences there, but those are now saved in a major-version-specific location (see below).
# We continue to use the non-versioned location for two reasons :
#
# - So the user has somewhere to save custom startup scripts they want to use across all versions.
# - So old preferences continue to be loaded even in new versions.
#
## \todo When all currently supported Gaffer versions are using a versioned location, remove
# the Gaffer-generated files from the non-versioned location.

startupDir = pathlib.Path( os.getenv( "HOME" ) ) / "gaffer" / "startup"
if str( startupDir ) not in os.environ["GAFFER_STARTUP_PATHS"].split( os.pathsep ) :
	os.environ["GAFFER_STARTUP_PATHS"] = os.pathsep.join( [ str( startupDir ), os.environ["GAFFER_STARTUP_PATHS"] ] )

# Add version-specific startup location to `GAFFER_STARTUP_PATHS`. If one doesn't exist, we
# create it by migrating from the previous startup directory.

def acquireVersionedStartupDir( parentDir ) :

	from Gaffer.About import About
	versionedStartupDir = parentDir / "startup-{}.{}".format( About.milestoneVersion(), About.majorVersion() )

	if versionedStartupDir.exists() :
		return versionedStartupDir

	# No versioned startup directory, so we must migrate from the previous version.

	if not parentDir.exists() :
		# Nothing to migrate from. We still return the theoretical location of
		# the versioned directory so we can include it in the searchpath for
		# educational purposes.
		return versionedStartupDir

	# Find source directory to migrate from.

	maxVersion = None
	for candidate in parentDir.iterdir() :
		m = re.fullmatch( r"startup-([0-9]+)\.([0-9]+)", candidate.name )
		if m :
			version = [ int( x ) for x in m.groups() ]
			maxVersion = max( version, maxVersion ) if maxVersion is not None else version

	sourceDir = parentDir / "startup" if maxVersion is None else parentDir / "startup-{}.{}".format( *maxVersion )
	if not sourceDir.exists() :
		return versionedStartupDir

	# Copy from source directory to `versionedStartupDir`. We first copy
	# everything to a temporary directory and then rename that atomically to
	# avoid conflicts between concurrently running processes.

	tempDir = pathlib.Path( tempfile.mkdtemp( dir = parentDir, prefix = "__migrating-" + versionedStartupDir.name ) )
	for sourceFile in sourceDir.glob( "**/*.py" ) :
		with open( sourceFile ) as file :
			if file.readline() != "# This file was automatically generated by Gaffer.\n" :
				# We only want to copy files created automatically by Gaffer for
				# the serialisation of preferences, layouts etc. Anything else
				# is assumed to be user-managed, in which case we should leave it alone.
				continue
		destFile = tempDir / sourceFile.relative_to( sourceDir )
		destFile.parent.mkdir( parents = True, exist_ok = True )
		shutil.copyfile( sourceFile, destFile )

	try :
		tempDir.rename( versionedStartupDir )
		IECore.msg( IECore.Msg.Level.Info, "Gaffer", "Migrated preferences from \"{}\"".format( sourceDir ) )
	except FileExistsError :
		# Another process beat us to it.
		shutil.rmtree( tempDir )

	return versionedStartupDir

versionedStartupDir = acquireVersionedStartupDir( startupDir.parent )
if str( versionedStartupDir ) not in os.environ["GAFFER_STARTUP_PATHS"].split( os.pathsep ) :
	os.environ["GAFFER_STARTUP_PATHS"] = os.pathsep.join( [ str( versionedStartupDir ), os.environ["GAFFER_STARTUP_PATHS"] ] )

# Load and run application.

helpText = """Usage :

    gaffer -help                    Print this message
    gaffer -help appName            Print help specific to named application
    gaffer appName [flags]          Run named application with specified flags
    gaffer fileName.gfr [flags]     Run gui application with specified script and flags
    gaffer [flags]                  Run gui application with specified flags
"""

appLoader = IECore.ClassLoader.defaultLoader( "GAFFER_APP_PATHS" )
applicationText = "Installed applications :\n\n" + "\n".join( "    " + x for x in appLoader.classNames() ) + "\n"

def loadApp( appName ) :

	if appName in appLoader.classNames() :
		return appLoader.load( appName )()
	else :
		sys.stderr.write( "ERROR : Application \"%s\" not installed on GAFFER_APP_PATHS\n" % appName )
		sys.stderr.write( "\n" + applicationText )
		sys.exit( 1 )

def checkCleanExit() :

	# Get the Gaffer and GafferUI modules, but only if the app actually
	# imported them. We don't want to force their importation because it's
	# just a waste of time if they weren't used.
	Gaffer = sys.modules.get( "Gaffer" )
	GafferUI = sys.modules.get( "GafferUI" )

	if Gaffer is None and GafferUI is None :
		return

	# Clean up any garbage left behind by Cortex's wrapper mechanism - because
	# the Gaffer.Application itself is derived from IECore.Parameterised, which
	# as far as I can tell is wrapped unnecessarily, we must call this to allow
	# the application to be deleted at all. Note that we're deliberately not also
	# calling gc.collect() - our intention here isn't to clean up on shutdown, but
	# to highlight problems caused by things not cleaning up after themselves during
	# execution. We aim to eliminate all circular references from our code, to avoid
	# garbage collection overhead and to avoid problems caused by referencing Qt widgets
	# which were long since destroyed in C++.
	## \todo Reevaluate the need for this call after Cortex 9 development.
	IECore.RefCounted.collectGarbage()
	# Importing here rather than at the top of the file prevents false
	# positives being reported in gc.get_objects() below. I have no idea why,
	# but if not imported here, get_objects() will report objects which have
	# nothing referring to them and which should be dead, even with an
	# explicit call to gc.collect() beforehand.
	import gc

	# Check for things that shouldn't exist at shutdown, and
	# warn of anything we find.
	scriptNodes = []
	widgets = []
	for o in gc.get_objects() :
		if Gaffer is not None and isinstance( o, Gaffer.ScriptNode ) :
			scriptNodes.append( o )
		elif GafferUI is not None and isinstance( o, GafferUI.Widget ) :
			widgets.append( o )

	if scriptNodes :
		IECore.msg(
			IECore.Msg.Level.Debug,
			"Gaffer shutdown", "%d remaining ScriptNode%s detected. Debugging with objgraph is recommended." % (
				len( scriptNodes ),
				"s" if len( scriptNodes ) > 1 else "",
			)
		)

	if widgets :

		count = {}
		for widget in widgets :
			widgetType = widget.__class__.__name__
			count[widgetType] = count.get( widgetType, 0 ) + 1

		summaries = [ "%s (%d)" % ( k, count[k] ) for k in sorted( count.keys() ) ]

		IECore.msg(
			IECore.Msg.Level.Debug,
			"Gaffer shutdown", "%d remaining Widget%s detected : \n\n%s\n\nDebugging with objgraph is recommended." % (
				len( widgets ),
				"s" if len( widgets ) > 1 else "",
				"\t" + "\n\t".join( summaries )
			)
		)

args = sys.argv[1:]
if args and args[0] in ( "-help", "-h", "--help", "-H" ) :
	if len( args ) > 1 :
		app = loadApp( args[1] )
		app["help"].setTypedValue( True )
		app.run()
		sys.exit( 0 )
	else :
		sys.stdout.write( helpText )
		sys.stdout.write( "\n" + applicationText )
		sys.exit( 0 )
else :
	appName = "gui"
	appArgs = args
	if len( args ) :
		if not args[0].startswith( "-" ) and not args[0].endswith( ".gfr" ) :
			appName = args[0]
			appArgs = args[1:]

	app = loadApp( appName )
	IECore.ParameterParser().parse( appArgs, app.parameters() )

	result = app.run()

	del app
	checkCleanExit()

	sys.exit( result )
