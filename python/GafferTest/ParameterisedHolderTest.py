##########################################################################
#  
#  Copyright (c) 2011, Image Engine Design Inc. All rights reserved.
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

from __future__ import with_statement

import unittest

import IECore

import Gaffer

class ParameterisedHolderTest( unittest.TestCase ) :

	## Different installations of cortex might have different version numbers
	# for the classes we're trying to load as part of the tests. This function
	# finds an appropriate version number. This is only really an issue because
	# Image Engine internal builds don't include cortex directly but instead
	# reference the central cortex install.
	@staticmethod
	def classSpecification( className, searchPathEnvVar ) :
	
		return (
			className,
			IECore.ClassLoader.defaultLoader( searchPathEnvVar ).versions( className )[-1],
			searchPathEnvVar
		)

	def testCreateEmpty( self ) :
	
		n = Gaffer.ParameterisedHolderNode()
		self.assertEqual( n.getName(), "ParameterisedHolderNode" )
		self.assertEqual( n.getParameterised(), ( None, "", -1, "" ) )

	def testSetParameterisedWithoutClassLoader( self ) :
	
		n = Gaffer.ParameterisedHolderNode()
		op = IECore.SequenceRenumberOp()
		
		n.setParameterised( op )
		self.assertEqual( n.getParameterised(), ( op, "", -1, "" ) )
		
	def testSimplePlugTypes( self ) :
	
		n = Gaffer.ParameterisedHolderNode()
		op = IECore.SequenceRenumberOp()		
		n.setParameterised( op )
		
		self.failUnless( isinstance( n["parameters"]["src"], Gaffer.StringPlug ) )
		self.failUnless( isinstance( n["parameters"]["dst"], Gaffer.StringPlug ) )
		self.failUnless( isinstance( n["parameters"]["multiply"], Gaffer.IntPlug ) )
		self.failUnless( isinstance( n["parameters"]["offset"], Gaffer.IntPlug ) )
		
		self.assertEqual( n["parameters"]["src"].defaultValue(), "" )
		self.assertEqual( n["parameters"]["dst"].defaultValue(), "" )
		self.assertEqual( n["parameters"]["multiply"].defaultValue(), 1 )
		self.assertEqual( n["parameters"]["offset"].defaultValue(), 0 )
		
		self.assertEqual( n["parameters"]["src"].getValue(), "" )
		self.assertEqual( n["parameters"]["dst"].getValue(), "" )
		self.assertEqual( n["parameters"]["multiply"].getValue(), 1 )
		self.assertEqual( n["parameters"]["offset"].getValue(), 0 )
		
		for k in op.parameters().keys() :
			self.assertEqual( n["parameters"][k].defaultValue(), op.parameters()[k].defaultValue.value )
			
		with n.parameterModificationContext() as parameters :
		
			parameters["multiply"].setNumericValue( 10 )
			parameters["dst"].setTypedValue( "/tmp/s.####.exr" )
			
		self.assertEqual( n["parameters"]["multiply"].getValue(), 10 )
		self.assertEqual( n["parameters"]["dst"].getValue(), "/tmp/s.####.exr" )
		
		n["parameters"]["multiply"].setValue( 20 )
		n["parameters"]["dst"].setValue( "lalalal.##.tif" )
		
		n.setParameterisedValues()
		
		self.assertEqual( op["multiply"].getNumericValue(), 20 )
		self.assertEqual( op["dst"].getTypedValue(), "lalalal.##.tif" )
	
	def testVectorTypedParameter( self ) :
	
		p = IECore.Parameterised( "" )
		
		p.parameters().addParameters(
			
			[
		
				IECore.BoolVectorParameter( "bv", "", IECore.BoolVectorData() ),
				IECore.IntVectorParameter( "iv", "", IECore.IntVectorData() ),
				IECore.FloatVectorParameter( "fv", "", IECore.FloatVectorData() ),
				IECore.StringVectorParameter( "sv", "", IECore.StringVectorData() ),
				IECore.V3fVectorParameter( "vv", "", IECore.V3fVectorData() ),
		
			]
			
		)	
		
		ph = Gaffer.ParameterisedHolderNode()
		ph.setParameterised( p )
		
		self.assertEqual( ph["parameters"]["bv"].defaultValue(), IECore.BoolVectorData() )
		self.assertEqual( ph["parameters"]["iv"].defaultValue(), IECore.IntVectorData() )
		self.assertEqual( ph["parameters"]["fv"].defaultValue(), IECore.FloatVectorData() )
		self.assertEqual( ph["parameters"]["sv"].defaultValue(), IECore.StringVectorData() )
		self.assertEqual( ph["parameters"]["vv"].defaultValue(), IECore.V3fVectorData() )
		
		self.assertEqual( ph["parameters"]["bv"].getValue(), IECore.BoolVectorData() )
		self.assertEqual( ph["parameters"]["iv"].getValue(), IECore.IntVectorData() )
		self.assertEqual( ph["parameters"]["fv"].getValue(), IECore.FloatVectorData() )
		self.assertEqual( ph["parameters"]["sv"].getValue(), IECore.StringVectorData() )
		self.assertEqual( ph["parameters"]["vv"].getValue(), IECore.V3fVectorData() )
		
		with ph.parameterModificationContext() as parameters :
		
			parameters["bv"].setValue( IECore.BoolVectorData( [ True, False ] ) )
			parameters["iv"].setValue( IECore.IntVectorData( [ 1, 2, 3 ] ) )
			parameters["fv"].setValue( IECore.FloatVectorData( [ 1 ] ) )
			parameters["sv"].setValue( IECore.StringVectorData( [ "a" ] ) )
			parameters["vv"].setValue( IECore.V3fVectorData( [ IECore.V3f( 1, 2, 3 ) ] ) )
		
		self.assertEqual( ph["parameters"]["bv"].getValue(), IECore.BoolVectorData( [ True, False ] ) )
		self.assertEqual( ph["parameters"]["iv"].getValue(), IECore.IntVectorData( [ 1, 2, 3 ] ) )
		self.assertEqual( ph["parameters"]["fv"].getValue(), IECore.FloatVectorData( [ 1 ] ) )
		self.assertEqual( ph["parameters"]["sv"].getValue(), IECore.StringVectorData( [ "a" ] ) )	
		self.assertEqual( ph["parameters"]["vv"].getValue(), IECore.V3fVectorData( [ IECore.V3f( 1, 2, 3 ) ] ) )
		
		ph["parameters"]["bv"].setValue( IECore.BoolVectorData( [ True, True ] ) )
		ph["parameters"]["iv"].setValue( IECore.IntVectorData( [ 2, 3, 4 ] ) )
		ph["parameters"]["fv"].setValue( IECore.FloatVectorData( [ 2 ] ) )
		ph["parameters"]["sv"].setValue( IECore.StringVectorData( [ "b" ] ) )
		ph["parameters"]["vv"].setValue( IECore.V3fVectorData( [ IECore.V3f( 10, 20, 30 ) ] ) )
		
		ph.setParameterisedValues()
		
		self.assertEqual( parameters["bv"].getValue(), IECore.BoolVectorData( [ True, True ] ) )
		self.assertEqual( parameters["iv"].getValue(), IECore.IntVectorData( [ 2, 3, 4 ] ) )
		self.assertEqual( parameters["fv"].getValue(), IECore.FloatVectorData( [ 2 ] ) )
		self.assertEqual( parameters["sv"].getValue(), IECore.StringVectorData( [ "b" ] ) )
		self.assertEqual( parameters["vv"].getValue(), IECore.V3fVectorData( [ IECore.V3f( 10, 20, 30 ) ] ) )
		
	def testNoHostMapping( self ) :
	
		p = IECore.Parameterised( "" )
		
		p.parameters().addParameters(
			
			[
		
				IECore.IntParameter( "i1", "", 1, userData = { "noHostMapping" : IECore.BoolData( False ) } ),
				IECore.IntParameter( "i2", "", 2, userData = { "noHostMapping" : IECore.BoolData( True ) } ),
				IECore.IntParameter( "i3", "", 2 ),
		
			]
			
		)
		
		ph = Gaffer.ParameterisedHolderNode()
		ph.setParameterised( p )
		
		self.failUnless( "i1" in ph["parameters"] )
		self.failIf( "i2" in ph["parameters"] )
		self.failUnless( "i3" in ph["parameters"] )
	
	def testCreateWithNonDefaultValues( self ) :
	
		p = IECore.Parameterised( "" )
		p.parameters().addParameter( IECore.IntParameter( "i1", "", 1, ) )
		
		p["i1"].setNumericValue( 10 )
		
		ph = Gaffer.ParameterisedHolderNode()
		ph.setParameterised( p )
		
		self.assertEqual( ph["parameters"]["i1"].defaultValue(), 1 )
		self.assertEqual( ph["parameters"]["i1"].getValue(), 10 )
	
	def testCompoundNumericTypes( self ) :
	
		p = IECore.Parameterised( "" )
		
		p.parameters().addParameters(
		
			[
				IECore.V2iParameter( "v2i", "", IECore.V2i( 1, 2 ) ),
				IECore.V3fParameter( "v3f", "", IECore.V3f( 1, 2, 3 ) ),
				IECore.Color4fParameter( "color4f", "", IECore.Color4f( 0.25, 0.5, 0.75, 1 ) ),
			]
		
		)
		
		ph = Gaffer.ParameterisedHolderNode()
		ph.setParameterised( p )
		
		self.assertEqual( ph["parameters"]["v2i"].defaultValue(), IECore.V2i( 1, 2 ) )
		self.assertEqual( ph["parameters"]["v3f"].defaultValue(), IECore.V3f( 1, 2, 3 ) )
		self.assertEqual( ph["parameters"]["color4f"].defaultValue(), IECore.Color4f( 0.25, 0.5, 0.75, 1 ) )
		
		self.assertEqual( ph["parameters"]["v2i"].getValue(), IECore.V2i( 1, 2 ) )
		self.assertEqual( ph["parameters"]["v3f"].getValue(), IECore.V3f( 1, 2, 3 ) )
		self.assertEqual( ph["parameters"]["color4f"].getValue(), IECore.Color4f( 0.25, 0.5, 0.75, 1 ) )
		
		ph["parameters"]["v2i"].setValue( IECore.V2i( 2, 3 ) )
		ph["parameters"]["v3f"].setValue( IECore.V3f( 4, 5, 6 ) )
		ph["parameters"]["color4f"].setValue( IECore.Color4f( 0.1, 0.2, 0.3, 0.5 ) )
		
		ph.setParameterisedValues()

		self.assertEqual( p["v2i"].getTypedValue(), IECore.V2i( 2, 3 ) )
		self.assertEqual( p["v3f"].getTypedValue(), IECore.V3f( 4, 5, 6 ) )
		self.assertEqual( p["color4f"].getTypedValue(), IECore.Color4f( 0.1, 0.2, 0.3, 0.5 ) )
		
	def testParameterHandlerMethod( self ) :
	
		p = IECore.Parameterised( "" )
		p.parameters().addParameter( IECore.IntParameter( "i1", "", 1, ) )
		
		ph = Gaffer.ParameterisedHolderNode()
		ph.setParameterised( p )
		
		h = ph.parameterHandler()
		self.failUnless( isinstance( h, Gaffer.CompoundParameterHandler ) )
		self.failUnless( h.parameter().isSame( p.parameters() ) )
		self.failUnless( h.plug().isSame( ph["parameters"] ) )
	
	def testBoxTypes( self ) :
	
		p = IECore.Parameterised( "" )
		
		p.parameters().addParameters(
		
			[
				IECore.Box3iParameter(
					"b",
					"",
					IECore.Box3i(
						IECore.V3i( -1, -2, -3 ), 
						IECore.V3i( 2, 1, 3 ), 
					),
				)			
			]
		
		)
		
		ph = Gaffer.ParameterisedHolderNode()
		ph.setParameterised( p )
		
		self.failUnless( isinstance( ph["parameters"]["b"], Gaffer.CompoundPlug ) )
		self.failUnless( isinstance( ph["parameters"]["b"]["min"], Gaffer.V3iPlug ) )
		self.failUnless( isinstance( ph["parameters"]["b"]["max"], Gaffer.V3iPlug ) )
		
		self.assertEqual( ph["parameters"]["b"]["min"].getValue(), IECore.V3i( -1, -2, -3 ) )
		self.assertEqual( ph["parameters"]["b"]["max"].getValue(), IECore.V3i( 2, 1, 3 ) )
		
		ph["parameters"]["b"]["min"].setValue( IECore.V3i( -10, -20, -30 ) )
		ph["parameters"]["b"]["max"].setValue( IECore.V3i( 10, 20, 30 ) )
		
		ph.parameterHandler().setParameterValue()
		
		self.assertEqual(
			p["b"].getTypedValue(),
			IECore.Box3i( IECore.V3i( -10, -20, -30 ), IECore.V3i( 10, 20, 30 ) )
		)
		
		with ph.parameterModificationContext() :
		
			p["b"].setTypedValue( IECore.Box3i( IECore.V3i( -2, -4, -6 ), IECore.V3i( 2, 4, 6 ) ) )
		
		self.assertEqual( ph["parameters"]["b"]["min"].getValue(), IECore.V3i( -2, -4, -6 ) )
		self.assertEqual( ph["parameters"]["b"]["max"].getValue(), IECore.V3i( 2, 4, 6 ) )
		
	def testAddAndRemoveParameters( self ) :
	
		p = IECore.Parameterised( "" )
		
		p.parameters().addParameter(
		
			IECore.IntParameter(
				"a",
				"",
				1
			)
		
		)
		
		ph = Gaffer.ParameterisedHolderNode()
		ph.setParameterised( p )
		
		self.failUnless( isinstance( ph["parameters"], Gaffer.CompoundPlug ) )
		self.failUnless( isinstance( ph["parameters"]["a"], Gaffer.IntPlug ) )
		self.assertEqual( len( ph["parameters"] ), 1 )
		
		with ph.parameterModificationContext() :
		
			p.parameters().removeParameter( p.parameters()["a"] )
			p.parameters().addParameter( IECore.IntParameter( "b", "", 2 ) )
			
		self.failUnless( isinstance( ph["parameters"], Gaffer.CompoundPlug ) )
		self.failUnless( isinstance( ph["parameters"]["b"], Gaffer.IntPlug ) )
		self.assertEqual( len( ph["parameters"] ), 1 )		
	
	def testParameterChangingType( self ) :
	
		p = IECore.Parameterised( "" )
		
		p.parameters().addParameter(
		
			IECore.IntParameter(
				"a",
				"",
				1
			)

		)
		
		ph = Gaffer.ParameterisedHolderNode()
		ph.setParameterised( p )
		
		self.failUnless( isinstance( ph["parameters"], Gaffer.CompoundPlug ) )
		self.failUnless( isinstance( ph["parameters"]["a"], Gaffer.IntPlug ) )
		self.assertEqual( len( ph["parameters"] ), 1 )
		
		with ph.parameterModificationContext() :
			p.parameters().removeParameter( p.parameters()["a"] )
			p.parameters().addParameter( IECore.FloatParameter( "a", "", 2 ) )
		
		self.failUnless( isinstance( ph["parameters"], Gaffer.CompoundPlug ) )
		self.failUnless( isinstance( ph["parameters"]["a"], Gaffer.FloatPlug ) )
		self.assertEqual( len( ph["parameters"] ), 1 )
		
	def testParameterHandlerIsConstant( self ) :
	
		# We need the ParameterisedHolder to keep using the same ParameterHandler,
		# as otherwise the ui code would become much more complex, having to track
		# the addition and removal of different parameter handlers.
		
		p = IECore.Parameterised( "" )
		
		phn = Gaffer.ParameterisedHolderNode()
		phn.setParameterised( p )

		ph = phn.parameterHandler()
		
		with phn.parameterModificationContext() :
			p.parameters().addParameter( IECore.FloatParameter( "a", "", 2 ) )
		
		self.failUnless( ph.isSame( phn.parameterHandler() ) )					
	
	def testClassLoading( self ) :
	
		ph = Gaffer.ParameterisedHolderNode()
		classSpec = self.classSpecification( "common/fileSystem/seqLs", "IECORE_OP_PATHS" )
		ph.setParameterised( *classSpec )
		
		p = ph.getParameterised()
		self.assertEqual( p[0].typeName(), "SequenceLsOp" )
		self.assertEqual( p[1], "common/fileSystem/seqLs" )
		self.assertEqual( p[2], classSpec[1] )
		self.assertEqual( p[3], "IECORE_OP_PATHS" )

	def testRunTimeTyped( self ) :
	
		n = Gaffer.ParameterisedHolderNode()
		
		self.assertEqual( n.typeName(), "ParameterisedHolderNode" )
		self.assertEqual( IECore.RunTimeTyped.typeNameFromTypeId( n.typeId() ), "ParameterisedHolderNode" )
		self.assertEqual( IECore.RunTimeTyped.baseTypeId( n.typeId() ), Gaffer.Node.staticTypeId() )
	
	def testSerialisation( self ) :
	
		ph = Gaffer.ParameterisedHolderNode()
		classSpec = self.classSpecification( "common/colorSpace/grade", "IECORE_OP_PATHS" )
		ph.setParameterised( *classSpec )
			
		s = Gaffer.ScriptNode()
		s["n"] = ph
		
		ss = s.serialise()
		
		s = Gaffer.ScriptNode()
		s.execute( ss )
				
if __name__ == "__main__":
	unittest.main()
	
