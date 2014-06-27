##########################################################################
#  
#  Copyright (c) 2014, Image Engine Design Inc. All rights reserved.
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
import stat
import shutil
import unittest

import IECore

import Gaffer
import GafferTest

class LocalDispatcherTest( GafferTest.TestCase ) :
	
	def setUp( self ) :
		
		localDispatcher = Gaffer.Dispatcher.dispatcher( "local" )
		localDispatcher["jobDirectory"].setValue( "/tmp/dispatcherTest" )
		localDispatcher["framesMode"].setValue( Gaffer.Dispatcher.FramesMode.CurrentFrame )
	
	def testDispatcherRegistration( self ) :
		
		self.failUnless( "local" in Gaffer.Dispatcher.dispatcherNames() )
		self.failUnless( Gaffer.Dispatcher.dispatcher( "local" ).isInstanceOf( Gaffer.LocalDispatcher.staticTypeId() ) )
	
	def testDispatch( self ) :
		
		dispatcher = Gaffer.Dispatcher.dispatcher( "local" )
		
		def createWriter( text ) :
			node = GafferTest.TextWriter()
			node["fileName"].setValue( "/tmp/dispatcherTest/%s_####.txt" % text )
			node["text"].setValue( text + " on ${frame}" )
			return node
		
		# Create a tree of dependencies for execution:
		# n1 requires:
		# - n2 requires:
		#    -n2a
		#    -n2b
		s = Gaffer.ScriptNode()
		s["n1"] = createWriter( "n1" )
		s["n2"] = createWriter( "n2" )
		s["n2a"] = createWriter( "n2a" )
		s["n2b"] = createWriter( "n2b" )
		s["n1"]['requirements'][0].setInput( s["n2"]['requirement'] )
		s["n2"]['requirements'][0].setInput( s["n2a"]['requirement'] )
		s["n2"]['requirements'][1].setInput( s["n2b"]['requirement'] )
		
		def verify( contexts, nodes = [ "n1", "n2", "n2a", "n2b" ], exist = True ) :
			
			for context in contexts :
				
				modTimes = {}
				
				for node in s.children( Gaffer.Node ) :
					
					fileName = context.substitute( node["fileName"].getValue() )
					self.assertEqual( os.path.isfile( fileName ), exist )
					if exist :
						modTimes[node.getName()] = os.stat( fileName )[stat.ST_MTIME]
						with file( fileName, "r" ) as f :
							text = f.read()
						self.assertEqual( text, "%s on %d" % ( node.getName(), context.getFrame() ) )
				
				if exist :
					if "n1" in nodes :
						self.assertGreater( modTimes["n1"], modTimes["n2"] )
					else :
						self.assertLess( modTimes["n1"], modTimes["n2"] )
					
					if "n2" in nodes :
						self.assertGreater( modTimes["n2"], modTimes["n2a"] )
						self.assertGreater( modTimes["n2"], modTimes["n2b"] )
					else :
						if "n2a" in nodes :
							self.assertLess( modTimes["n2"], modTimes["n2a"] )
						if "n2b" in nodes :
							self.assertLess( modTimes["n2"], modTimes["n2b"] )
		
		# No files should exist yet
		verify( [ s.context() ], exist = False )
		
		# Executing n1 should trigger execution of all of them
		dispatcher.dispatch( [ s["n1"] ] )
		verify( [ s.context() ] )
		
		# Executing n1 and anything else, should be the same as just n1
		dispatcher.dispatch( [ s["n2b"], s["n1"] ] )
		verify( [ s.context() ] )
		
		# Executing all nodes should be the same as just n1
		dispatcher.dispatch( [ s["n2"], s["n2b"], s["n1"], s["n2a"] ] )
		verify( [ s.context() ] )
		
		# Executing a sub-branch (n2) should only trigger execution in that branch
		dispatcher.dispatch( [ s["n2"] ] )
		verify( [ s.context() ], nodes = [ "n2", "n2a", "n2b" ] )
		
		# Executing a leaf node, should not trigger other executions.		
		dispatcher.dispatch( [ s["n2b"] ] )
		verify( [ s.context() ], nodes = [ "n2b" ] )
	
	def testDispatchDifferentFrame( self ) :
		
		s = Gaffer.ScriptNode()
		s["n1"] = GafferTest.TextWriter()
		s["n1"]["fileName"].setValue( "/tmp/dispatcherTest/n1_####.txt" )
		s["n1"]["text"].setValue( "n1 on ${frame}" )
		
		context = Gaffer.Context( s.context() )
		context.setFrame( s.context().getFrame() + 10 )
		
		with context :
			Gaffer.Dispatcher.dispatcher( "local" ).dispatch( [ s["n1"] ] )
		
		fileName = context.substitute( s["n1"]["fileName"].getValue() )
		self.assertTrue( os.path.isfile( fileName ) )
		with file( fileName, "r" ) as f :
			text = f.read()
		self.assertEqual( text, "%s on %d" % ( s["n1"].getName(), context.getFrame() ) )
	
	def testDispatchScriptRange( self ) :
		
		dispatcher = Gaffer.Dispatcher.dispatcher( "local" )
		dispatcher["framesMode"].setValue( Gaffer.Dispatcher.FramesMode.ScriptRange )
		frameList = IECore.FrameList.parse( "5-7" )
		
		def createWriter( text ) :
			node = GafferTest.TextWriter()
			node["fileName"].setValue( "/tmp/dispatcherTest/%s_####.txt" % text )
			node["text"].setValue( text + " on ${frame}" )
			return node
		
		# Create a tree of dependencies for execution:
		# n1 requires:
		# - n2 requires:
		#    -n2a
		#    -n2b
		s = Gaffer.ScriptNode()
		s["frameRange"]["start"].setValue( 5 )
		s["frameRange"]["end"].setValue( 7 )
		s["n1"] = createWriter( "n1" )
		s["n2"] = createWriter( "n2" )
		s["n2a"] = createWriter( "n2a" )
		s["n2b"] = createWriter( "n2b" )
		s["n1"]['requirements'][0].setInput( s["n2"]['requirement'] )
		s["n2"]['requirements'][0].setInput( s["n2a"]['requirement'] )
		s["n2"]['requirements'][1].setInput( s["n2b"]['requirement'] )
		
		def verify( contexts, nodes = [ "n1", "n2", "n2a", "n2b" ], exist = True ) :
			
			for context in contexts :
				
				modTimes = {}
				
				for node in s.children( Gaffer.Node ) :
					
					fileName = context.substitute( node["fileName"].getValue() )
					self.assertEqual( os.path.isfile( fileName ), exist )
					if exist :
						sequences = IECore.ls( os.path.dirname( fileName ), minSequenceSize = 1 )
						sequence = [ x for x in sequences if x.fileName.startswith( node.getName() ) ][0]
						self.assertEqual( sequence.frameList, frameList )
						modTimes[node.getName()] = os.stat( fileName )[stat.ST_MTIME]
						with file( fileName, "r" ) as f :
							text = f.read()
						self.assertEqual( text, "%s on %d" % ( node.getName(), context.getFrame() ) )
				
				if exist :
					if "n1" in nodes :
						self.assertGreater( modTimes["n1"], modTimes["n2"] )
					
					if "n2" in nodes :
						self.assertGreater( modTimes["n2"], modTimes["n2a"] )
						self.assertGreater( modTimes["n2"], modTimes["n2b"] )
					elif "n2b" in nodes :
						self.assertLess( modTimes["n2"], modTimes["n2b"] )
		
		contexts = []
		for frame in frameList.asList() :
			contexts.append( Gaffer.Context( s.context(), Gaffer.Context.Ownership.Borrowed ) )
			contexts[-1].setFrame( frame )
		
		# No files should exist yet
		verify( contexts, exist = False )
		
		# Executing n1 should trigger execution of all of them
		dispatcher.dispatch( [ s["n1"] ] )
		verify( contexts )
		
		# Executing a leaf node, should not trigger other executions.		
		dispatcher.dispatch( [ s["n2b"] ] )
		verify( contexts, nodes = [ "n2b" ] )
	
	def testDispatchCustomRange( self ) :
		
		dispatcher = Gaffer.Dispatcher.dispatcher( "local" )
		dispatcher["framesMode"].setValue( Gaffer.Dispatcher.FramesMode.CustomRange )
		frameList = IECore.FrameList.parse( "2-6x2" )
		dispatcher["frameRange"].setValue( str(frameList) )
		
		def createWriter( text ) :
			node = GafferTest.TextWriter()
			node["fileName"].setValue( "/tmp/dispatcherTest/%s_####.txt" % text )
			node["text"].setValue( text + " on ${frame}" )
			return node
		
		# Create a tree of dependencies for execution:
		# n1 requires:
		# - n2 requires:
		#    -n2a
		#    -n2b
		s = Gaffer.ScriptNode()
		s["n1"] = createWriter( "n1" )
		s["n2"] = createWriter( "n2" )
		s["n2a"] = createWriter( "n2a" )
		s["n2b"] = createWriter( "n2b" )
		s["n1"]['requirements'][0].setInput( s["n2"]['requirement'] )
		s["n2"]['requirements'][0].setInput( s["n2a"]['requirement'] )
		s["n2"]['requirements'][1].setInput( s["n2b"]['requirement'] )
		
		def verify( contexts, nodes = [ "n1", "n2", "n2a", "n2b" ], exist = True ) :
			
			for context in contexts :
				
				modTimes = {}
				
				for node in s.children( Gaffer.Node ) :
					
					fileName = context.substitute( node["fileName"].getValue() )
					self.assertEqual( os.path.isfile( fileName ), exist )
					if exist :
						sequences = IECore.ls( os.path.dirname( fileName ), minSequenceSize = 1 )
						sequence = [ x for x in sequences if x.fileName.startswith( node.getName() ) ][0]
						self.assertEqual( sequence.frameList, frameList )
						modTimes[node.getName()] = os.stat( fileName )[stat.ST_MTIME]
						with file( fileName, "r" ) as f :
							text = f.read()
						self.assertEqual( text, "%s on %d" % ( node.getName(), context.getFrame() ) )
				
				if exist :
					if "n1" in nodes :
						self.assertGreater( modTimes["n1"], modTimes["n2"] )
					
					if "n2" in nodes :
						self.assertGreater( modTimes["n2"], modTimes["n2a"] )
						self.assertGreater( modTimes["n2"], modTimes["n2b"] )
					elif "n2b" in nodes :
						self.assertLess( modTimes["n2"], modTimes["n2b"] )
		
		contexts = []
		for frame in frameList.asList() :
			contexts.append( Gaffer.Context( s.context(), Gaffer.Context.Ownership.Borrowed ) )
			contexts[-1].setFrame( frame )
		
		# No files should exist yet
		verify( contexts, exist = False )
		
		# Executing n1 should trigger execution of all of them
		dispatcher.dispatch( [ s["n1"] ] )
		verify( contexts )
		
		# Executing a leaf node, should not trigger other executions.		
		dispatcher.dispatch( [ s["n2b"] ] )
		verify( contexts, nodes = [ "n2b" ] )
	
	def testDispatchBadCustomRange( self ) :
		
		dispatcher = Gaffer.Dispatcher.dispatcher( "local" )
		dispatcher["framesMode"].setValue( Gaffer.Dispatcher.FramesMode.CustomRange )
		dispatcher["frameRange"].setValue( "notAFrameRange" )
		
		s = Gaffer.ScriptNode()
		s["n1"] = GafferTest.TextWriter()
		s["n1"]["fileName"].setValue( "/tmp/dispatcherTest/n1_####.txt" )
		s["n1"]["text"].setValue( "n1 on ${frame}" )
		
		self.assertRaises( RuntimeError, dispatcher.dispatch, [ s["n1"] ] )
		self.assertFalse( os.path.isfile( s.context().substitute( s["n1"]["fileName"].getValue() ) ) )
	
	def testContextVariation( self ) :
		
		s = Gaffer.ScriptNode()
		context = Gaffer.Context( s.context() )
		context["script:name"] = "notTheRealScriptName"
		context["textWriter:replace"] = IECore.StringVectorData( [ " ", "\n" ] )
		
		s["n1"] = GafferTest.TextWriter()
		s["n1"]["fileName"].setValue( "/tmp/dispatcherTest/${script:name}_####.txt" )
		s["n1"]["text"].setValue( "${script:name} on ${frame}" )
		
		fileName = context.substitute( s["n1"]["fileName"].getValue() )
		self.assertFalse( os.path.isfile( fileName ) )
		
		with context :
			Gaffer.Dispatcher.dispatcher( "local" ).dispatch( [ s["n1"] ] )
		
		self.assertTrue( os.path.isfile( fileName ) )
		self.assertTrue( os.path.basename( fileName ).startswith( context["script:name"] ) )
		with file( fileName, "r" ) as f :
			text = f.read()
		expected = "%s on %d" % ( context["script:name"], context.getFrame() )
		expected = expected.replace( context["textWriter:replace"][0], context["textWriter:replace"][1] )
		self.assertEqual( text, expected )
	
	def testDispatcherSignals( self ) :
		
		class CapturingSlot2( list ) :
			
			def __init__( self, *signals ) :
				
				self.__connections = []
				for s in signals :
					self.__connections.append( s.connect( Gaffer.WeakMethod( self.__slot ) ) )
			
			def __slot( self, d, nodes ) :
				self.append( (d,nodes) )
		
		preCs = CapturingSlot2( Gaffer.Dispatcher.preDispatchSignal() )
		self.assertEqual( len( preCs ), 0 )
		postCs = GafferTest.CapturingSlot( Gaffer.Dispatcher.postDispatchSignal() )
		self.assertEqual( len( postCs ), 0 )
		
		s = Gaffer.ScriptNode()
		s["n1"] = GafferTest.TextWriter()
		s["n1"]["fileName"].setValue( "/tmp/dispatcherTest/n1_####.txt" )
		s["n1"]["text"].setValue( "n1 on ${frame}" )
		
		dispatcher = Gaffer.Dispatcher.dispatcher( "local" )
		dispatcher.dispatch( [ s["n1"] ] )
		
		self.assertEqual( len( preCs ), 1 )
		self.failUnless( preCs[0][0].isSame( dispatcher ) )
		self.assertEqual( preCs[0][1], [ s["n1"] ] )
		
		self.assertEqual( len( postCs ), 1 )
		self.failUnless( postCs[0][0].isSame( dispatcher ) )
		self.assertEqual( postCs[0][1], [ s["n1"] ] )
	
	def testBadJobDirectory( self ) :
		
		dispatcher = Gaffer.LocalDispatcher()
		self.assertEqual( dispatcher["jobName"].getValue(), "" )
		self.assertEqual( dispatcher["jobDirectory"].getValue(), "" )
		jobDir = dispatcher.jobDirectory( Gaffer.Context() )
		self.assertNotEqual( jobDir, "" )
		self.assertTrue( os.path.exists( jobDir ) )
		shutil.rmtree( jobDir )
	
	def tearDown( self ) :
		
		shutil.rmtree( "/tmp/dispatcherTest", ignore_errors = True )

if __name__ == "__main__":
	unittest.main()
	
