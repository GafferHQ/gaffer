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
import inspect
import imath

import IECore

import Gaffer
import GafferTest
import GafferImage
import GafferImageTest

class ImageLoopTest( GafferImageTest.ImageTestCase ) :

	def testLoop( self ) :

		script = Gaffer.ScriptNode()

		script["c"] = GafferImage.Constant()
		script["loop"] = Gaffer.Loop()
		script["loop"].setup( GafferImage.ImagePlug() )
		script["loop"]["in"].setInput( script["c"]["out"] )

		script["grade"] = GafferImage.Grade()
		script["grade"]["offset"].setValue( imath.Color4f( .1 ) )
		script["grade"]["in"].setInput( script["loop"]["previous"] )
		script["loop"]["next"].setInput( script["grade"]["out"] )

		script["sampler"] = GafferImage.ImageSampler()
		script["sampler"]["pixel"].setValue( imath.V2f( 10 ) )
		script["sampler"]["image"].setInput( script["loop"]["out"] )

		with script.context() :

			script["loop"]["iterations"].setValue( 2 )
			self.assertAlmostEqual( script["sampler"]["color"]["r"].getValue(), .2 )

			script["loop"]["iterations"].setValue( 4 )
			self.assertAlmostEqual( script["sampler"]["color"]["r"].getValue(), .4 )

		script2 = Gaffer.ScriptNode()
		script2.execute( script.serialise() )

		with script2.context() :

			script2["loop"]["iterations"].setValue( 3 )
			self.assertAlmostEqual( script2["sampler"]["color"]["r"].getValue(), .3 )

			script2["loop"]["iterations"].setValue( 5 )
			self.assertAlmostEqual( script2["sampler"]["color"]["r"].getValue(), .5 )

	def testIterationsContext( self ) :

		script = Gaffer.ScriptNode()

		script["c"] = GafferImage.Constant()
		script["loop"] = Gaffer.Loop()
		script["loop"].setup( GafferImage.ImagePlug() )
		script["loop"]["in"].setInput( script["c"]["out"] )

		script["grade"] = GafferImage.Grade()
		script["grade"]["offset"].setValue( imath.Color4f( .1 ) )
		script["grade"]["in"].setInput( script["loop"]["previous"] )
		script["loop"]["next"].setInput( script["grade"]["out"] )

		script["sampler"] = GafferImage.ImageSampler()
		script["sampler"]["pixel"].setValue( imath.V2f( 10 ) )
		script["sampler"]["image"].setInput( script["loop"]["out"] )

		script["expression"] = Gaffer.Expression()
		script["expression"].setExpression( inspect.cleandoc(
			"""
			assert( context.get( "image:channelName", None ) is None )
			assert( context.get( "image:tileOrigin", None ) is None )
			parent["loop"]["iterations"] = 4
			"""
		) )

		with script.context() :

			self.assertAlmostEqual( script["sampler"]["color"]["r"].getValue(), .4 )

if __name__ == "__main__":
	unittest.main()
