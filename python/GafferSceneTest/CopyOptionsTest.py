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

import IECore

import Gaffer
import GafferTest
import GafferScene
import GafferSceneTest


class CopyOptionsTest( GafferSceneTest.SceneTestCase ) :

	def test( self ) :

		plane = GafferScene.Plane()

		options = GafferScene.CustomOptions()
		options["in"].setInput( plane["out"] )

		deleteOptions = GafferScene.DeleteOptions()
		deleteOptions["in"].setInput( options["out"] )

		copyOptions = GafferScene.CopyOptions()
		copyOptions["in"].setInput( deleteOptions["out"] )
		copyOptions["source"].setInput( options["out"] )

		# set up some options that we can delete and copy
		options["options"].addChild( Gaffer.NameValuePlug( "test1", 1 ) )
		options["options"].addChild( Gaffer.NameValuePlug( "test2", 2 ) )
		options["options"].addChild( Gaffer.NameValuePlug( "test3", 3 ) )

		# verify result
		g = deleteOptions["out"]["globals"].getValue()
		self.assertEqual( g["option:test1"], IECore.IntData( 1 ) )
		self.assertEqual( g["option:test2"], IECore.IntData( 2 ) )
		self.assertEqual( g["option:test3"], IECore.IntData( 3 ) )

		# delete options
		deleteOptions["names"].setValue( "test*" )

		# verify result
		g = deleteOptions["out"]["globals"].getValue()
		self.assertFalse( "option:test1" in g )
		self.assertFalse( "option:test2" in g )
		self.assertFalse( "option:test3" in g )

		# copy options
		copyOptions["options"].setValue( "test*" )

		# verify result
		g = copyOptions["out"]["globals"].getValue()
		self.assertEqual( g["option:test1"], IECore.IntData( 1 ) )
		self.assertEqual( g["option:test2"], IECore.IntData( 2 ) )
		self.assertEqual( g["option:test3"], IECore.IntData( 3 ) )

		# test dirty propagation
		cs = GafferTest.CapturingSlot( copyOptions.plugDirtiedSignal() )

		copyOptions["options"].setValue( "" )
		self.assertTrue( copyOptions["out"]["globals"] in set( e[0] for e in cs ) )
