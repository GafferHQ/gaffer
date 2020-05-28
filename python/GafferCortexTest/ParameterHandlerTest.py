##########################################################################
#
#  Copyright (c) 2011-2014, Image Engine Design Inc. All rights reserved.
#  Copyright (c) 2011, John Haddon. All rights reserved.
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

import unittest

import IECore

import Gaffer
import GafferTest
import GafferCortex

class ParameterHandlerTest( GafferTest.TestCase ) :

	def testFactory( self ) :

		p = IECore.IntParameter( "i", "d", 10 )

		n = Gaffer.Node()
		h = GafferCortex.ParameterHandler.create( p )
		h.setupPlug( n )

		self.assertIsInstance( h, GafferCortex.ParameterHandler )
		self.assertIsInstance( n["i"], Gaffer.IntPlug )

	def testCustomHandler( self ) :

		class CustomParameter( IECore.IntParameter ) :

			def __init__( self, name, description, defaultValue ) :

				IECore.IntParameter.__init__( self, name, description, defaultValue )

		IECore.registerRunTimeTyped( CustomParameter )

		class CustomHandler( GafferCortex.ParameterHandler ) :

			def __init__( self, parameter ) :

				GafferCortex.ParameterHandler.__init__( self )

				self.__parameter = parameter
				self.__plug = None

			def parameter( self ) :

				return self.__parameter

			def setupPlug( self, plugParent, direction, flags ) :

				self.__plug = plugParent.getChild( self.__parameter.name )
				if not isinstance( self.__plug, Gaffer.IntPlug ) or self.__plug.direction() != direction :
					self.__plug = Gaffer.IntPlug(
						self.__parameter.name,
						Gaffer.Plug.Direction.In,
						self.__parameter.numericDefaultValue,
						self.__parameter.minValue,
						self.__parameter.maxValue
					)

				## \todo: should ParameterHandler::setupPlugFlags be exposed so we can call it here?
				self.__plug.setFlags( flags )

				plugParent[self.__parameter.name] = self.__plug

			def plug( self ) :

				return self.__plug

			def setParameterValue( self ) :

				self.__parameter.setValue( self.__plug.getValue() * 10 )

			def setPlugValue( self ) :

				self.__plug.setValue( self.__parameter.getNumericValue() // 10 )

		GafferCortex.ParameterHandler.registerParameterHandler( CustomParameter, CustomHandler )

		p = IECore.Parameterised( "" )
		p.parameters().addParameter(

			CustomParameter(

				"i",
				"d",
				10

			)

		)

		ph = GafferCortex.ParameterisedHolderNode()
		ph.setParameterised( p )

		self.assertEqual( ph["parameters"]["i"].getValue(), 1 )

		with ph.parameterModificationContext() as parameters :

			p["i"].setNumericValue( 100 )

		self.assertEqual( ph["parameters"]["i"].getValue(), 10 )

		ph["parameters"]["i"].setValue( 1000 )

		ph.setParameterisedValues()

		self.assertEqual( p["i"].getNumericValue(), 10000 )

	def testPlugMethod( self ) :

		p = IECore.IntParameter( "i", "d", 10 )

		n = Gaffer.Node()
		h = GafferCortex.ParameterHandler.create( p )
		h.setupPlug( n )

		self.assertEqual( h.plug().getName(), "i" )
		self.assertTrue( h.plug().parent().isSame( n ) )

	def testCompoundParameterHandler( self ) :

		c = IECore.CompoundParameter(

			"c",
			"",

			[
				IECore.IntParameter( "i", "" ),
				IECore.FloatParameter( "f", "" )
			]

		)

		n = Gaffer.Node()

		h = GafferCortex.CompoundParameterHandler( c )
		h.setupPlug( n )

		self.assertTrue( h.childParameterHandler( c["i"] ).parameter().isSame( c["i"] ) )
		self.assertTrue( h.childParameterHandler( c["f"] ).parameter().isSame( c["f"] ) )

	def testReadOnly( self ) :

		p = IECore.IntParameter( "i", "d", 10 )

		n = Gaffer.Node()
		h = GafferCortex.ParameterHandler.create( p )
		h.setupPlug( n )

		self.assertFalse( Gaffer.MetadataAlgo.getReadOnly( h.plug() ) )

		p.userData()["gaffer"] = IECore.CompoundObject( {
			"readOnly" : IECore.BoolData( True ),
		} )

		h.setupPlug( n )
		self.assertTrue( Gaffer.MetadataAlgo.getReadOnly( h.plug() ) )

	def testNonDefaultFlags( self ) :

		p = IECore.IntParameter( "i", "d", 10 )

		n = Gaffer.Node()
		h = GafferCortex.ParameterHandler.create( p )

		h.setupPlug( n )
		self.assertTrue( h.plug().getFlags( Gaffer.Plug.Flags.Dynamic ) )
		self.assertTrue( h.plug().getFlags( Gaffer.Plug.Flags.Serialisable ) )

		h.setupPlug( n, flags = Gaffer.Plug.Flags.Default )
		self.assertFalse( h.plug().getFlags( Gaffer.Plug.Flags.Dynamic ) )
		self.assertTrue( h.plug().getFlags( Gaffer.Plug.Flags.Serialisable ) )

		h.setupPlug( n, flags = Gaffer.Plug.Flags.Default & ~Gaffer.Plug.Flags.Serialisable )
		self.assertFalse( h.plug().getFlags( Gaffer.Plug.Flags.Dynamic ) )
		self.assertFalse( h.plug().getFlags( Gaffer.Plug.Flags.Serialisable ) )

	def testHash( self ) :

		c = IECore.CompoundParameter(

			"c",
			"",

			[
				IECore.IntParameter( "i", "" ),
				IECore.FloatParameter( "f", "" )
			]

		)

		n = Gaffer.Node()

		h = GafferCortex.CompoundParameterHandler( c )
		h.setupPlug( n )

		hash1 = h.hash()
		n["c"]["i"].setValue( 10 )
		hash2 = h.hash()
		n["c"]["f"].setValue( 10 )
		hash3 = h.hash()

		self.assertNotEqual( hash1, hash2 )
		self.assertNotEqual( hash1, hash3 )
		self.assertNotEqual( hash2, hash3 )

	def testSubstitutions( self ) :

		p = IECore.StringParameter( "s", "d", "" )

		n = Gaffer.Node()
		h = GafferCortex.ParameterHandler.create( p )
		h.setupPlug( n )
		self.assertEqual( n["s"].substitutions(), IECore.StringAlgo.Substitutions.AllSubstitutions )

		# adding substitutions should affect the plug
		p.userData()["gaffer"] = IECore.CompoundObject( {
			"substitutions" : IECore.IntData( IECore.StringAlgo.Substitutions.AllSubstitutions & ~IECore.StringAlgo.Substitutions.FrameSubstitutions ),
		} )
		h.setupPlug( n )
		self.assertEqual( n["s"].substitutions(), IECore.StringAlgo.Substitutions.AllSubstitutions & ~IECore.StringAlgo.Substitutions.FrameSubstitutions )

		# make sure connections are maintained as well
		nn = Gaffer.Node()
		nn["driver"] = Gaffer.StringPlug()
		n["s"].setInput( nn["driver"] )
		# we're forcing a re-creation of the plug because substitutions have changed
		p.userData()["gaffer"] = IECore.CompoundObject( {
			"substitutions" : IECore.IntData( IECore.StringAlgo.Substitutions.AllSubstitutions & ~IECore.StringAlgo.Substitutions.VariableSubstitutions ),
		} )
		h.setupPlug( n )
		self.assertEqual( n["s"].substitutions(), IECore.StringAlgo.Substitutions.AllSubstitutions & ~IECore.StringAlgo.Substitutions.VariableSubstitutions )
		self.assertEqual( n["s"].getInput(), nn["driver"] )

if __name__ == "__main__":
	unittest.main()
