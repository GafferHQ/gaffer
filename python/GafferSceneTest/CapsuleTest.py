##########################################################################
#
#  Copyright (c) 2017, Image Engine Design Inc. All rights reserved.
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

import inspect
import unittest

import IECore

import Gaffer
import GafferScene
import GafferSceneTest

class CapsuleTest( GafferSceneTest.SceneTestCase ) :

	def test( self ) :

		sphere = GafferScene.Sphere()

		h = IECore.MurmurHash()
		for path in ( "/", "/sphere" ) :
			for method in ( "boundHash", "transformHash", "objectHash", "attributesHash" ) :
				h.append( getattr( sphere["out"], method )( path ) )

		capsule = GafferScene.Capsule(
			sphere["out"],
			"/",
			Gaffer.Context(),
			h,
			sphere["out"].bound( "/" )
		)

		self.assertEqual( capsule.scene(), sphere["out"] )
		self.assertEqual( capsule.root(), "/" )
		self.assertEqual( capsule.bound(), sphere["out"].bound( "/" ) )

		capsuleCopy = capsule.copy()
		self.assertEqual( capsuleCopy.scene(), sphere["out"] )
		self.assertEqual( capsuleCopy.root(), "/" )
		self.assertEqual( capsuleCopy.bound(), sphere["out"].bound( "/" ) )
		self.assertEqual( capsuleCopy.hash(), capsule.hash() )

if __name__ == "__main__":
	unittest.main()
