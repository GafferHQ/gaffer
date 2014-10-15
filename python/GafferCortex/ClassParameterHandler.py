##########################################################################
#
#  Copyright (c) 2012-2014, Image Engine Design Inc. All rights reserved.
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

import Gaffer
import GafferCortex

# Implemented in Python because ClassParameter is implemented in Python, and
# we don't want to introduce a Python dependency into libGafferCortex.
class ClassParameterHandler( GafferCortex.CompoundParameterHandler ) :

	def __init__( self, parameter ) :

		GafferCortex.CompoundParameterHandler.__init__( self, parameter )

		assert( isinstance( parameter, IECore.ClassParameter ) )

	def restore( self, plugParent ) :

		compoundPlug = plugParent.getChild( self.parameter().name )
		if compoundPlug is not None :
			className = compoundPlug["__className"].getValue()
			classVersion = compoundPlug["__classVersion"].getValue()
			searchPathEnvVar = compoundPlug["__searchPathEnvVar"].getValue()
			self.parameter().setClass( className, classVersion, searchPathEnvVar )

		GafferCortex.CompoundParameterHandler.restore( self, plugParent )

	def setupPlug( self, plugParent, direction, flags ) :

		GafferCortex.CompoundParameterHandler.setupPlug( self, plugParent, direction, flags )

		# add the class specification plugs now if they're not there.
		compoundPlug = self.plug()
		if "__className" not in compoundPlug :
			compoundPlug["__className"] = Gaffer.StringPlug( "__className", Gaffer.Plug.Direction.In, "", flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
			compoundPlug["__classVersion"] = Gaffer.IntPlug( "__classVersion", Gaffer.Plug.Direction.In, 0, flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
			compoundPlug["__searchPathEnvVar"] = Gaffer.StringPlug( "__searchPathEnvVar", Gaffer.Plug.Direction.In, "", flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		# store the current class
		c = self.parameter().getClass( True )
		compoundPlug["__className"].setValue( c[1] )
		compoundPlug["__classVersion"].setValue( c[2] )
		compoundPlug["__searchPathEnvVar"].setValue( c[3] )

	def setParameterValue( self ) :

		GafferCortex.CompoundParameterHandler.setParameterValue( self )

	def setPlugValue( self ) :

		GafferCortex.CompoundParameterHandler.setPlugValue( self )

		c = self.parameter().getClass( True )

		self.plug()["__className"].setValue( c[1] )
		self.plug()["__classVersion"].setValue( c[2] )
		self.plug()["__searchPathEnvVar"].setValue( c[3] )

	def childParameterProvider( self, childParameter ) :

		if childParameter.name not in self.parameter() :
			return None

		if not self.parameter()[childParameter.name].isSame( childParameter ) :
			return None

		return self.parameter().getClass( False )

GafferCortex.ParameterHandler.registerParameterHandler( IECore.ClassParameter, ClassParameterHandler )
