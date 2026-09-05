##########################################################################
#
#  Copyright (c) 2026, Pascal Andre. All rights reserved.
#
#  Redistribution and use in source and binary forms, with or without
#  modification, are permitted provided that the following conditions are
#  met:
#
#      * Redistributions of source code must retain the above
#        copyright notice, this list of conditions and the following
#        disclaimer.
#      * Redistributions in binary form must reproduce the above
#        copyright notice, this list of conditions and the following
#        disclaimer in the documentation and/or other materials provided with
#        the distribution.
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
#  PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS;
#  OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
#  WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR
#  OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF
#  ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
##########################################################################

import sys
import unittest
import unittest.mock

import GafferUI
import GafferUITest

from Qt import QtGui


class ShowURLTest( GafferUITest.TestCase ) :

	def testWebURL( self ) :

		with unittest.mock.patch.object( QtGui.QDesktopServices, "openUrl" ) as openURL :
			GafferUI.showURL( "https://www.gafferhq.org" )

		openURL.assert_called_once()
		self.assertEqual( openURL.call_args[0][0].toString(), "https://www.gafferhq.org" )

	@unittest.skipUnless( sys.platform == "win32", "Windows-specific URL handling" )
	def testLocalFileURL( self ) :

		path = "C:/Program Files/Gaffer/doc/gaffer/html/index.html"
		with unittest.mock.patch.object( QtGui.QDesktopServices, "openUrl" ) as openURL :
			GafferUI.showURL( "file://" + path + "#section" )

		openURL.assert_called_once()
		url = openURL.call_args[0][0]
		self.assertTrue( url.isLocalFile() )
		self.assertEqual( url.toLocalFile().replace( "\\", "/" ), path )
