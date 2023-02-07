##########################################################################
#
#  Copyright (c) 2011-2013, Image Engine Design Inc. All rights reserved.
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

import stat
import unittest
import imath
import pathlib

import IECore
import Gaffer
import GafferTest

class ApplicationRootTest( GafferTest.TestCase ) :

	__defaultPreferencesFile = pathlib.Path( "~/gaffer/startup/testApp/preferences.py" ).expanduser()

	class testApp( Gaffer.Application ) :

		def __init__( self ) :

			Gaffer.Application.__init__( self )

	def testPreferences( self ) :

		application = ApplicationRootTest.testApp()
		applicationRoot = application.root()

		p = applicationRoot["preferences"]
		self.assertIsInstance( p, Gaffer.Preferences )

		p["category1"] = Gaffer.Plug()
		p["category1"]["i"] = Gaffer.IntPlug( defaultValue = 2 )

		p["category2"] = Gaffer.Plug()
		p["category2"]["s"] = Gaffer.StringPlug( defaultValue = "apples" )
		p["category2"]["v"] = Gaffer.V3fPlug( defaultValue = imath.V3f( 1, 0, 0 ) )

		p["category1"]["i"].setValue( 10 )
		p["category2"]["s"].setValue( "oranges" )
		p["category2"]["v"].setValue( imath.V3f( 2, 3, 4 ) )

		self.assertFalse( self.__defaultPreferencesFile.exists() )
		applicationRoot.savePreferences()
		self.assertTrue( self.__defaultPreferencesFile.exists() )

		preferencesFile = self.temporaryDirectory() / "testPreferences.gfr"

		self.assertFalse( preferencesFile.exists() )
		applicationRoot.savePreferences( preferencesFile )
		self.assertTrue( preferencesFile.exists() )

		p["category1"]["i"].setValue( 1 )
		p["category2"]["s"].setValue( "beef" )
		p["category2"]["v"].setValue( imath.V3f( -10 ) )

		executionContext = { "application" : application }
		exec(
			compile( open( preferencesFile, encoding = "utf-8" ).read(), preferencesFile, "exec" ),
			executionContext, executionContext
		)

		self.assertEqual( p["category1"]["i"].getValue(), 10 )
		self.assertEqual( p["category2"]["s"].getValue(), "oranges" )
		self.assertEqual( p["category2"]["v"].getValue(), imath.V3f( 2, 3, 4 ) )

	def testPreferencesPermissionsErrors( self ) :

		a = Gaffer.ApplicationRoot( "testApp" )

		preferencesFile = self.temporaryDirectory() / "testPreferences.gfr"
		a.savePreferences( preferencesFile )
		preferencesFile.chmod( 0 )
		self.assertRaises( RuntimeError, a.savePreferences, preferencesFile )

	def testPreferencesLocation( self ) :

		a = Gaffer.ApplicationRoot( "testApp" )

		self.assertEqual( a.preferencesLocation(), self.__defaultPreferencesFile.parent )
		self.assertTrue( pathlib.Path( a.preferencesLocation() ).is_dir() )

	def testClipboard( self ) :

		a = Gaffer.ApplicationRoot()

		d = []
		def f( app ) :

			self.assertTrue( app.isSame( a ) )
			d.append( app.getClipboardContents() )

		c = a.clipboardContentsChangedSignal().connect( f, scoped = True )

		self.assertEqual( len( d ), 0 )
		self.assertEqual( a.getClipboardContents(), None )

		a.setClipboardContents( IECore.IntData( 10 ) )
		self.assertEqual( len( d ), 1 )
		self.assertEqual( a.getClipboardContents(), IECore.IntData( 10 ) )

		a.setClipboardContents( IECore.IntData( 20 ) )
		self.assertEqual( len( d ), 2 )
		self.assertEqual( a.getClipboardContents(), IECore.IntData( 20 ) )

		a.setClipboardContents( IECore.IntData( 20 ) )
		self.assertEqual( len( d ), 2 )
		self.assertEqual( a.getClipboardContents(), IECore.IntData( 20 ) )

	def testScriptContainer( self ) :

		a = Gaffer.ApplicationRoot()
		self.assertIsInstance( a["scripts"], Gaffer.ScriptContainer )

	def tearDown( self ) :

		GafferTest.TestCase.tearDown( self )

		if self.__defaultPreferencesFile.exists() :
			self.__defaultPreferencesFile.unlink()

if __name__ == "__main__":
	unittest.main()
