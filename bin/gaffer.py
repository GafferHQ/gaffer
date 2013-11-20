#!/usr/bin/env python2.6
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

import os
import sys
import ctypes
import signal
import warnings

# Work around cross module rtti errors on linux.
sys.setdlopenflags( sys.getdlopenflags() | ctypes.RTLD_GLOBAL )

# Get rid of the annoying signal handler which turns Ctrl-C into a KeyboardInterrupt exception
signal.signal( signal.SIGINT, signal.SIG_DFL )

# Reenable deprecation warnings - Python2.7 turns them off by default so otherwise we'd never get
# to catch all the naughty deprecated things we do.
warnings.simplefilter( "default", DeprecationWarning )

import IECore

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

args = sys.argv[1:]
if args and args[0] in ( "-help", "-h", "--help", "-H" ) :
	if len( args ) > 1 :
		app = loadApp( args[1] )
		formatter = IECore.WrappedTextFormatter( sys.stdout )
		formatter.paragraph( "Name : " + app.path )
		if app.description :
			formatter.paragraph( app.description + "\n" )
		if len( app.parameters().values() ):
			formatter.heading( "Parameters" )
			formatter.indent()
			for p in app.parameters().values() :
				IECore.formatParameterHelp( p, formatter )
			formatter.unindent()
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
	sys.exit( result )
