##########################################################################
#
#  Copyright (c) 2018, John Haddon. All rights reserved.
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

import imath

import IECore
import IECoreScene

import GafferScene
import GafferSceneTest

class DeleteObjectTest( GafferSceneTest.SceneTestCase ) :

	def test( self ) :

		plane = GafferScene.Plane()

		# Node should do nothing without a filter applied.

		deleteObject = GafferScene.DeleteObject()
		deleteObject["in"].setInput( plane["out"] )

		self.assertScenesEqual( plane["out"], deleteObject["out"] )
		self.assertSceneHashesEqual( plane["out"], deleteObject["out"] )

		# Applying a filter should kick it into action.

		f = GafferScene.PathFilter()
		f["paths"].setValue( IECore.StringVectorData( [ "/plane" ] ) )
		deleteObject["filter"].setInput( f["out"] )

		self.assertEqual( deleteObject["out"].object( "/plane" ), IECore.NullObject() )

		# Bounds should be unchanged unless we ask for them to be adjusted

		self.assertScenesEqual( plane["out"], deleteObject["out"], checks = self.allSceneChecks - { "object" } )
		self.assertSceneHashesEqual( plane["out"], deleteObject["out"], checks = self.allSceneChecks - { "object" } )

		deleteObject["adjustBounds"].setValue( True )

		self.assertEqual( deleteObject["out"].bound( "/" ), imath.Box3f() )
		self.assertEqual( deleteObject["out"].bound( "/plane" ), imath.Box3f() )

		self.assertScenesEqual( plane["out"], deleteObject["out"], checks = self.allSceneChecks - { "object", "bound" } )
		self.assertSceneHashesEqual( plane["out"], deleteObject["out"], checks = self.allSceneChecks - { "object", "bound" } )

if __name__ == "__main__":
	unittest.main()
