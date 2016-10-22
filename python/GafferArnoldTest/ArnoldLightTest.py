##########################################################################
#
#  Copyright (c) 2016, Image Engine Design Inc. All rights reserved.
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

import arnold

import IECore
import IECoreArnold

import GafferSceneTest
import GafferArnold

class ArnoldLightTest( GafferSceneTest.SceneTestCase ) :

	def testUsesShaders( self ) :

		l = GafferArnold.ArnoldLight()
		l.loadShader( "point_light" )

		n = l["out"].attributes( "/light" )["ai:light"]
		self.assertTrue( isinstance( n, IECore.ObjectVector ) )
		self.assertEqual( len( n ), 1 )
		self.assertTrue( isinstance( n[0], IECore.Shader ) )
		self.assertEqual( n[0].type, "ai:light" )
		self.assertEqual( n[0].name, "point_light" )

	def testLoadAllLightsWithoutWarnings( self ) :

		lightNames = []
		with IECoreArnold.UniverseBlock( writable = False ) :
			it = arnold.AiUniverseGetNodeEntryIterator( arnold.AI_NODE_LIGHT )
			while not arnold.AiNodeEntryIteratorFinished( it ) :
				nodeEntry = arnold.AiNodeEntryIteratorGetNext( it )
				lightNames.append( arnold.AiNodeEntryGetName( nodeEntry ) )

		self.longMessage = True

		for lightName in lightNames :
			with IECore.CapturingMessageHandler() as mh :
				l = GafferArnold.ArnoldLight()
				l.loadShader( lightName )
				self.assertEqual( [ m.message for m in mh.messages ], [], "Error loading %s" % lightName )

	def testShaderInputs( self ) :

		s = GafferArnold.ArnoldShader()
		s.loadShader( "physical_sky" )
		s["parameters"]["intensity"].setValue( 2 )

		l = GafferArnold.ArnoldLight()
		l.loadShader( "skydome_light" )
		l["parameters"]["color"].setInput( s["out"] )

		network = l["out"].attributes( "/light" )["ai:light"]
		self.assertEqual( len( network ), 2 )
		self.assertEqual( network[0].name, "physical_sky" )
		self.assertEqual( network[0].parameters["intensity"].value, 2 )
		self.assertEqual( network[1].parameters["color"].value, "link:" + network[0].parameters["__handle"].value )

		s["parameters"]["intensity"].setValue( 4 )
		network = l["out"].attributes( "/light" )["ai:light"]
		self.assertEqual( network[0].parameters["intensity"].value, 4 )

if __name__ == "__main__":
	unittest.main()
