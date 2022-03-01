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

import os
import unittest
import imath

import IECore
import Gaffer
import GafferTest

class ApplicationRootTest( GafferTest.TestCase ) :

	__defaultPreferencesFile = os.path.expanduser( "~/gaffer/startup/testApp/preferences.py" )
	__preferencesFile = "/tmp/testPreferences.py"

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

		self.assertFalse( os.path.exists( self.__defaultPreferencesFile ) )
		applicationRoot.savePreferences()
		self.assertTrue( os.path.exists( self.__defaultPreferencesFile ) )

		self.assertFalse( os.path.exists( self.__preferencesFile ) )
		applicationRoot.savePreferences( self.__preferencesFile )
		self.assertTrue( os.path.exists( self.__preferencesFile ) )

		p["category1"]["i"].setValue( 1 )
		p["category2"]["s"].setValue( "beef" )
		p["category2"]["v"].setValue( imath.V3f( -10 ) )

		executionContext = { "application" : application }
		exec(
			compile( open( self.__preferencesFile ).read(), self.__preferencesFile, "exec" ),
			executionContext, executionContext
		)

		self.assertEqual( p["category1"]["i"].getValue(), 10 )
		self.assertEqual( p["category2"]["s"].getValue(), "oranges" )
		self.assertEqual( p["category2"]["v"].getValue(), imath.V3f( 2, 3, 4 ) )

	def testPreferencesPermissionsErrors( self ) :

		a = Gaffer.ApplicationRoot( "testApp" )

		a.savePreferences( self.__preferencesFile )
		os.chmod( self.__preferencesFile, 0 )
		self.assertRaises( RuntimeError, a.savePreferences, self.__preferencesFile )

	def testPreferencesLocation( self ) :

		a = Gaffer.ApplicationRoot( "testApp" )

		self.assertEqual( a.preferencesLocation(), os.path.dirname( self.__defaultPreferencesFile ) )
		self.assertTrue( os.path.isdir( a.preferencesLocation() ) )

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

		for f in [
			self.__defaultPreferencesFile,
			self.__preferencesFile,
		] :
			if os.path.exists( f ) :
				os.remove( f )

if __name__ == "__main__":
	unittest.main()
