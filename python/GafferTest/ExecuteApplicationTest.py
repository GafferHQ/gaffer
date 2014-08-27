##########################################################################
#
#  Copyright (c) 2011, John Haddon. All rights reserved.
#  Copyright (c) 2013-2014, Image Engine Design Inc. All rights reserved.
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
import subprocess
import unittest

import IECore

import Gaffer
import GafferTest

class ExecuteApplicationTest( GafferTest.TestCase ) :

	__scriptFileName = "/tmp/executeScript.gfr"
	__outputFileSeq = IECore.FileSequence( "/tmp/sphere.####.cob" )

	def testErrorReturnStatusForMissingScript( self ) :

		p = subprocess.Popen(
			"gaffer execute thisScriptDoesNotExist",
			shell=True,
			stderr = subprocess.PIPE,
		)
		p.wait()

		self.failUnless( "thisScriptDoesNotExist" in "".join( p.stderr.readlines() ) )
		self.failUnless( p.returncode )

	def testExecuteObjectWriter( self ) :

		s = Gaffer.ScriptNode()

		s["sphere"] = GafferTest.SphereNode()
		s["write"] = Gaffer.ObjectWriter()
		s["write"]["in"].setInput( s["sphere"]["out"] )
		s["write"]["fileName"].setValue( self.__outputFileSeq.fileName )

		s["fileName"].setValue( self.__scriptFileName )
		s.save()

		self.failIf( os.path.exists( self.__outputFileSeq.fileNameForFrame( 1 ) ) )
		p = subprocess.Popen(
			"gaffer execute " + self.__scriptFileName,
			shell=True,
			stderr = subprocess.PIPE,
		)
		p.wait()

		error = "".join( p.stderr.readlines() )
		self.failUnless( error == "" )
		self.failUnless( os.path.exists( self.__outputFileSeq.fileNameForFrame( 1 ) ) )
		self.failIf( p.returncode )

	def testFramesParameter( self ) :

		s = Gaffer.ScriptNode()
		s["sphere"] = GafferTest.SphereNode()
		s["write"] = Gaffer.ObjectWriter()
		s["write"]["in"].setInput( s["sphere"]["out"] )
		s["write"]["fileName"].setValue( self.__outputFileSeq.fileName )

		s["fileName"].setValue( self.__scriptFileName )
		s.save()

		frames = IECore.FrameList.parse( "1-5" )
		for f in frames.asList() :
			self.failIf( os.path.exists( self.__outputFileSeq.fileNameForFrame( f ) ) )

		p = subprocess.Popen(
			"gaffer execute " + self.__scriptFileName + " -frames " + str(frames),
			shell=True,
			stderr = subprocess.PIPE,
		)
		p.wait()

		error = "".join( p.stderr.readlines() )
		self.failUnless( error == "" )
		self.failIf( p.returncode )
		for f in frames.asList() :
			self.failUnless( os.path.exists( self.__outputFileSeq.fileNameForFrame( f ) ) )

	def testContextParameter( self ) :

		s = Gaffer.ScriptNode()
		s["sphere"] = GafferTest.SphereNode()
		s["e"] = Gaffer.Expression()
		s["e"]["engine"].setValue( "python" )
		s["e"]["expression"].setValue( "parent['sphere']['radius'] = context.get( 'sphere:radius', 1 )" )
		s["e2"] = Gaffer.Expression()
		s["e2"]["engine"].setValue( "python" )
		s["e2"]["expression"].setValue( "parent['sphere']['theta'] = context.get( 'sphere:theta', 360 )" )
		s["write"] = Gaffer.ObjectWriter()
		s["write"]["in"].setInput( s["sphere"]["out"] )
		s["write"]["fileName"].setValue( self.__outputFileSeq.fileName )

		s["fileName"].setValue( self.__scriptFileName )
		s.save()

		self.failIf( os.path.exists( self.__outputFileSeq.fileNameForFrame( 1 ) ) )
		p = subprocess.Popen(
			"gaffer execute " + self.__scriptFileName + " -context -sphere:radius 5 -sphere:theta 180",
			shell=True,
			stderr = subprocess.PIPE,
		)
		p.wait()

		error = "".join( p.stderr.readlines() )
		self.failUnless( error == "" )
		self.failIf( p.returncode )
		self.failUnless( os.path.exists( self.__outputFileSeq.fileNameForFrame( 1 ) ) )

		prim = IECore.ObjectReader( self.__outputFileSeq.fileNameForFrame( 1 ) ).read()
		self.failUnless( prim.isInstanceOf( IECore.SpherePrimitive.staticTypeId() ) )
		self.assertEqual( prim.bound(), IECore.Box3f( IECore.V3f( -5 ), IECore.V3f( 5 ) ) )
		self.assertEqual( prim.thetaMax(), 180 )

	def testErrorReturnStatusForBadContext( self ) :

		s = Gaffer.ScriptNode()
		s["fileName"].setValue( self.__scriptFileName )
		s["write"] = Gaffer.ObjectWriter()
		s.save()

		p = subprocess.Popen(
			"gaffer execute -script " + self.__scriptFileName + " -context -myArg 10 -noValue",
			shell=True,
			stderr = subprocess.PIPE,
		)
		p.wait()

		error = "".join( p.stderr.readlines() )
		self.failUnless( "ERROR" in error )
		self.failUnless( "Context parameter" in error )
		self.failUnless( p.returncode )

	def tearDown( self ) :

		files = [ self.__scriptFileName ]
		seq = IECore.ls( self.__outputFileSeq.fileName, minSequenceSize = 1 )
		if seq :
			files.extend( seq.fileNames() )

		for f in files :
			if os.path.exists( f ) :
				os.remove( f )

if __name__ == "__main__":
	unittest.main()

