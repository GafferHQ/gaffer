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

import IECore
import IECoreScene

import Gaffer
import GafferScene

def __compatibilityFunc( node, oldParent ):
	parentNode = node.ancestor( Gaffer.Node )
	while parentNode :
		gafferVersion = (
			Gaffer.Metadata.value( parentNode, "serialiser:milestoneVersion" ),
			Gaffer.Metadata.value( parentNode, "serialiser:majorVersion" ),
			Gaffer.Metadata.value( parentNode, "serialiser:minorVersion" ),
			Gaffer.Metadata.value( parentNode, "serialiser:patchVersion" )
		)

		# only use the information if we have valid information from the node
		if not filter( lambda x : x is None, gafferVersion ) :
			break

		gafferVersion = None
		parentNode = parentNode.ancestor( Gaffer.Node )

	if gafferVersion is not None and gafferVersion < ( 0, 52, 0, 0 ) :
		# The old Gaffer implicitly used a film fit of "Fit".  This was usually undesirable
		# ( It resulted in usually getting a vertical fit, whereas artists expect horizontal ),
		# but for compatibility's sake we set up old cameras so that they will continue to do this

		node["renderSettingOverrides"]["filmFit"]["enabled"].setValue( True )
		node["renderSettingOverrides"]["filmFit"]["value"].setValue( IECoreScene.Camera.FilmFit.Fit )

def __initWrapper( originalInit, defaultName ):

	def init( self, name = defaultName ):
		originalInit( self, name )
		self.__compatibilityCallback = self.parentChangedSignal().connect( __compatibilityFunc )

	return init

GafferScene.Camera.__init__ = __initWrapper( GafferScene.Camera.__init__, "Camera" )

