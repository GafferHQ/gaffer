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

import unittest

import Gaffer
import GafferScene
import GafferSceneTest

class FilterTest( GafferSceneTest.SceneTestCase ) :

	def testInputScene( self ) :

		c = Gaffer.Context()

		self.assertEqual( GafferScene.Filter.getInputScene( c ), None )

		p = GafferScene.Plane()
		GafferScene.Filter.setInputScene( c, p["out"] )
		self.assertEqual( GafferScene.Filter.getInputScene( c ), p["out"] )

	def testEnabledPlugContextSanitisation( self ) :

		# Make a graph where `pathFilter.enabled` reads from the
		# scene globals.
		plane = GafferScene.Plane()

		optionQuery = GafferScene.OptionQuery()
		optionQuery["scene"].setInput( plane["out"] )
		query = optionQuery.addQuery( Gaffer.BoolPlug(), "test" )

		pathFilter = GafferScene.PathFilter()
		pathFilter["enabled"] .setInput( optionQuery.outPlugFromQuery( query )["value"] )

		attributes = GafferScene.StandardAttributes()
		attributes["in"].setInput( plane["out"] )
		attributes["filter"].setInput( pathFilter["out"] )

		# Trigger an evaluation of the filter. We don't need to assert anything
		# here, because all tests run with a ContextSanitiser active, and that
		# will cause a failure if the filter leaks a context variable like
		# `scene:path` into the evaluation of the scene globals.
		attributes["out"].attributes( "/plane" )

if __name__ == "__main__":
	unittest.main()
