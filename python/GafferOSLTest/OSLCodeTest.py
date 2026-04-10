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

import os
import pathlib
import subprocess
import shutil
import unittest
import functools
import imath

import IECore

import Gaffer
import GafferTest
import GafferOSL
import GafferOSLTest

class OSLCodeTest( GafferOSLTest.OSLTestCase ) :

	def setUp( self ) :

		GafferOSLTest.OSLTestCase.setUp( self )

		# Arrange to restore GAFFEROSL_CODE_DIRECTORY env-var, so tests
		# are free to modify it temporarily.

		oslCodeDir = os.environ.get( "GAFFEROSL_CODE_DIRECTORY" )
		if oslCodeDir :
			self.addCleanup( os.environ.__setitem__, "GAFFEROSL_CODE_DIRECTORY", oslCodeDir )
		else :
			self.addCleanup( os.environ.__delitem__, "GAFFEROSL_CODE_DIRECTORY" )

	def testPlugTypes( self ) :

		oslCode = GafferOSL.OSLCode()
		code = ""

		for i, plugType in enumerate( [
			Gaffer.IntPlug,
			Gaffer.FloatPlug,
			functools.partial( Gaffer.V3fPlug, interpretation = IECore.GeometricData.Interpretation.Vector ),
			Gaffer.Color3fPlug,
			Gaffer.M44fPlug,
			Gaffer.StringPlug,
			GafferOSL.ClosurePlug,
		] ) :

			inName = "in%d" % i
			outName = "out%d" % i

			oslCode["parameters"][inName] = plugType( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
			oslCode["out"][outName] = plugType( direction = Gaffer.Plug.Direction.Out, flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

			code += "%s = %s;\n" % ( outName, inName )

		oslCode["code"].setValue( code )

		# The OSLCode node will have generated a shader from
		# the code and parameters we gave it. Load this onto
		# a regular OSLShader node to check it.

		oslShader = GafferOSL.OSLShader()
		oslShader.loadShader( self.__osoFileName( oslCode ) )

		self.assertEqual( oslShader["parameters"].keys(), oslCode["parameters"].keys() )
		self.assertEqual( oslShader["out"].keys(), oslCode["out"].keys() )

		for p in oslShader["parameters"].children() :
			p.setFlags( Gaffer.Plug.Flags.Dynamic, True )
			self.assertEqual( repr( p ), repr( oslCode["parameters"][p.getName()] ) )

		for p in oslShader["out"].children() :
			p.setFlags( Gaffer.Plug.Flags.Dynamic, True )
			self.assertEqual( repr( p ), repr( oslCode["out"][p.getName()] ) )

	def testParseError( self ) :

		n = GafferOSL.OSLCode()
		n["code"].setValue( "oops" )
		with self.assertRaisesRegex( Gaffer.ProcessException, "'oops' was not declared in this scope" ) :
			self.__osoFileName( n )

	def testParseErrorDoesntDestroyExistingPlugs( self ) :

		n = GafferOSL.OSLCode()
		n["parameters"]["in"] = Gaffer.IntPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		n["out"]["out"] = Gaffer.IntPlug( direction = Gaffer.Plug.Direction.Out, flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		originalPlugs = n["parameters"].children() + n["out"].children()

		n["code"].setValue( "oops" )
		with self.assertRaisesRegex( Gaffer.ProcessException, "'oops' was not declared in this scope" ) :
			self.__osoFileName( n )

		self.assertEqual( n["parameters"].children() + n["out"].children(), originalPlugs )

	def testEmpty( self ) :

		# We want empty shaders to still output a
		# shader so that the ShaderView picks it
		# up, ready to update when an output is
		# added.

		n = GafferOSL.OSLCode()
		self.assertTrue( self.__osoFileName( n ) )
		self.assertEqual( n["type"].getValue(), "osl:shader" )

		n["code"].setValue( "//" )
		self.assertTrue( self.__osoFileName( n ) )
		self.assertEqual( n["type"].getValue(), "osl:shader" )

		n["code"].setValue( "" )
		self.assertTrue( self.__osoFileName( n ) )
		self.assertEqual( n["type"].getValue(), "osl:shader" )

	def testMissingSemiColon( self ) :

		n1 = GafferOSL.OSLCode()
		n1["parameters"]["in"] = Gaffer.IntPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		n1["out"]["out"] = Gaffer.IntPlug( direction = Gaffer.Plug.Direction.Out, flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		n2 = GafferOSL.OSLCode()
		n2["parameters"]["in"] = Gaffer.IntPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		n2["out"]["out"] = Gaffer.IntPlug( direction = Gaffer.Plug.Direction.Out, flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		# The OSLCode node will often be used to throw in a one-liner,
		# and omitting a semicolon is an easy mistake that we should
		# correct automatically.
		n1["code"].setValue( "out = in * 2" )
		n2["code"].setValue( "out = in * 2;" )

		self.assertEqual( self.__osoFileName( n1 ), self.__osoFileName( n2 ) )

	def testAddingAndRemovingPlugsUpdatesShader( self ) :

		oslCode = GafferOSL.OSLCode()
		oslCode["parameters"]["in"] = Gaffer.IntPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		oslCode["out"]["out"] = Gaffer.IntPlug( direction = Gaffer.Plug.Direction.Out, flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		oslShader = GafferOSL.OSLShader()
		oslShader.loadShader( self.__osoFileName( oslCode ) )
		self.assertTrue( "in" in oslShader["parameters"] )
		self.assertTrue( "out" in oslShader["out"] )

	def testObjectProcessingFunctions( self ) :

		oslCode = GafferOSL.OSLCode()
		oslCode["out"]["out"] = Gaffer.FloatPlug( direction = Gaffer.Plug.Direction.Out, flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		oslCode["code"].setValue( 'out = inFloat( "s", 0 );' )
		self.__osoFileName( oslCode ) # Will error if can't compile shader

	def testImageProcessingFunctions( self ) :

		oslCode = GafferOSL.OSLCode()
		oslCode["out"]["out"] = Gaffer.FloatPlug( direction = Gaffer.Plug.Direction.Out, flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		oslCode["code"].setValue( 'out = inChannel( "R", 0 );' )
		self.__osoFileName( oslCode ) # Will error if can't compile shader

	def testColorRamp( self ) :

		oslCode = GafferOSL.OSLCode()
		oslCode["parameters"]["sp"] = Gaffer.RampfColor3fPlug(
			defaultValue = IECore.RampfColor3f(
				(
					( 0, imath.Color3f( 0 ) ),
					( 1, imath.Color3f( 1 ) ),
				),
				IECore.RampInterpolation.CatmullRom
			),
			flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic
		)
		oslCode["out"]["o"] = Gaffer.Color3fPlug( direction = Gaffer.Plug.Direction.Out, flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		oslCode["code"].setValue( "o = colorSpline( spPositions, spValues, spBasis, u );" )

		# Load the generated shader onto an OSLShader
		# node to verify it.

		oslShader = GafferOSL.OSLShader()
		oslShader.loadShader( self.__osoFileName( oslCode ) )

		oslShader["parameters"]["sp"].setFlags( Gaffer.Plug.Flags.Dynamic, True )

		self.assertEqual( repr( oslShader["parameters"]["sp"] ), repr( oslCode["parameters"]["sp"] ) )

	def testShaderNameMatchesFileName( self ) :

		oslCode = GafferOSL.OSLCode()
		oslCode["out"]["o"] = Gaffer.Color3fPlug( direction = Gaffer.Plug.Direction.Out, flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		oslCode["code"].setValue( "o = color( 0, 1, 0 );" )

		info = subprocess.check_output( [ "oslinfo", self.__osoFileName( oslCode ) ], universal_newlines = True )
		self.assertTrue(
			info.startswith( "shader \"{0}\"".format( pathlib.Path( self.__osoFileName( oslCode ) ).name ) )
		)

	def testSerialisation( self ) :

		s = Gaffer.ScriptNode()
		s["o"] = GafferOSL.OSLCode()
		s["o"]["parameters"]["i"] = Gaffer.Color3fPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		s["o"]["out"]["o"] = Gaffer.Color3fPlug( direction = Gaffer.Plug.Direction.Out, flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		s["o"]["code"].setValue( "o = i * color( u, v, 0 );")

		s2 = Gaffer.ScriptNode()
		s2.execute( s.serialise() )

		self.assertEqual( self.__osoFileName( s2["o"] ), self.__osoFileName( s["o"] ) )

	def testUndo( self ) :

		s = Gaffer.ScriptNode()
		s["o"] = GafferOSL.OSLCode()

		f1 = self.__osoFileName( s["o"] )

		with Gaffer.UndoScope( s ) :
			s["o"]["parameters"]["i"] = Gaffer.Color3fPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
			s["o"]["out"]["o"] = Gaffer.Color3fPlug( direction = Gaffer.Plug.Direction.Out, flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		f2 = self.__osoFileName( s["o"] )
		self.assertNotEqual( f2, f1 )

		with Gaffer.UndoScope( s ) :
			s["o"]["code"].setValue( "o = i * color( u, v, 0 );")

		f3 = self.__osoFileName( s["o"] )
		self.assertNotEqual( f3, f1 )
		self.assertNotEqual( f3, f2 )

		s.undo()
		self.assertEqual( self.__osoFileName( s["o"] ), f2 )

		s.undo()
		self.assertEqual( self.__osoFileName( s["o"] ), f1 )

		s.redo()
		self.assertEqual( self.__osoFileName( s["o"] ), f2 )

		s.redo()
		self.assertEqual( self.__osoFileName( s["o"] ), f3 )

	def testSource( self ) :

		# Make a shader using the OSLCode node.

		oslCode = GafferOSL.OSLCode()

		oslCode["parameters"]["i"] = Gaffer.Color3fPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		oslCode["out"]["o"] = Gaffer.Color3fPlug( direction = Gaffer.Plug.Direction.Out, flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		oslCode["code"].setValue( "o = i * color( u, v, 0 );")

		# Export it to a .osl file and compile it.

		oslFilePath = self.temporaryDirectory() / "test.osl"
		with open( oslFilePath, "w", encoding = "utf-8" ) as f :
			f.write( oslCode.source( "test") )

		shader = self.compileShader( oslFilePath )

		# Load that onto an OSLShader and check that
		# it matches.

		oslShader = GafferOSL.OSLShader()
		oslShader.loadShader( shader )

		self.assertEqual( oslShader["parameters"].keys(), oslCode["parameters"].keys() )
		self.assertEqual( oslShader["out"].keys(), oslCode["out"].keys() )

		for p in oslShader["parameters"].children() :
			p.setFlags( Gaffer.Plug.Flags.Dynamic, True )
			self.assertEqual( repr( p ), repr( oslCode["parameters"][p.getName()] ) )

		for p in oslShader["out"].children() :
			p.setFlags( Gaffer.Plug.Flags.Dynamic, True )
			self.assertEqual( repr( p ), repr( oslCode["out"][p.getName()] ) )

	def testSourceUsesRequestedName( self ) :

		oslCode = GafferOSL.OSLCode()
		source = oslCode.source( "test" )
		self.assertTrue( "shader test" in source )

	def testParameterRenaming( self ) :

		oslCode = GafferOSL.OSLCode()
		oslCode["parameters"]["i"] = Gaffer.Color3fPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		oslCode["out"]["o"] = Gaffer.Color3fPlug( direction = Gaffer.Plug.Direction.Out, flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		oslCode["code"].setValue( "o = in" )

		with self.assertRaisesRegex( Gaffer.ProcessException, "'in' was not declared in this scope" ) :
			self.__osoFileName( oslCode )

		cs = GafferTest.CapturingSlot( oslCode.plugDirtiedSignal() )
		oslCode["parameters"]["i"].setName( "in" )
		self.assertTrue( oslCode["out"] in [ x[0] for x in cs ] )
		self.__osoFileName( oslCode )

		oslCode["parameters"]["in"].setName( "i" )
		with self.assertRaisesRegex( Gaffer.ProcessException, "'in' was not declared in this scope" ) :
			self.__osoFileName( oslCode )

	def testMoveCodeDirectory( self ) :

		# Make an OSL shader in a specific code directory.

		os.environ["GAFFEROSL_CODE_DIRECTORY"] = ( self.temporaryDirectory() / "codeDirectoryA" ).as_posix()

		s = Gaffer.ScriptNode()

		s["o"] = GafferOSL.OSLCode()
		s["o"]["parameters"]["i"] = Gaffer.Color3fPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		s["o"]["out"]["o"] = Gaffer.Color3fPlug( direction = Gaffer.Plug.Direction.Out, flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		s["o"]["code"].setValue( "o = i * color( u, v, 0 );")

		self.assertTrue( self.__osoFileName( s["o"] ).startswith( os.environ["GAFFEROSL_CODE_DIRECTORY"] ) )

		# Now simulate the loading of that script in a different environment,
		# with a different code directory.

		scriptFileName = self.temporaryDirectory() / "test.gfr"
		s["fileName"].setValue( scriptFileName )
		s.save()

		shutil.rmtree( os.environ["GAFFEROSL_CODE_DIRECTORY"] )

		env = os.environ.copy()
		env["GAFFEROSL_CODE_DIRECTORY"] = ( self.temporaryDirectory() / "codeDirectoryB" ).as_posix()

		subprocess.check_call(
			[
				str( Gaffer.executablePath() ), "env", "python", "-c",
				"import GafferOSLTest; GafferOSLTest.OSLCodeTest()._assertMovedCodeDirectoryOK( '{scriptFileName}' )".format(
					scriptFileName = scriptFileName.as_posix()
				)
			],
			env = env
		)

	def _assertMovedCodeDirectoryOK( self, scriptFileName ) :

		s = Gaffer.ScriptNode()
		s["fileName"].setValue( scriptFileName )
		s.load()

		self.assertTrue( self.__osoFileName( s["o"] ).startswith( os.environ["GAFFEROSL_CODE_DIRECTORY"] ) )

	def testRenameRemovedParameter( self ) :

		parameter = Gaffer.Color3fPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		oslCode = GafferOSL.OSLCode()
		oslCode["parameters"]["c"] = parameter
		oslCode["parameters"].removeChild( parameter )

		# Changing name is irrelevant now we've removed the parameter,
		# and shouldn't propagate dirtiness.

		cs = GafferTest.CapturingSlot( oslCode.plugDirtiedSignal() )
		parameter.setName( "d" )
		self.assertEqual( len( cs ), 0 )

	def testParseErrorLineNumbers( self ) :

		oslCode = GafferOSL.OSLCode()
		oslCode["code"].setValue( "undefined" )

		with self.assertRaisesRegex( Gaffer.ProcessException, "code:1: error: 'undefined' was not declared in this scope$" ) :
			self.__osoFileName( oslCode )

	def testShaderNotCompiledForEveryParameterAddition( self ) :

		directory = self.temporaryDirectory() / "oslCode"
		os.environ["GAFFEROSL_CODE_DIRECTORY"] = directory.as_posix()
		self.assertFalse( directory.exists() )

		# Shader is only generated when we ask for it.

		oslCode = GafferOSL.OSLCode()
		oslCode["parameters"]["i"] = Gaffer.IntPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		self.assertFalse( directory.exists() )

		self.__osoFileName( oslCode )
		self.assertTrue( directory.exists() )
		self.assertEqual( len( list( directory.iterdir() ) ), 1 )

		# And is only regenerated when we ask for it again.

		oslCode["parameters"]["j"] = Gaffer.IntPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		oslCode["parameters"]["k"] = Gaffer.IntPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		self.assertEqual( len( list( directory.iterdir() ) ), 1 )

		self.__osoFileName( oslCode )
		self.assertEqual( len( list( directory.iterdir() ) ), 2 )

	def testMetadataDoesntThrowOnCodingError( self ) :

		oslCode = GafferOSL.OSLCode()
		oslCode["parameters"]["i"] = Gaffer.IntPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		oslCode["code"].setValue( "oops!" )

		self.assertIsNone( oslCode.shaderMetadata( "test" ) )
		self.assertIsNone( oslCode.parameterMetadata( oslCode["parameters"]["i"], "test" ) )

	def testOutputGetValueDoesntThrowOnCodingError( self ) :

		oslCode = GafferOSL.OSLCode()
		oslCode["out"]["i"] = Gaffer.IntPlug( direction = Gaffer.Plug.Direction.Out, flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		oslCode["code"].setValue( "oops!" )

		self.assertEqual( oslCode["out"]["i"].getValue(), 0 )

	def __osoFileName( self, oslCode ) :

		result = oslCode.attributes()["osl:shader"].outputShader().name
		self.assertTrue( pathlib.Path( result ).with_suffix( ".oso" ).is_file() )
		return result

if __name__ == "__main__":
	unittest.main()
