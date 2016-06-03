##########################################################################
#
#  Copyright (c) 2013-2014, Image Engine Design Inc. All rights reserved.
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

import IECore

import Gaffer
import GafferUI
import GafferDispatch

##########################################################################
# Project variables
##########################################################################

def __scriptAdded( container, script ) :


	variables = script["variables"]
	if "projectName" not in variables :
		variables.addChild(Gaffer.CompoundDataPlug.MemberPlug("projectName", flags=(Gaffer.Plug.Flags.Default ) & ~Gaffer.Plug.Flags.Serialisable))
		variables["projectName"].addChild(Gaffer.StringPlug("name", defaultValue='project:name', flags=Gaffer.Plug.Flags.Default))
		variables["projectName"].addChild(Gaffer.StringPlug("value", defaultValue='default',
																	  flags=Gaffer.Plug.Flags.Default ))
		variables["projectName"].setFlags(Gaffer.Plug.Flags.ReadOnly, True)
	if "projectRootDirectory" not in variables :
		variables.addChild(Gaffer.CompoundDataPlug.MemberPlug("projectRootDirectory", flags=(Gaffer.Plug.Flags.Default) & ~Gaffer.Plug.Flags.Serialisable))
		variables["projectRootDirectory"].addChild(Gaffer.StringPlug("name", defaultValue='project:rootDirectory', flags=Gaffer.Plug.Flags.Default))
		variables["projectRootDirectory"].addChild(Gaffer.StringPlug("value", defaultValue='$HOME/gaffer/projects/${project:name}',
																	  flags=Gaffer.Plug.Flags.Default ))
		variables["projectRootDirectory"].setFlags(Gaffer.Plug.Flags.ReadOnly, True)

	__scriptAddedConnection = application.root()["scripts"].childAddedSignal().connect( __scriptAdded )

##########################################################################
# Bookmarks
##########################################################################

def __projectBookmark( forWidget, location ) :

	script = None
	if forWidget is not None :
		if isinstance( forWidget, GafferUI.ScriptWindow ) :
			scriptWindow = forWidget
		else :
			scriptWindow = forWidget.ancestor( GafferUI.ScriptWindow )
		if scriptWindow is not None :
			script = scriptWindow.scriptNode()

	if script is not None :
		p = script.context().substitute( location )
		if not os.path.exists( p ) :
			try :
				os.makedirs( p )
			except OSError :
				pass
		return p
	else :
		return os.getcwd()

GafferUI.Bookmarks.acquire( application ).add( "Project", IECore.curry( __projectBookmark, location="${project:rootDirectory}" ) )
GafferUI.Bookmarks.acquire( application, category="script" ).setDefault( IECore.curry( __projectBookmark, location="${project:rootDirectory}/scripts" ) )
GafferUI.Bookmarks.acquire( application, category="reference" ).setDefault( IECore.curry( __projectBookmark, location="${project:rootDirectory}/references" ) )

##########################################################################
# Dispatchers
##########################################################################

dispatchers = [ GafferDispatch.LocalDispatcher ]
with IECore.IgnoredExceptions( ImportError ) :
	import GafferTractor
	dispatchers.append( GafferTractor.TractorDispatcher )

for dispatcher in dispatchers :

	Gaffer.Metadata.registerPlugValue( dispatcher, "jobName", "userDefault", "${script:name}" )
	directoryName = dispatcher.staticTypeName().rpartition( ":" )[2].replace( "Dispatcher", "" ).lower()
	Gaffer.Metadata.registerPlugValue( dispatcher, "jobsDirectory", "userDefault", "${project:rootDirectory}/dispatcher/" + directoryName )

Gaffer.Metadata.registerPlugValue( GafferDispatch.LocalDispatcher, "executeInBackground", "userDefault", True )
GafferDispatch.Dispatcher.setDefaultDispatcherType( "Local" )
