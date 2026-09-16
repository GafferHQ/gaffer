##########################################################################
#
#  Copyright (c) 2026, Cinesite VFX Ltd. All rights reserved.
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

import imath

import IECore

import Gaffer
import GafferScene
import GafferSceneTest

class PromotePointInstancesTest( GafferSceneTest.SceneTestCase ) :

	class TestNetwork( GafferScene.SceneNode ) :

		def __init__( self, name = "SimpleInstancer" ) :

			GafferScene.SceneNode.__init__( self, name )

			self["plane"] = GafferScene.Plane()

			self["sphere"] = GafferScene.Sphere()
			self["cube"] = GafferScene.Cube()

			self["prototypes"] = GafferScene.Group()
			self["prototypes"]["in"][0].setInput( self["sphere"]["out"] )
			self["prototypes"]["in"][1].setInput( self["cube"]["out"] )

			self["planeFilter"] = GafferScene.PathFilter()
			self["planeFilter"]["paths"].setValue( IECore.StringVectorData( [ "/plane" ] ) )

			self["instancer"] = GafferScene.PointInstancer()
			self["instancer"]["in"].setInput( self["plane"]["out"] )
			self["instancer"]["prototypes"].setInput( self["prototypes"]["out"] )
			self["instancer"]["filter"].setInput( self["planeFilter"]["out"] )
			self["instancer"]["prototypesList"].setValue( IECore.StringVectorData( [ "/group/sphere", "/group/cube" ] ) )
			self["instancer"]["prototypeIndexMode"].setValue( GafferScene.PointInstancer.PrototypeIndexMode.Random )

			self["primitiveVariables"] = GafferScene.PrimitiveVariables()
			self["primitiveVariables"]["in"].setInput( self["instancer"]["out"] )
			self["primitiveVariables"]["filter"].setInput( self["planeFilter"]["out"] )
			self["primitiveVariables"]["primitiveVariables"].addChild(
				Gaffer.NameValuePlug( "invisibleIds", IECore.Int64VectorData( [] ) )
			)
			Gaffer.PlugAlgo.promoteWithName( self["primitiveVariables"]["primitiveVariables"][-1]["value"], name = "invisibleIds" )

			self["promoter"] = GafferScene.PromotePointInstances()
			self["promoter"]["in"].setInput( self["primitiveVariables"]["out"] )
			self["promoter"]["filter"].setInput( self["planeFilter"]["out"] )
			Gaffer.PlugAlgo.promote( self["promoter"]["idList"] )
			Gaffer.PlugAlgo.promote( self["promoter"]["name"] )
			Gaffer.PlugAlgo.promote( self["promoter"]["destination"] )

			self["out"].setInput( self["promoter"]["out"] )

	def testPassThrough( self ) :

		network = self.TestNetwork()
		self.assertScenesEqual( network["promoter"]["out"], network["promoter"]["in"] )

	def testChildNames( self ) :

		network = self.TestNetwork()
		prototypeIndices = network["out"].object( "/plane" ).getPrototypeIndex()

		for id in range( 0, 4 ) :

			network["idList"].setValue( IECore.Int64VectorData( [ id ] ) )
			self.assertEqual( network["out"].childNames( "/" ), IECore.InternedStringVectorData( [ "plane", "promotedInstances" ] ) )
			self.assertEqual( network["out"].childNames( "/promotedInstances" ), IECore.InternedStringVectorData( [ str( id ) ] ) )
			prototype = [ "sphere", "cube" ][prototypeIndices[id]]
			self.assertEqual( network["out"].childNames( f"/promotedInstances/{id}" ), IECore.InternedStringVectorData( [ prototype ] ) )

	def testPromotedIDsAddedToInvisibleIDs( self ) :

		network = self.TestNetwork()
		for id in range( 0, 4 ) :
			network["idList"].setValue( IECore.Int64VectorData( [ id ] ) )
			self.assertEqual( list( network["out"].object( "/plane" ).getInvisibleIDs() ), [ id ] )

	def testTransforms( self ) :

		network = self.TestNetwork()

		for id in range( 0, 4 ) :
			network["idList"].setValue( IECore.Int64VectorData( [ id ] ) )
			self.assertEqual(
				network["out"].transform( f"/promotedInstances/{id}" ),
				imath.M44f().translate(
					network["promoter"]["in"].object( "/plane" )["P"].data[id]
				)
			)

	def testAttributes( self ) :

		network = self.TestNetwork()
		N = network["out"].object( "/plane" )["N"].data
		uv = network["out"].object( "/plane" )["uv"]

		for id in range( 0, 4 ) :

			network["idList"].setValue( IECore.Int64VectorData( [ id ] ) )

			self.assertEqual(
				network["out"].attributes( f"/promotedInstances/{id}" ),
				IECore.CompoundObject( {
					"N" : IECore.V3fData( N[id], IECore.GeometricData.Interpretation.Normal ),
					"uv" : IECore.V2fData( uv.data[uv.indices[id]], IECore.GeometricData.Interpretation.UV ),
				} )
			)

	def testInvisibleIDsTranslatedToSceneVisibility( self ) :

		network = self.TestNetwork()
		invisibleIds = [ 0, 2 ]
		network["invisibleIds"].setValue( IECore.Int64VectorData( invisibleIds ) )
		network["idList"].setValue( IECore.Int64VectorData( [ 0, 1, 2, 3 ] ) )

		for id in range( 0, 4 ) :
			attributes = network["out"].attributes( f"/promotedInstances/{id}" )
			if id in invisibleIds :
				self.assertEqual( attributes["scene:visible"].value, False )
			else :
				self.assertNotIn( "scene:visible", attributes )

	def testNoContextLeaks( self ) :

		network = self.TestNetwork()
		network["idList"].setValue( IECore.Int64VectorData( [ 0, 1, 2, 3 ] ) )

		with Gaffer.ContextMonitor( root = network["prototypes"] ) as monitor :
			GafferSceneTest.traverseScene( network["promoter"]["out"] )

		self.assertEqual(
			set( monitor.combinedStatistics().variableNames() ),
			{ "scene:path", "frame", "framesPerSecond" }
		)
