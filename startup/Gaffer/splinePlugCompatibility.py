##########################################################################
#
#  Copyright (c) 2017, Image Engine Design Inc. All rights reserved.
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
import IECore


def __convertCortexSpline( spline, oldType, newType ):
	if type( spline ) != oldType :
		# Not the case we need to fix
		return spline

	interpolation = None
	if spline.basis == type( spline.basis ).linear():
		interpolation = Gaffer.SplineDefinitionInterpolation.Linear
	elif spline.basis == type( spline.basis ).catmullRom():
		interpolation = Gaffer.SplineDefinitionInterpolation.CatmullRom
	elif spline.basis == eval( repr( type( spline.basis ).bSpline() ) ):
		# Note that serialising the bSpline basis alters it slightly due to floating point precision,
		# so we have to compare to altered version
		interpolation = Gaffer.SplineDefinitionInterpolation.BSpline
	else:
		raise Exception( "Error setting " + newType.__name__ + "- Unrecognized basis: " + repr( spline.basis ) )

	result = newType( spline.points(), interpolation )
	if not result.trimEndPoints():
		raise Exception( "Error setting " + newType.__name__ + "- Could not convert: " + repr( spline ) )

	return result



def __initWrapper( originalInit, defaultName, oldValueType, valueType ):

	def init( self, name = defaultName, direction = Gaffer.Plug.Direction.In,
		defaultValue = valueType(), flags = Gaffer.Plug.Flags.Default ):

		originalInit( self, name, direction, __convertCortexSpline( defaultValue, oldValueType, valueType ), flags )

	return init

Gaffer.SplineffPlug.__init__ = __initWrapper( Gaffer.SplineffPlug.__init__, "SplineffPlug",
	IECore.Splineff, Gaffer.SplineDefinitionff )
Gaffer.SplinefColor3fPlug.__init__ = __initWrapper( Gaffer.SplinefColor3fPlug.__init__, "SplinefColor3fPlug",
	IECore.SplinefColor3f, Gaffer.SplineDefinitionfColor3f )

def __setValueWrapper( originalSetValue, oldValueType, valueType ):

	def setValue( self, value ):

		originalSetValue( self, __convertCortexSpline( value, oldValueType, valueType ) )

	return setValue

Gaffer.SplineffPlug.setValue = __setValueWrapper( Gaffer.SplineffPlug.setValue,
	IECore.Splineff, Gaffer.SplineDefinitionff )
Gaffer.SplinefColor3fPlug.setValue = __setValueWrapper( Gaffer.SplinefColor3fPlug.setValue,
	IECore.SplinefColor3f, Gaffer.SplineDefinitionfColor3f )


class __DummyIgnoreAllSetValuesRecursive( object ) :

	def setValue( self, value ) :
		pass

	def __getitem__( self, item ) :
		return self

def __getitemWrapper( originalGetitem ):

	def getItem( self, item ):

		if item == "basis":
			return __DummyIgnoreAllSetValuesRecursive()
		else:
			return originalGetitem( self, item )

	return getItem

Gaffer.SplineffPlug.__getitem__ = __getitemWrapper( Gaffer.SplineffPlug.__getitem__ )
Gaffer.SplinefColor3fPlug.__getitem__ = __getitemWrapper( Gaffer.SplinefColor3fPlug.__getitem__ )
