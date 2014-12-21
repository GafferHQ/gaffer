##########################################################################
#
#  Copyright (c) 2013, John Haddon. All rights reserved.
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

import Gaffer
import GafferUI

import GafferOSL

##########################################################################
# Metadata. We register dynamic Gaffer.Metadata entries which are
# implemented as queries to the OSL metadata held within the shader.
##########################################################################

def __nodeDescription( node ) :

	__defaultDescription = """Loads OSL shaders for use in supported renderers. Use the ShaderAssignment node to assign shaders to objects in the scene."""

	description = node.shaderMetadata( "help" )
	return description or __defaultDescription

def __plugDescription( plug ) :

	return plug.node().parameterMetadata( plug, "help" ) or ""

def __plugLabel( plug ) :

	return plug.node().parameterMetadata( plug, "label" )

def __plugDivider( plug ) :

	return plug.node().parameterMetadata( plug, "divider" ) or False

Gaffer.Metadata.registerNodeDescription( GafferOSL.OSLShader, __nodeDescription )

Gaffer.Metadata.registerPlugDescription( GafferOSL.OSLShader, "parameters.*", __plugDescription )
Gaffer.Metadata.registerPlugValue( GafferOSL.OSLShader, "parameters.*", "label", __plugLabel )
Gaffer.Metadata.registerPlugValue( GafferOSL.OSLShader, "parameters.*", "divider", __plugDivider )

##########################################################################
# Nodules
##########################################################################

def __outPlugNoduleCreator( plug ) :

	if isinstance( plug, Gaffer.CompoundPlug ) :
		return GafferUI.CompoundNodule( plug, GafferUI.LinearContainer.Orientation.Y, spacing = 0.2 )
	else :
		return GafferUI.StandardNodule( plug )

GafferUI.Nodule.registerNodule( GafferOSL.OSLShader, "out", __outPlugNoduleCreator )
