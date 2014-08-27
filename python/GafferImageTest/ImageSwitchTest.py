##########################################################################
#
#  Copyright (c) 2013, Image Engine Design Inc. All rights reserved.
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
import GafferImage
import GafferSceneTest

class ImageSwitchTest( GafferTest.TestCase ) :

	def testDefaultName( self ) :

		s = GafferImage.ImageSwitch()
		self.assertEqual( s.getName(), "ImageSwitch" )

	def testEnabledPlug( self ) :

		s = GafferImage.ImageSwitch()
		self.assertTrue( isinstance( s["enabled"], Gaffer.BoolPlug ) )
		self.assertTrue( s["enabled"].isSame( s.enabledPlug() ) )
		self.assertFalse( "enabled1" in s )

	def testAffects( self ) :

		in0 = GafferImage.Constant()
		in1 = GafferImage.Constant()

		switch = GafferImage.ImageSwitch()
		switch["in"].setInput( in0["out"] )
		switch["in1"].setInput( in1["out"] )

		for p in [ switch["in"], switch["in1"] ] :
			for n in [ "format", "dataWindow", "channelNames", "channelData" ] :
				a = switch.affects( p[n] )
				self.assertEqual( len( a ), 1 )
				self.assertTrue( a[0].isSame( switch["out"][n] ) )

		a = set( [ plug.relativeName( plug.node() ) for plug in switch.affects( switch["enabled"] ) ] )
		self.assertEqual(
			a,
			set( [
				"out.format", "out.dataWindow", "out.channelNames", "out.channelData",
			] ),
		)

		a = set( [ plug.relativeName( plug.node() ) for plug in switch.affects( switch["index"] ) ] )
		self.assertEqual(
			a,
			set( [
				"out.format", "out.dataWindow", "out.channelNames", "out.channelData",
			] ),
		)

	def testSwitching( self ) :

		in0 = GafferImage.Constant()
		in0["format"].setValue( GafferImage.Format( 100, 100, 1.0 ) )
		in0["color"].setValue( IECore.Color4f( 1, 0, 0, 1 ) )
		in1 = GafferImage.Constant()
		in1["format"].setValue( GafferImage.Format( 100, 100, 1.0 ) )
		in0["color"].setValue( IECore.Color4f( 0, 1, 0, 1 ) )

		switch = GafferImage.ImageSwitch()
		switch["in"].setInput( in0["out"] )
		switch["in1"].setInput( in1["out"] )

		self.assertEqual( switch["out"].imageHash(), in0["out"].imageHash() )
		self.assertEqual( switch["out"].image(), in0["out"].image() )

		switch["index"].setValue( 1 )

		self.assertEqual( switch["out"].imageHash(), in1["out"].imageHash() )
		self.assertEqual( switch["out"].image(), in1["out"].image() )

		switch["enabled"].setValue( False )

		self.assertEqual( switch["out"].imageHash(), in0["out"].imageHash() )
		self.assertEqual( switch["out"].image(), in0["out"].image() )

	def testSerialisation( self ) :

		script = Gaffer.ScriptNode()

		script["switch"] = GafferImage.ImageSwitch()
		script["in0"] = GafferImage.Constant()
		script["in1"] = GafferImage.Constant()

		script["switch"]["in"].setInput( script["in0"]["out"] )
		script["switch"]["in1"].setInput( script["in1"]["out"] )

		script2 = Gaffer.ScriptNode()
		script2.execute( script.serialise() )

		self.assertTrue( script2["switch"]["in"].getInput().isSame( script2["in0"]["out"] ) )
		self.assertTrue( script2["switch"]["in1"].getInput().isSame( script2["in1"]["out"] ) )
		self.assertTrue( script2["switch"]["in2"].getInput() is None )

if __name__ == "__main__":
	unittest.main()
