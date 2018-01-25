##########################################################################
#
#  Copyright (c) 2016, Scene Engine Design Inc. All rights reserved.
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

import GafferScene
import GafferSceneTest

class FilteredSceneProcessorTest( GafferSceneTest.SceneTestCase ) :

	def testDerivingInPython( self ) :

		# We allow deriving in Python for use as a "shell" node containing
		# an internal node network which provides the implementation. But
		# we don't allow the overriding of the compute*() and hash*() methods
		# because the performance would be abysmal.

		class ShaderAndAttributes( GafferScene.FilteredSceneProcessor ) :

			def __init__( self, name = "ShaderAndAttributes" ) :

				GafferScene.FilteredSceneProcessor.__init__( self, name, filterDefault = IECore.PathMatcher.Result.NoMatch )

				self["__shader"] = GafferSceneTest.TestShader()
				self["__shader"]["type"].setValue( "test:surface" )

				self["__shaderAssignment"] = GafferScene.ShaderAssignment()
				self["__shaderAssignment"]["in"].setInput( self["in"] )
				self["__shaderAssignment"]["shader"].setInput( self["__shader"]["out"] )
				self["__shaderAssignment"]["filter"].setInput( self["filter"] )
				self["__shaderAssignment"]["enabled"].setInput( self["enabled"] )

				self["__attributes"] = GafferScene.StandardAttributes()
				self["__attributes"]["in"].setInput( self["__shaderAssignment"]["out"] )
				self["__attributes"]["enabled"].setInput( self["enabled"] )
				self["__attributes"]["filter"].setInput( self["filter"] )
				self["__attributes"]["attributes"]["doubleSided"]["enabled"].setValue( True )
				self["__attributes"]["attributes"]["doubleSided"]["value"].setValue( True )

				self["out"].setInput( self["__attributes"]["out"] )

		IECore.registerRunTimeTyped( ShaderAndAttributes )

		p = GafferScene.Plane()
		s = ShaderAndAttributes()
		s["in"].setInput( p["out"] )

		self.assertEqual( s["out"].attributes( "/plane" ).keys(), [] )

		f = GafferScene.PathFilter()
		f["paths"].setValue( IECore.StringVectorData( [ "/plane" ] ) )
		s["filter"].setInput( f["out"] )
		self.assertEqual( set( s["out"].attributes( "/plane" ).keys() ), { "test:surface", "doubleSided" } )

		s["enabled"].setValue( False )
		self.assertEqual( s["out"].attributes( "/plane" ).keys(), [] )

if __name__ == "__main__":
	unittest.main()
