##########################################################################
#
#  Copyright (c) 2014, Image Engine Design Inc. All rights reserved.
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
import GafferUI
import GafferUITest
import GafferScene
import GafferSceneUI

class SceneGadgetTest( GafferUITest.TestCase ) :

	def testBound( self ) :

		s = Gaffer.ScriptNode()
		s["p"] = GafferScene.Plane()
		s["g"] = GafferScene.Group()
		s["g"]["in"].setInput( s["p"]["out"] )
		s["g"]["transform"]["translate"]["x"].setValue( 2 )

		sg = GafferSceneUI.SceneGadget()
		sg.setScene( s["g"]["out"] )

		self.assertEqual( sg.bound(), s["g"]["out"].bound( "/" ) )

		s["g"]["transform"]["translate"]["y"].setValue( 4 )
		self.assertEqual( sg.bound(), s["g"]["out"].bound( "/" ) )

	def assertObjectAt( self, gadget, ndcPosition, path ) :

		viewportGadget = gadget.ancestor( GafferUI.ViewportGadget )

		rasterPosition = ndcPosition * IECore.V2f( viewportGadget.getViewport() )
		gadgetLine = viewportGadget.rasterToGadgetSpace( rasterPosition, gadget )

		self.assertEqual( gadget.objectAt( gadgetLine ), path )

	def assertObjectsAt( self, gadget, ndcBox, paths ) :

		viewportGadget = gadget.ancestor( GafferUI.ViewportGadget )

		rasterMin = ndcBox.min * IECore.V2f( viewportGadget.getViewport() )
		rasterMax = ndcBox.max * IECore.V2f( viewportGadget.getViewport() )

		gadgetMin = viewportGadget.rasterToGadgetSpace( rasterMin, gadget ).p0
		gadgetMax = viewportGadget.rasterToGadgetSpace( rasterMax, gadget ).p1

		objectsAt = GafferScene.PathMatcher()
		gadget.objectsAt( gadgetMin, gadgetMax, objectsAt )

		objects = set( objectsAt.paths() )
		expectedObjects = set( GafferScene.PathMatcher( paths ).paths() )
		self.assertEqual( objects, expectedObjects )

	def testObjectVisibility( self ) :

		s = Gaffer.ScriptNode()
		s["s"] = GafferScene.Sphere()
		s["g"] = GafferScene.Group()
		s["g"]["in"].setInput( s["s"]["out"] )
		s["a"] = GafferScene.StandardAttributes()
		s["a"]["in"].setInput( s["g"]["out"] )

		sg = GafferSceneUI.SceneGadget()
		sg.setMinimumExpansionDepth( 1 )
		sg.setScene( s["a"]["out"] )

		with GafferUI.Window() as w :
			gw = GafferUI.GadgetWidget( sg )

		w.setVisible( True )
		self.waitForIdle( 1000 )

		gw.getViewportGadget().frame( sg.bound() )

		self.assertObjectAt( sg, IECore.V2f( 0.5 ), IECore.InternedStringVectorData( [ "group", "sphere" ] ) )

		s["a"]["attributes"]["visibility"]["enabled"].setValue( True )
		s["a"]["attributes"]["visibility"]["value"].setValue( False )

		self.assertObjectAt( sg, IECore.V2f( 0.5 ), None )

		s["a"]["attributes"]["visibility"]["enabled"].setValue( True )
		s["a"]["attributes"]["visibility"]["value"].setValue( True )

		self.assertObjectAt( sg, IECore.V2f( 0.5 ), IECore.InternedStringVectorData( [ "group", "sphere" ] ) )

	def testExpansion( self ) :

		s = Gaffer.ScriptNode()
		s["s"] = GafferScene.Sphere()
		s["g"] = GafferScene.Group()
		s["g"]["in"].setInput( s["s"]["out"] )
		s["a"] = GafferScene.StandardAttributes()
		s["a"]["in"].setInput( s["g"]["out"] )

		sg = GafferSceneUI.SceneGadget()
		sg.setScene( s["a"]["out"] )

		with GafferUI.Window() as w :
			gw = GafferUI.GadgetWidget( sg )

		w.setVisible( True )
		self.waitForIdle( 1000 )

		gw.getViewportGadget().frame( sg.bound() )

		self.assertObjectAt( sg, IECore.V2f( 0.5 ), None )
		self.assertObjectsAt( sg, IECore.Box2f( IECore.V2f( 0 ), IECore.V2f( 1 ) ), [ "/group" ] )

		sg.setExpandedPaths( GafferScene.PathMatcherData( GafferScene.PathMatcher( [ "/group" ] ) ) )

		self.assertObjectAt( sg, IECore.V2f( 0.5 ), IECore.InternedStringVectorData( [ "group", "sphere" ] ) )
		self.assertObjectsAt( sg, IECore.Box2f( IECore.V2f( 0 ), IECore.V2f( 1 ) ), [ "/group/sphere" ] )

		sg.setExpandedPaths( GafferScene.PathMatcherData( GafferScene.PathMatcher( [] ) ) )

		self.assertObjectAt( sg, IECore.V2f( 0.5 ), None )
		self.assertObjectsAt( sg, IECore.Box2f( IECore.V2f( 0 ), IECore.V2f( 1 ) ), [ "/group" ] )

if __name__ == "__main__":
	unittest.main()
