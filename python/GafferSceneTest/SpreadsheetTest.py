##########################################################################
#
#  Copyright (c) 2019, Image Engine Design Inc. All rights reserved.
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
import GafferScene
import GafferSceneTest

class SpreadsheetTest( GafferSceneTest.SceneTestCase ) :

	def testScenePathAsSelector( self ) :

		sphere = GafferScene.Sphere()
		cube = GafferScene.Cube()

		group = GafferScene.Group()
		group["in"][0].setInput( sphere["out"] )
		group["in"][1].setInput( cube["out"] )

		pathFilter = GafferScene.PathFilter()
		pathFilter["paths"].setValue( IECore.StringVectorData( [ "/group/sphere", "/group/cube" ] ) )

		attributes = GafferScene.StandardAttributes()
		attributes["in"].setInput( group["out"] )
		attributes["filter"].setInput( pathFilter["out"] )
		attributes["attributes"]["deformationBlur"]["enabled"].setValue( True )

		spreadsheet = Gaffer.Spreadsheet()
		spreadsheet["selector"].setValue( "${scene:path}" )
		spreadsheet["rows"].addColumn( attributes["attributes"]["deformationBlur"]["value"] )
		attributes["attributes"]["deformationBlur"]["value"].setInput( spreadsheet["out"][0] )

		row = spreadsheet["rows"].addRow()
		row["name"].setValue( "/group/cube" )
		row["cells"][0]["value"].setValue( False )

		self.assertEqual( attributes["out"].attributes( "/group/sphere" )["gaffer:deformationBlur"].value, True )
		self.assertEqual( attributes["out"].attributes( "/group/cube" )["gaffer:deformationBlur"].value, False )

if __name__ == "__main__":
	unittest.main()
