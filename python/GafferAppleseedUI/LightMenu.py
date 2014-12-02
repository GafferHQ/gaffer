##########################################################################
#
#  Copyright (c) 2014, Esteban Tovagliari. All rights reserved.
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

import appleseed

import IECore

import GafferUI
import GafferAppleseed

def appendLights( menuDefinition, prefix="/Appleseed" ) :

	for model in appleseed.EnvironmentEDF.get_input_metadata() :
		__addToMenu( menuDefinition, prefix + "/Environment/", model )

	for model in appleseed.Light.get_input_metadata() :
		__addToMenu( menuDefinition, prefix + "/Light/", model )

def __lightCreator( name ) :

	light = GafferAppleseed.AppleseedLight( name )
	light.loadShader( name )
	return light

def __addToMenu( menuDefinition, prefix, model ) :

	displayName = __displayName( model )
	menuPath = prefix + displayName
	menuDefinition.append(
		menuPath,
		{
			"command" : GafferUI.NodeMenu.nodeCreatorWrapper( IECore.curry( __lightCreator, model ) ),
			"searchText" : "as" + displayName.replace( " ", "" ),
		}
	)

def __displayName( model ) :

	displayName = " ".join( [ IECore.CamelCase.toSpaced( x ) for x in model.split( "_" ) ] )
	displayName = displayName.replace(" Light", "" )
	displayName = displayName.replace(" Environment Edf", "" )
	return displayName

