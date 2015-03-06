##########################################################################
#
#  Copyright (c) 2015, Image Engine Design Inc. All rights reserved.
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
import GafferScene
import GafferSceneTest

class FilterSwitchTest( GafferSceneTest.SceneTestCase ) :

	def testConstruct( self ) :

		f = GafferScene.FilterSwitch()
		self.assertEqual( f.getName(), "FilterSwitch" )

	def testSwitch( self ) :

		# Build a scene with a sphere, a plane, and
		# a filter switch controlling an attribute
		# assignment. Index 0 should assign to the
		# plane and index 1 should assign to the
		# sphere.

		script = Gaffer.ScriptNode()

		script["plane"] = GafferScene.Plane()
		script["sphere"] = GafferScene.Sphere()
		script["group"] = GafferScene.Group()
		script["group"]["in"].setInput( script["plane"]["out"] )
		script["group"]["in1"].setInput( script["sphere"]["out"] )

		script["planeSet"] = GafferScene.Set()
		script["planeSet"]["paths"].setValue( IECore.StringVectorData( [ "/group/plane" ] ) )
		script["planeSet"]["in"].setInput( script["group"]["out"] )

		script["attributes"] = GafferScene.StandardAttributes()
		script["attributes"]["attributes"]["visibility"]["enabled"].setValue( True )
		script["attributes"]["in"].setInput( script["planeSet"]["out"] )

		script["setFilter"] = GafferScene.SetFilter()
		script["setFilter"]["set"].setValue( "set" )

		script["pathFilter"] = GafferScene.PathFilter()
		script["pathFilter"]["paths"].setValue( IECore.StringVectorData( [ "/group/sphere" ] ) )

		script["switchFilter"] = GafferScene.FilterSwitch()
		script["switchFilter"]["in"].setInput( script["setFilter"]["out"] )
		script["switchFilter"]["in1"].setInput( script["pathFilter"]["out"] )

		script["attributes"]["filter"].setInput( script["switchFilter"]["out"] )

		# Check that we get the assignments we expect for each index.

		self.assertEqual( len( script["attributes"]["out"].attributes( "/group/plane" ) ), 1 )
		self.assertEqual( len( script["attributes"]["out"].attributes( "/group/sphere" ) ), 0 )

		script["switchFilter"]["index"].setValue( 1 )

		self.assertEqual( len( script["attributes"]["out"].attributes( "/group/plane" ) ), 0 )
		self.assertEqual( len( script["attributes"]["out"].attributes( "/group/sphere" ) ), 1 )

		# Check that we get dirtiness signalled when changing the
		# index.

		cs = GafferTest.CapturingSlot( script["attributes"].plugDirtiedSignal() )
		self.assertEqual( len( cs ), 0 )

		script["switchFilter"]["index"].setValue( 0 )
		self.assertTrue( script["attributes"]["out"] in [ c[0] for c in cs ] )

		# Check that we get dirtiness signalled for the attributes
		# when changing the set used by the set filter.

		del cs[:]
		script["planeSet"]["paths"].setValue( IECore.StringVectorData( [ "/group", "/group/plane" ] ) )
		self.assertTrue( script["attributes"]["out"]["attributes"] in [ c[0] for c in cs ] )

		# But also check that we don't get it signalled unnecessarily when
		# the set filter isn't the current index.

		script["switchFilter"]["index"].setValue( 1 )
		del cs[:]
		script["planeSet"]["paths"].setValue( IECore.StringVectorData( [ "/group/plane" ] ) )
		self.assertFalse( script["attributes"]["out"]["attributes"] in [ c[0] for c in cs ] )

		# Now check that we can use expressions successfully on the index.

		script["expression"] = Gaffer.Expression()
		script["expression"]["engine"].setValue( "python" )
		script["expression"]["expression"].setValue( 'parent["switchFilter"]["index"] = int( context.getFrame() )' )

		with script.context() :

			script.context().setFrame( 0 )
			self.assertEqual( len( script["attributes"]["out"].attributes( "/group/plane" ) ), 1 )
			self.assertEqual( len( script["attributes"]["out"].attributes( "/group/sphere" ) ), 0 )

			script.context().setFrame( 1 )
			self.assertEqual( len( script["attributes"]["out"].attributes( "/group/plane" ) ), 0 )
			self.assertEqual( len( script["attributes"]["out"].attributes( "/group/sphere" ) ), 1 )

		# Now we have an expression based on the context, changing the upstream set should
		# always signal dirtiness for the attributes, because we don't know which index
		# the switch will use until we actually compute.

		del cs[:]
		script["planeSet"]["paths"].setValue( IECore.StringVectorData( [ "/group", "/group/plane" ] ) )
		self.assertTrue( script["attributes"]["out"]["attributes"] in [ c[0] for c in cs ] )

if __name__ == "__main__":
	unittest.main()
