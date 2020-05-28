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

# Implemented in Python because ClassVectorParameter is implemented in Python, and
# we don't want to introduce a Python dependency into libGafferCortex.
class ClassVectorParameterHandler( GafferCortex.CompoundParameterHandler ) :

	def __init__( self, parameter ) :

		GafferCortex.CompoundParameterHandler.__init__( self, parameter )

		assert( isinstance( parameter, IECore.ClassVectorParameter ) )

	def restore( self, plugParent ) :

		compoundPlug = plugParent.getChild( self.parameter().name )
		if compoundPlug is not None :
			classNames = compoundPlug["__classNames"].getValue()
			classVersions = compoundPlug["__classVersions"].getValue()
			parameterNames = [ k for k in compoundPlug.keys() if not k.startswith( "__" ) ]
			self.parameter().setClasses( list( zip( parameterNames, classNames, classVersions ) ) )

		GafferCortex.CompoundParameterHandler.restore( self, plugParent )

	def setupPlug( self, plugParent, direction, flags ) :

		GafferCortex.CompoundParameterHandler.setupPlug( self, plugParent, direction, flags )

		# add the class specification plugs now if they're not there.
		compoundPlug = self.plug()
		if "__classNames" not in compoundPlug :
			compoundPlug["__classNames"] = Gaffer.StringVectorDataPlug( "__classNames", Gaffer.Plug.Direction.In, IECore.StringVectorData(), flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
			compoundPlug["__classVersions"] = Gaffer.IntVectorDataPlug( "__classVersions", Gaffer.Plug.Direction.In, IECore.IntVectorData(), flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		# store the current classes
		self.__storeClasses()

	def setParameterValue( self ) :

		GafferCortex.CompoundParameterHandler.setParameterValue( self )

	def setPlugValue( self ) :

		GafferCortex.CompoundParameterHandler.setPlugValue( self )

		self.__storeClasses()

	def childParameterProvider( self, childParameter ) :

		if childParameter.name not in self.parameter() :
			return None

		if not self.parameter()[childParameter.name].isSame( childParameter ) :
			return None

		return self.parameter().getClass( childParameter )

	def __storeClasses( self ) :

		compoundPlug = self.plug()
		classes = self.parameter().getClasses( True )
		compoundPlug["__classNames"].setValue( IECore.StringVectorData( [ c[2] for c in classes ] ) )
		compoundPlug["__classVersions"].setValue( IECore.IntVectorData( [ c[3] for c in classes ] ) )

GafferCortex.ParameterHandler.registerParameterHandler( IECore.ClassVectorParameter, ClassVectorParameterHandler )
