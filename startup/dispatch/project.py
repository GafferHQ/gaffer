##########################################################################
#
#  Copyright (c) 2018, Image Engine Design Inc. All rights reserved.
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

## \todo : This entire file was copied directly from startup/gui/project.py
# and should likely be kept in-sync. Is it desirable to maintain this separately
# from the gui app or should we unify project variables and initial dispatcher
# settings across the apps?

import IECore

import Gaffer

import GafferDispatch

##########################################################################
# Project variables
##########################################################################

def __scriptAdded( container, script ) :

	variables = script["variables"]
	if "projectName" not in variables :
		projectName = variables.addMember( "project:name", IECore.StringData( "default" ), "projectName" )
	if "projectRootDirectory" not in variables :
		projectRoot = variables.addMember( "project:rootDirectory", IECore.StringData( "$HOME/gaffer/projects/${project:name}" ), "projectRootDirectory" )

	Gaffer.MetadataAlgo.setReadOnly( variables["projectName"]["name"], True )
	Gaffer.MetadataAlgo.setReadOnly( variables["projectRootDirectory"]["name"], True )

application.root()["scripts"].childAddedSignal().connect( __scriptAdded, scoped = False )

##########################################################################
# Dispatchers
##########################################################################

dispatchers = [ GafferDispatch.LocalDispatcher ]
with IECore.IgnoredExceptions( ImportError ) :
	import GafferTractor
	dispatchers.append( GafferTractor.TractorDispatcher )

for dispatcher in dispatchers :

	Gaffer.Metadata.registerValue( dispatcher, "jobName", "userDefault", "${script:name}" )
	directoryName = dispatcher.staticTypeName().rpartition( ":" )[2].replace( "Dispatcher", "" ).lower()
	Gaffer.Metadata.registerValue( dispatcher, "jobsDirectory", "userDefault", "${project:rootDirectory}/dispatcher/" + directoryName )

GafferDispatch.Dispatcher.setDefaultDispatcherType( "Local" )
