##########################################################################
#
#  Copyright (c) 2022, Cinesite VFX Inc. All rights reserved.
#
#  Redistribution and use in source and binary forms, with or without
#  modification, are permitted provided that the following conditions are
#  met:
#
#	  * Redistributions of source code must retain the above
#		copyright notice, this list of conditions and the following
#		disclaimer.
#
#	  * Redistributions in binary form must reproduce the above
#		copyright notice, this list of conditions and the following
#		disclaimer in the documentation and/or other materials provided with
#		the distribution.
#
#	  * Neither the name of John Haddon nor the names of
#		any other contributors to this software may be used to endorse or
#		promote products derived from this software without specific prior
#		written permission.
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

import os
import unittest
import sys
if os.name == 'posix' and sys.version_info[0] < 3:
	import subprocess32 as subprocess
else:
	import subprocess
import imath

import IECore

import Gaffer
import GafferTest
import GafferImage
import GafferImageTest

class LookTransformTest( GafferImageTest.ImageTestCase ) :

	fileName = os.path.expandvars( "$GAFFER_ROOT/python/GafferImageTest/images/checker.exr" )
	groundTruth = os.path.expandvars( "$GAFFER_ROOT/python/GafferImageTest/images/checker_ocio_look.exr" )
	ocioConfig = os.path.expandvars( "$GAFFER_ROOT/python/GafferImageTest/openColorIO/context.ocio" )

	def test( self ) :

		n = GafferImage.ImageReader()
		n["fileName"].setValue( self.fileName )

		o = GafferImage.LookTransform()
		o["in"].setInput( n["out"] )

		self.assertImageHashesEqual( n["out"], o["out"] )
		self.assertImagesEqual( n["out"], o["out"] )

		o["look"].setValue( "primary" )

		self.assertRaises( AssertionError, lambda: self.assertImageHashesEqual( n["out"], o["out"] ) )
		self.assertRaises( Exception, lambda: self.assertImagesEqual( n["out"], o["out"] ) )

	def testPrimary( self ):

		scriptFileName = self.temporaryDirectory() + "/script.gfr"
		contextImageFile = self.temporaryDirectory() + "/look.#.exr"

		s = Gaffer.ScriptNode()

		s["reader"] =  GafferImage.ImageReader()
		s["reader"]["fileName"].setValue( self.fileName )

		s["lt"] = GafferImage.LookTransform()
		s["lt"]["in"].setInput( s["reader"]["out"] )
		s["lt"]["look"].setValue( "primary" )

		s["writer"] = GafferImage.ImageWriter()
		s["writer"]["fileName"].setValue( contextImageFile )
		s["writer"]["in"].setInput( s["lt"]["out"] )
		s["writer"]["channels"].setValue( "R G B A" )

		s["fileName"].setValue( scriptFileName )
		s.save()

		env = os.environ.copy()
		env["OCIO"] = self.ocioConfig
		env["LUT"] = "srgb.spi1d"
		env["CDL"] = "cineon.spi1d"

		subprocess.check_call(
			" ".join( ["gaffer", "execute", scriptFileName, "-frames", "1"] ),
			shell = True,
			stderr = subprocess.PIPE,
			env = env,
		)

		i = GafferImage.ImageReader()
		i["fileName"].setValue( self.groundTruth )

		o = GafferImage.ImageReader()
		o["fileName"].setValue( contextImageFile )

		expected = i["out"]
		context = o["out"]

		# check against expected output
		self.assertImagesEqual( expected, context, ignoreMetadata = True )

	def testInversePrimary( self ):

		scriptFileName = self.temporaryDirectory() + "/script.gfr"
		contextImageFile = self.temporaryDirectory() + "/look.#.exr"

		s = Gaffer.ScriptNode()

		s["reader"] =  GafferImage.ImageReader()
		s["reader"]["fileName"].setValue( self.groundTruth )

		s["lt"] = GafferImage.LookTransform()
		s["lt"]["in"].setInput( s["reader"]["out"] )
		s["lt"]["look"].setValue( "-primary" )

		s["writer"] = GafferImage.ImageWriter()
		s["writer"]["fileName"].setValue( contextImageFile )
		s["writer"]["in"].setInput( s["lt"]["out"] )
		s["writer"]["channels"].setValue( "R G B A" )

		s["fileName"].setValue( scriptFileName )
		s.save()

		env = os.environ.copy()
		env["OCIO"] = self.ocioConfig
		env["LUT"] = "srgb.spi1d"
		env["CDL"] = "cineon.spi1d"

		subprocess.check_call(
			" ".join( ["gaffer", "execute", scriptFileName, "-frames", "1"] ),
			shell = True,
			stderr = subprocess.PIPE,
			env = env,
		)

		i = GafferImage.ImageReader()
		i["fileName"].setValue( self.fileName )

		o = GafferImage.ImageReader()
		o["fileName"].setValue( contextImageFile )

		expected = i["out"]
		context = o["out"]

		# check against expected output
		self.assertImagesEqual( expected, context, ignoreMetadata = True, maxDifference = 0.001 )

	def testDirectionPrimary( self ):

		scriptFileName = self.temporaryDirectory() + "/script.gfr"
		contextImageFile = self.temporaryDirectory() + "/look.#.exr"

		s = Gaffer.ScriptNode()

		s["reader"] =  GafferImage.ImageReader()
		s["reader"]["fileName"].setValue( self.groundTruth )

		s["lt"] = GafferImage.LookTransform()
		s["lt"]["in"].setInput( s["reader"]["out"] )
		s["lt"]["look"].setValue( "primary" )
		s["lt"]["direction"].setValue( GafferImage.OpenColorIOTransform.Direction.Inverse )

		s["writer"] = GafferImage.ImageWriter()
		s["writer"]["fileName"].setValue( contextImageFile )
		s["writer"]["in"].setInput( s["lt"]["out"] )
		s["writer"]["channels"].setValue( "R G B A" )

		s["fileName"].setValue( scriptFileName )
		s.save()

		env = os.environ.copy()
		env["OCIO"] = self.ocioConfig
		env["LUT"] = "srgb.spi1d"
		env["CDL"] = "cineon.spi1d"

		subprocess.check_call(
			" ".join( ["gaffer", "execute", scriptFileName, "-frames", "1"] ),
			shell = True,
			stderr = subprocess.PIPE,
			env = env,
		)

		i = GafferImage.ImageReader()
		i["fileName"].setValue( self.fileName )

		o = GafferImage.ImageReader()
		o["fileName"].setValue( contextImageFile )

		expected = i["out"]
		context = o["out"]

		# check against expected output
		self.assertImagesEqual( expected, context, ignoreMetadata = True, maxDifference = 0.001 )
