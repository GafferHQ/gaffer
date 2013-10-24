##########################################################################
#  
#  Copyright (c) 2011-2012, Image Engine Design Inc. All rights reserved.
#  Copyright (c) 2011-2012, John Haddon. All rights reserved.
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

import os
import unittest
import datetime

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
		classSpec = self.classSpecification( "files/sequenceLs", "IECORE_OP_PATHS" )
		ph.setParameterised( *classSpec )
		
		p = ph.getParameterised()
		self.assertEqual( p[0].typeName(), "SequenceLsOp" )
		self.assertEqual( p[1], "files/sequenceLs" )
		self.assertEqual( p[2], classSpec[1] )
		self.assertEqual( p[3], "IECORE_OP_PATHS" )

	def testRunTimeTyped( self ) :
	
		n = Gaffer.ParameterisedHolderNode()
		
		self.assertEqual( n.typeName(), "Gaffer::ParameterisedHolderNode" )
		self.assertEqual( IECore.RunTimeTyped.typeNameFromTypeId( n.typeId() ), "Gaffer::ParameterisedHolderNode" )
		self.assertEqual( IECore.RunTimeTyped.baseTypeId( n.typeId() ), Gaffer.Node.staticTypeId() )
	
	def testSerialisation( self ) :
	
		ph = Gaffer.ParameterisedHolderNode()
		classSpec = self.classSpecification( "image/grade", "IECORE_OP_PATHS" )
		ph.setParameterised( *classSpec )
			
		s = Gaffer.ScriptNode()
		s["n"] = ph
		s["n"]["parameters"]["lift"].setValue( IECore.Color3f( 1, 0, 0 ) )
		
		ss = s.serialise()
		
		s = Gaffer.ScriptNode()
		s.execute( ss )
		
		self.failUnless( "n" in s )
		parameterised = s["n"].getParameterised()
		
		self.assertEqual( parameterised[1:], classSpec )
		self.assertEqual( parameterised[0].typeName(), "Grade" )
		self.assertEqual( s["n"]["parameters"]["lift"].getValue(), IECore.Color3f( 1, 0, 0 ) )
	
	def testKeepExistingValues( self ) :
	
		ph = Gaffer.ParameterisedHolderNode()
		
		ph.setParameterised( IECore.Grade() )
		ph["parameters"]["lift"].setValue( IECore.Color3f( 1, 0, 0 ) )
		
		ph.setParameterised( IECore.Grade() )
		self.assertEqual( ph["parameters"]["lift"].getValue(), IECore.Color3f( 0 ) )
		
		ph["parameters"]["lift"].setValue( IECore.Color3f( 1, 0, 0 ) )
		ph.setParameterised( IECore.Grade(), keepExistingValues=True )
		self.assertEqual( ph["parameters"]["lift"].getValue(), IECore.Color3f( 1, 0, 0 ) )
		
	def testDateTimeParameter( self ) :
	
		p = IECore.Parameterised( "" )
		
		now = datetime.datetime.now()
		p.parameters().addParameters(
		
			[
				IECore.DateTimeParameter(
					"dt",
					"",
					now
				)			
			]
		
		)
		
		ph = Gaffer.ParameterisedHolderNode()
		ph.setParameterised( p )
		
		self.failUnless( isinstance( ph["parameters"]["dt"], Gaffer.StringPlug ) )
		
		ph.parameterHandler().setParameterValue()
		self.assertEqual( p["dt"].getValue(), IECore.DateTimeData( now ) )
		
		tomorrow = now + datetime.timedelta( days=1 )
		p["dt"].setValue( IECore.DateTimeData( tomorrow ) )
		ph.parameterHandler().setPlugValue()
		ph.parameterHandler().setParameterValue()
		self.assertEqual( p["dt"].getValue(), IECore.DateTimeData( tomorrow ) )
	
	def testClassParameter( self ) :
			
		ph = Gaffer.ParameterisedHolderNode()
		ph.setParameterised( "classParameter", 1, "GAFFERTEST_CLASS_PATHS" )
		p = ph.getParameterised()[0]
		
		with ph.parameterModificationContext() :
			p["class"].setClass( *self.classSpecification( "files/sequenceLs", "IECORE_OP_PATHS" ) )

		seqLsParameterNames = p["class"].keys()	
		for n in seqLsParameterNames :
			self.failUnless( n in ph["parameters"]["class"] )
			
		with ph.parameterModificationContext() :
			p["class"].setClass( "", 0 )
		
		for n in seqLsParameterNames :
			self.failIf( n in ph["parameters"]["class"] )
		
	def testClassParameterSerialisation( self ) :
	
		s = Gaffer.ScriptNode()
		
		s["ph"] = Gaffer.ParameterisedHolderNode()
		s["ph"].setParameterised( "classParameter", 1, "GAFFERTEST_CLASS_PATHS" )
		
		p = s["ph"].getParameterised()[0]
		
		classSpec = self.classSpecification( "files/sequenceLs", "IECORE_OP_PATHS" )
		with s["ph"].parameterModificationContext() :
			p["class"].setClass( *classSpec )
		
		classPlugNames = s["ph"]["parameters"]["class"].keys()
		for k in p["class"].keys() :
			self.failUnless( k in classPlugNames )
		
		s["ph"]["parameters"]["class"]["recurse"].setValue( True )
	
		ss = s.serialise()
		
		s2 = Gaffer.ScriptNode()
		s2.execute( ss )
		
		self.assertEqual( s2["ph"]["parameters"]["class"].keys(), classPlugNames )
		
		p2 = s2["ph"].getParameterised()[0]
		
		self.assertEqual( p2["class"].getClass( True )[1:], classSpec )
		
		s2["ph"].parameterHandler().setParameterValue()
		self.assertEqual( p2["class"]["recurse"].getTypedValue(), True )
			
	def testClassVectorParameter( self ) :
			
		ph = Gaffer.ParameterisedHolderNode()
		ph.setParameterised( "classVectorParameter", 1, "GAFFERTEST_CLASS_PATHS" )
		p = ph.getParameterised()[0]
		
		seqLsClassSpec = self.classSpecification( "files/sequenceLs", "IECORE_OP_PATHS" )[:2]
		gradeClassSpec = self.classSpecification( "image/grade", "IECORE_OP_PATHS" )[:2]
		classes = [
			( "p0", ) + seqLsClassSpec,
			( "p1", ) + gradeClassSpec,
		]
		
		with ph.parameterModificationContext() :
			p["classes"].setClasses( classes )

		seqLsParameterNames = p["classes"]["p0"].keys()	
		for n in seqLsParameterNames :
			self.failUnless( n in ph["parameters"]["classes"]["p0"] )
		
		gradeParameterNames = p["classes"]["p1"].keys()	
		for n in gradeParameterNames :
			self.failUnless( n in ph["parameters"]["classes"]["p1"] )
			
		with ph.parameterModificationContext() :
			p["classes"].setClasses( [] )
		
		for k in ph["parameters"]["classes"].keys() :
			self.failUnless( k.startswith( "__" ) )
	
	def testClassVectorParameterMaintainsPlugValues( self ) :
	
		ph = Gaffer.ParameterisedHolderNode()
		ph.setParameterised( "classVectorParameter", 1, "GAFFERTEST_CLASS_PATHS" )
		p = ph.getParameterised()[0]
		
		seqLsClassSpec = self.classSpecification( "files/sequenceLs", "IECORE_OP_PATHS" )[:2]
		gradeClassSpec = self.classSpecification( "image/grade", "IECORE_OP_PATHS" )[:2]
		classes = [
			( "p0", ) + gradeClassSpec,
		]
		
		with ph.parameterModificationContext() :
			p["classes"].setClasses( classes )
		
		ph["parameters"]["classes"]["p0"]["multiply"].setValue( IECore.Color3f( 0.5, 0.25, 0.125 ) )
		ph.setParameterisedValues()
		
		classes.append( ( "p1", ) + seqLsClassSpec )		
		with ph.parameterModificationContext() :
			p["classes"].setClasses( classes )
			
		self.assertEqual( ph["parameters"]["classes"]["p0"]["multiply"].getValue(), IECore.Color3f( 0.5, 0.25, 0.125 ) )	
	
	def testClassVectorParameterSerialisation( self ) :
	
		s = Gaffer.ScriptNode()
		s["ph"] = Gaffer.ParameterisedHolderNode()
		s["ph"].setParameterised( "classVectorParameter", 1, "GAFFERTEST_CLASS_PATHS" )
		p = s["ph"].getParameterised()[0]
		
		gradeClassSpec = self.classSpecification( "image/grade", "IECORE_OP_PATHS" )[:2]
		classes = [
			( "p0", ) + gradeClassSpec,
		]
		
		with s["ph"].parameterModificationContext() :
			p["classes"].setClasses( classes )
		
		s["ph"]["parameters"]["classes"]["p0"]["multiply"].setValue( IECore.Color3f( 0.5, 0.25, 0.125 ) )

		ss = s.serialise()
		
		s2 = Gaffer.ScriptNode()
		s2.execute( ss )
		
		self.assertEqual( s2["ph"]["parameters"]["classes"]["p0"]["multiply"].getValue(), IECore.Color3f( 0.5, 0.25, 0.125 ) )

	def testTimeCodeParameter( self ) :
		
		p = IECore.Parameterised( "" )
		
		p.parameters().addParameters(
		
			[
				IECore.TimeCodeParameter(
					"t",
					"",
					IECore.TimeCode(
						hours = 10,
						minutes = 15,
						seconds = 1,
						frame = 12,
					)
				)			
			]
		
		)
		
		ph = Gaffer.ParameterisedHolderNode()
		ph.setParameterised( p )
		
		self.failUnless( "t" in ph["parameters"] )
		self.failUnless( isinstance( ph["parameters"]["t"], Gaffer.CompoundPlug ) )

		self.failUnless( isinstance( ph["parameters"]["t"]["hours"], Gaffer.IntPlug ) )
		self.assertEqual( ph["parameters"]["t"]["hours"].minValue(), 0 )
		self.assertEqual( ph["parameters"]["t"]["hours"].maxValue(), 23 )
		self.assertEqual( ph["parameters"]["t"]["hours"].defaultValue(), 10 )
		self.assertEqual( ph["parameters"]["t"]["hours"].getValue(), 10 )

		self.failUnless( isinstance( ph["parameters"]["t"]["minutes"], Gaffer.IntPlug ) )
		self.assertEqual( ph["parameters"]["t"]["minutes"].minValue(), 0 )
		self.assertEqual( ph["parameters"]["t"]["minutes"].maxValue(), 59 )
		self.assertEqual( ph["parameters"]["t"]["minutes"].defaultValue(), 15 )
		self.assertEqual( ph["parameters"]["t"]["minutes"].getValue(), 15 )
				
		self.failUnless( isinstance( ph["parameters"]["t"]["seconds"], Gaffer.IntPlug ) )
		self.assertEqual( ph["parameters"]["t"]["seconds"].minValue(), 0 )
		self.assertEqual( ph["parameters"]["t"]["seconds"].maxValue(), 59 )
		self.assertEqual( ph["parameters"]["t"]["seconds"].defaultValue(), 1 )
		self.assertEqual( ph["parameters"]["t"]["seconds"].getValue(), 1 )

		self.failUnless( isinstance( ph["parameters"]["t"]["frame"], Gaffer.IntPlug ) )
		self.assertEqual( ph["parameters"]["t"]["frame"].minValue(), 0 )
		self.assertEqual( ph["parameters"]["t"]["frame"].maxValue(), 29 )
		self.assertEqual( ph["parameters"]["t"]["frame"].defaultValue(), 12 )
		self.assertEqual( ph["parameters"]["t"]["frame"].getValue(), 12 )
		
		ph["parameters"]["t"]["hours"].setValue( 11 )
		ph["parameters"]["t"]["minutes"].setValue( 10 )
		ph["parameters"]["t"]["seconds"].setValue( 2 )
		ph["parameters"]["t"]["frame"].setValue( 20 )
		
		ph.parameterHandler().setParameterValue()
		
		tc = p["t"].getTypedValue()
		self.assertEqual( tc.hours(), 11 )
		self.assertEqual( tc.minutes(), 10 )
		self.assertEqual( tc.seconds(), 2 )
		self.assertEqual( tc.frame(), 20 )

		with ph.parameterModificationContext() :
		
			tc.setHours( 1 )
			tc.setMinutes( 2 )
			tc.setSeconds( 3 )
			tc.setFrame( 4 )
			p["t"].setTypedValue( tc )
		
		self.assertEqual( ph["parameters"]["t"]["hours"].getValue(), 1 )
		self.assertEqual( ph["parameters"]["t"]["minutes"].getValue(), 2 )
		self.assertEqual( ph["parameters"]["t"]["seconds"].getValue(), 3 )
		self.assertEqual( ph["parameters"]["t"]["frame"].getValue(), 4 )
	
	def testParameterChangedCanChangeValues( self ) :
	
		class ParameterChanger( IECore.Parameterised ) :
		
			def __init__( self ) :
			
				IECore.Parameterised.__init__( self, "" )
				
				self.parameters().addParameters(
				
					[
					
						IECore.IntParameter(
							name = "driver",
							description = "",
						),
					
						IECore.IntParameter(
							name = "driven",
							description = "",
						),
						
					],
				
				)
				
				self.changes = []
				
			def parameterChanged( self, parameter ) :
			
				self.changes.append( ( parameter, parameter.getNumericValue() ) )
			
				if parameter.isSame( self.parameters()["driver"] ) :
				
					self.parameters()["driven"].setNumericValue( parameter.getNumericValue() * 2 )
		
		c = ParameterChanger()
		
		ph = Gaffer.ParameterisedHolderNode()
		ph.setParameterised( c )
		
		self.assertEqual( ph["parameters"]["driver"].getValue(), 0 )
		self.assertEqual( ph["parameters"]["driven"].getValue(), 0 )
		self.assertEqual( len( c.changes ), 0 )
		
		ph["parameters"]["driver"].setValue( 10 )
		
		self.assertEqual( ph["parameters"]["driver"].getValue(), 10 )
		self.assertEqual( ph["parameters"]["driven"].getValue(), 20 )
		self.assertEqual( len( c.changes ), 1 )
		self.failUnless( c.changes[0][0].isSame( c["driver"] ) )
		self.assertEqual( c.changes[0][1], 10 )
		
		ph["parameters"]["driven"].setValue( 30 )
		
		self.assertEqual( ph["parameters"]["driver"].getValue(), 10 )
		self.assertEqual( ph["parameters"]["driven"].getValue(), 30 )
		self.assertEqual( len( c.changes ), 2 )
		self.failUnless( c.changes[1][0].isSame( c["driven"] ) )
		self.assertEqual( c.changes[1][1], 30 )
	
	def testParameterChangedWithCompoundParameters( self ) :
	
		class ParameterChanger( IECore.Parameterised ) :
		
			def __init__( self ) :
			
				IECore.Parameterised.__init__( self, "" )
				
				self.parameters().addParameters(
				
					[
					
						IECore.IntParameter(
							name = "driver",
							description = "",
						),
					
						IECore.CompoundParameter(
							name = "c",
							members = [
								IECore.IntParameter(
									"i", ""
								),
								IECore.StringParameter(
									"s", "", ""
								),
							]
						),
						
					],
				
				)
				
				self.changes = []
			
			# the mere existence of this function caused the problem this
			# test is checking is fixed.
			def parameterChanged( self, parameter ) :
			
				pass

		c = ParameterChanger()
		
		ph = Gaffer.ParameterisedHolderNode()
		ph.setParameterised( c )

		self.failUnless( "parameters" in ph )
		self.failUnless( "c" in ph["parameters"] )
		self.failUnless( "i" in ph["parameters"]["c"] )
		self.failUnless( "s" in ph["parameters"]["c"] )
	
	def testParameterChangedWithIntermediateClasses( self ) :
	
		class ClassParameterChanger( IECore.Parameterised ) :
		
			def __init__( self ) :
			
				IECore.Parameterised.__init__( self, "" )
				
				self.parameters().addParameters(
				
					[
					
						IECore.IntParameter(
							name = "driver",
							description = "",
						),
					
						IECore.IntParameter(
							name = "driven",
							description = "",
						),
						
						IECore.CompoundParameter(
							name = "c",
							description = "",
							members = [
								
								IECore.IntParameter(
									name = "driver2",
									description = "",
								),
								
								IECore.IntParameter(
									name = "driven2",
									description = "",
								),
								
								IECore.ClassParameter(
									name = "class",
									description = "",
									searchPathEnvVar = "GAFFERTEST_CLASS_PATHS",
								),
								
								IECore.ClassVectorParameter(
									name = "classes",
									description = "",
									searchPathEnvVar = "GAFFERTEST_CLASS_PATHS",
								),
								
							],
						),
						
					],
				
				)
				
				self.changes = []
				
			def parameterChanged( self, parameter ) :
			
				self.changes.append( ( parameter, str( parameter.getValue() ) ) )
							
				if parameter.isSame( self.parameters()["driver"] ) :
				
					self.parameters()["driven"].setNumericValue( parameter.getNumericValue() * 2 )
				
				elif parameter.isSame( self.parameters()["c"]["driver2"] ) :
				
					self.parameters()["c"]["driven2"].setNumericValue( parameter.getNumericValue() * 4 )

		c = ClassParameterChanger()
		
		ph = Gaffer.ParameterisedHolderNode()
		ph.setParameterised( c )
		
		with ph.parameterModificationContext() :
			c["c"]["class"].setClass( "parameterChangedCallback", 1 )
			c["c"]["classes"].setClasses(
				[
					( "p0", "parameterChangedCallback", 1 ),
					( "p1", "parameterChangedCallback", 1 ),
				]
			)
			
		# check that the main class gets callbacks for the parameters it
		# owns directly.
		
		self.assertEqual( ph["parameters"]["driver"].getValue(), 0 )
		self.assertEqual( ph["parameters"]["driven"].getValue(), 0 )
 		self.assertEqual( len( c.changes ), 0 )
 		
 		ph["parameters"]["driver"].setValue( 10 )
 				
 		self.assertEqual( ph["parameters"]["driver"].getValue(), 10 )
 		self.assertEqual( ph["parameters"]["driven"].getValue(), 20 )
 		self.assertEqual( len( c.changes ), 1 )
 		self.failUnless( c.changes[0][0].isSame( c["driver"] ) )
 		self.assertEqual( c.changes[0][1], "10" )
 		
 		ph["parameters"]["driven"].setValue( 30 )
 		
 		self.assertEqual( ph["parameters"]["driver"].getValue(), 10 )
 		self.assertEqual( ph["parameters"]["driven"].getValue(), 30 )
 		self.assertEqual( len( c.changes ), 2 )
 		self.failUnless( c.changes[1][0].isSame( c["driven"] ) )
 		self.assertEqual( c.changes[1][1], "30" )
		
		# check that the main class gets callbacks for the parameters it
		# owns directly via a CompoundParameter.
		
 		self.assertEqual( ph["parameters"]["c"]["driver2"].getValue(), 0 )
 		self.assertEqual( ph["parameters"]["c"]["driven2"].getValue(), 0 )
 		self.assertEqual( len( c.changes ), 2 )
		
 		ph["parameters"]["c"]["driver2"].setValue( 10 )
 		
 		self.assertEqual( ph["parameters"]["c"]["driver2"].getValue(), 10 )
 		self.assertEqual( ph["parameters"]["c"]["driven2"].getValue(), 40 )
 		self.assertEqual( len( c.changes ), 4 )
 		self.failUnless( c.changes[2][0].isSame( c["c"]["driver2"] ) )
 		self.assertEqual( c.changes[2][1], "10" )
 		self.failUnless( c.changes[3][0].isSame( c["c"] ) )
 		
 		ph["parameters"]["c"]["driven2"].setValue( 30 )
 		
 		self.assertEqual( ph["parameters"]["c"]["driver2"].getValue(), 10 )
 		self.assertEqual( ph["parameters"]["c"]["driven2"].getValue(), 30 )
 		self.assertEqual( len( c.changes ), 6 )
 		self.failUnless( c.changes[4][0].isSame( c["c"]["driven2"] ) )
 		self.assertEqual( c.changes[4][1], "30" )
 		self.failUnless( c.changes[5][0].isSame( c["c"] ) )

		# check that parameters changed on the classparameter are passed to
		# the class itself and not the top level parameterised.
		
		c2 = c["c"]["class"].getClass()
		self.assertEqual( len( c2.changes ), 0 )
		
		ph["parameters"]["c"]["class"]["driver"].setValue( 10 )
				
		self.assertEqual( ph["parameters"]["c"]["class"]["driver"].getValue(), 10 )
 		self.assertEqual( ph["parameters"]["c"]["class"]["driven"].getValue(), 50 )
 		
 		self.assertEqual( len( c2.changes ), 1 )
 		self.failUnless( c2.changes[0][0].isSame( c2["driver"] ) )
 		self.assertEqual( c2.changes[0][1], "10" )

		# check that parameters changed on the classvectorparameter are passed to
		# the class itself and not the top level parameterised.
		
		c3 = c["c"]["classes"].getClass( "p0" )
		self.assertEqual( len( c3.changes ), 0 )
		
		ph["parameters"]["c"]["classes"]["p0"]["driver"].setValue( 10 )
				
		self.assertEqual( ph["parameters"]["c"]["classes"]["p0"]["driver"].getValue(), 10 )
 		self.assertEqual( ph["parameters"]["c"]["classes"]["p0"]["driven"].getValue(), 50 )
 		 		
 		self.assertEqual( len( c3.changes ), 2 )
 		self.failUnless( c3.changes[0][0].isSame( c3["driver"] ) )
 		self.assertEqual( c3.changes[0][1], "10" )
 		self.failUnless( c3.changes[1][0].isSame( c["c"]["classes"]["p0"] ) )
 		
 		c4 = c["c"]["classes"].getClass( "p1" )
		self.assertEqual( len( c4.changes ), 0 )
		
		ph["parameters"]["c"]["classes"]["p1"]["driver"].setValue( 10 )
				
		self.assertEqual( ph["parameters"]["c"]["classes"]["p1"]["driver"].getValue(), 10 )
 		self.assertEqual( ph["parameters"]["c"]["classes"]["p1"]["driven"].getValue(), 50 )
 		 		
 		self.assertEqual( len( c4.changes ), 2 )
 		self.failUnless( c4.changes[0][0].isSame( c4["driver"] ) )
 		self.assertEqual( c4.changes[0][1], "10" )
 		self.failUnless( c4.changes[1][0].isSame( c["c"]["classes"]["p1"] ) )
 	
	def testReadOnly( self ) :
		
		p = IECore.Parameterised( "" )
		
		p.parameters().addParameters(
		
			[
				IECore.IntParameter(
					"i",
					"",
					1,
				)
			]
		
		)
		
		ph = Gaffer.ParameterisedHolderNode()
		ph.setParameterised( p )

		self.failUnless( "parameters" in ph )
		self.failUnless( "i" in ph["parameters"] )
		self.assertEqual( ph["parameters"]["i"].getValue(), 1 )
		self.assertEqual( ph["parameters"]["i"].getFlags( Gaffer.Plug.Flags.ReadOnly ), False )
		
		with ph.parameterModificationContext() :
		
			p.parameters()["i"].userData()["gaffer"] = IECore.CompoundObject( {
				"readOnly" : IECore.BoolData( True ),
			} )
			p.parameters()["i"].setNumericValue( 2 )
		
		self.assertEqual( ph["parameters"]["i"].getFlags( Gaffer.Plug.Flags.ReadOnly ), True )
		# the plug was made read only, so should not have accepted the new parameter value
		self.assertEqual( ph["parameters"]["i"].getValue(), 1 )
		
	def testExceptionInParameterChanged( self ) :

		class ParameterChangedRaiser( IECore.Parameterised ) :

			def __init__( self ) :

				IECore.Parameterised.__init__( self, "" )

				self.parameters().addParameters(

					[

						IECore.IntParameter(
							name = "driver",
							description = "",
						),

					],

				)

				self.changes = []

			def parameterChanged( self, parameter ) :

				raise RuntimeError( "Ooops!" )

		c = ParameterChangedRaiser()

		ph = Gaffer.ParameterisedHolderNode()
		ph.setParameterised( c )

		self.assertRaises( RuntimeError, ph["parameters"]["driver"].setValue, 10 )

	def testParameterInvalidWhenParameterChangedRaises( self ) :
	
		class InvalidValueRaiser( IECore.Parameterised ) :

			def __init__( self ) :

				IECore.Parameterised.__init__( self, "" )

				self.parameters().addParameters(

					[

						IECore.IntParameter(
							name = "driver",
							description = "",
							defaultValue = 0,
						),

					],

				)

				self.changes = []

			def parameterChanged( self, parameter ) :

				# this puts the parameter in a state where its value
				# is not valid.
				parameter.setValue( IECore.StringData( "oh dear" ) )
				# then when we raise here, a further exception will
				# occur when the invalid parameter value is discovered
				# during the application of parameter changes to the plugs.
				raise RuntimeError( "Ooops!" )
				
		c = InvalidValueRaiser()

		ph = Gaffer.ParameterisedHolderNode()
		ph.setParameterised( c )
		
		self.assertRaises( RuntimeError, ph["parameters"]["driver"].setValue, 1 )

	def setUp( self ) :
	
		os.environ["GAFFERTEST_CLASS_PATHS"] = os.path.dirname( __file__ ) + "/classes"
					
if __name__ == "__main__":
	unittest.main()
	
