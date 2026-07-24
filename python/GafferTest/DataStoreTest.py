##########################################################################
#
#  Copyright (c) 2026, Image Engine Design Inc. All rights reserved.
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

import inspect
import os
import pathlib
import random
import shutil
import tempfile
import unittest

import IECore

import Gaffer
import GafferDispatch
import GafferTest

class DataStoreTest( GafferTest.TestCase ) :

	def setupComparison( self, s ) :
		s["dataStore"] = Gaffer.DataStore()
		s["compareBox"] = Gaffer.Box()
		s["compareBox"]["compound"] = Gaffer.CompoundDataPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

	def comparisonSetEntry( self, s, key, value ) :
		if value is None:
			s["dataStore"].removeEntry( key )
			del s["compareBox"]["compound"][key]
		else:
			s["dataStore"].setEntry( key, value )
			s["compareBox"]["compound"].addMembers( IECore.CompoundData( { key : value } ), True )

	def assertComparisonValid( self, s ) :
		keys = set( s["dataStore"]["keys"].getValue() )

		compoundData = IECore.CompoundData()
		s["compareBox"]["compound"].fillCompoundData( compoundData )

		self.assertEqual( keys, set( [ k for k in compoundData.keys() ] ) )

		for k in keys:
			self.assertEqual( s["dataStore"].getEntry( k ), compoundData[ k ] )

	def assertSaved( self, s ) :

		hashes = set()

		for dataStore in Gaffer.DataStore.RecursiveRange( s ):

			keys = set( dataStore["keys"].getValue() )
			for k in keys:
				hashes.add( dataStore.getEntry( k ).hash() )
				self.assertFalse( dataStore.isLive( k ) )

		storeDir = s["fileName"].getValue() + ".dataStore"
		entryFiles = set()
		if not os.path.exists( storeDir ):
			# If the store dir doesn't exist, that is equivalent to having an empty store dir
			# One is the situation if a script has never had data stores, one is the situation if
			# all data stores have been deleted, either is fine, if it corresponds to a script with
			# no data stores.
			pass
		else:
			entryFiles = set( os.listdir( storeDir ) )

		expectedEntryFiles = set( [ "%s.cob" % h.toString() for h in hashes ] )
		# We can ignore a .recycleBin - it will be deleted when the ScriptNode is freed
		if ".recycleBin" in entryFiles:
			entryFiles.remove( ".recycleBin" )

		self.assertEqual( entryFiles, expectedEntryFiles )

	def testBasic( self ):

		s = Gaffer.ScriptNode()
		s["dataStore"] = Gaffer.DataStore()
		s["dataStore"].setEntry( "a", IECore.IntData( 7 ) )
		s["dataStore"].setEntry( "b", IECore.FloatData( 123.456 ) )
		s["dataStore"].setEntry( "c", IECore.StringData( "Hello world" ) )

		self.assertEqual( s["dataStore"].getEntry( "a" ), IECore.IntData( 7 ) )
		self.assertEqual( s["dataStore"].getEntry( "b" ), IECore.FloatData( 123.456 ) )
		self.assertEqual( s["dataStore"].getEntry( "c" ), IECore.StringData( "Hello world" ) )

		with self.assertRaisesRegex( IECore.Exception, "Unknown key: d" ) :
			self.assertEqual( s["dataStore"].getEntry( "d" ), IECore.StringData( "Hello world" ) )
		self.assertEqual( s["dataStore"].getEntry( "d", throwExceptions = False ), None )

		s["dataStore"]["selector"].setValue( "a")
		self.assertEqual( s["dataStore"]["out"].getValue(), IECore.IntData( 7 ) )
		s["dataStore"]["selector"].setValue( "c")
		self.assertEqual( s["dataStore"]["out"].getValue(), IECore.StringData( "Hello world" ) )
		s["dataStore"]["selector"].setValue( "${contextVar}")

		c = Gaffer.Context()
		with c:
			c["contextVar"] = IECore.StringData( "a" )
			self.assertEqual( s["dataStore"]["out"].getValue(), IECore.IntData( 7 ) )
			c["contextVar"] = IECore.StringData( "b" )
			self.assertEqual( s["dataStore"]["out"].getValue(), IECore.FloatData( 123.456 ) )
			c["contextVar"] = IECore.StringData( "d" )
			with self.assertRaisesRegex( Gaffer.ProcessException, "Unknown key: d" ) :
				s["dataStore"]["out"].getValue()


		# After saving, the live values will be cleared, and values will be read from disk
		s["fileName"].setValue( self.temporaryDirectory() / "test.gfr" )
		s.save()
		Gaffer.ValuePlug.clearCache()

		self.assertEqual( s["dataStore"].getEntry( "a" ), IECore.IntData( 7 ) )
		self.assertEqual( s["dataStore"].getEntry( "b" ), IECore.FloatData( 123.456 ) )
		self.assertEqual( s["dataStore"].getEntry( "c" ), IECore.StringData( "Hello world" ) )

	def testComparison( self ):
		# Test by comparing against values stored explicitly in the Gaffer script
		s = Gaffer.ScriptNode()
		self.setupComparison( s )
		self.comparisonSetEntry( s, "a", IECore.IntData( 7 ) )
		self.comparisonSetEntry( s, "b", IECore.FloatData( 123.456 ) )
		self.comparisonSetEntry( s, "c", IECore.StringData( "Hello world" ) )
		self.assertComparisonValid( s )

		s["fileName"].setValue( self.temporaryDirectory() / "test.gfr" )
		s.save()
		self.assertComparisonValid( s )
		self.assertSaved( s )

		del s

		self.assertFalse( os.path.exists( self.temporaryDirectory() / "test.gfr.dataStore" / ".recycleBin" ) )

		# Test match after reopening
		s = Gaffer.ScriptNode()
		s["fileName"].setValue( self.temporaryDirectory() / "test.gfr" )
		s.load()
		self.assertComparisonValid( s )
		self.assertSaved( s )

		# Modify two entries, check that the old data stores get moved to the recycle bin
		self.comparisonSetEntry( s, "a", IECore.IntData( 1 ) )
		self.comparisonSetEntry( s, "b", IECore.FloatData( 2 ) )

		s.save()
		self.assertComparisonValid( s )
		self.assertSaved( s )

		self.assertTrue( os.path.exists( self.temporaryDirectory() / "test.gfr.dataStore" ) )
		self.assertTrue( os.path.exists( self.temporaryDirectory() / "test.gfr.dataStore" / ".recycleBin" ) )
		self.assertEqual( len( os.listdir( self.temporaryDirectory() / "test.gfr.dataStore" / ".recycleBin" ) ), 2 )

		# Do another save, which moves another entry to the recycle bin
		self.comparisonSetEntry( s, "a", IECore.IntData( 10000 ) )
		self.assertComparisonValid( s )
		s.save()
		self.assertComparisonValid( s )
		self.assertSaved( s )

		self.assertEqual( len( os.listdir( self.temporaryDirectory() / "test.gfr.dataStore" / ".recycleBin" ) ), 3 )

		del s

		# Closing the script deletes the recycle bin
		self.assertFalse( os.path.exists( self.temporaryDirectory() / "test.gfr.dataStore" / ".recycleBin" ) )

		# Everything still loads fine
		s = Gaffer.ScriptNode()
		s["fileName"].setValue( self.temporaryDirectory() / "test.gfr" )
		s.load()
		self.assertComparisonValid( s )
		self.assertSaved( s )

	def testComparisonFuzz( self ):

		# At any given time, there are 5 main actions that can be taken that affect DataStores in
		# the current script:
		# A) setting a new entry
		# B) changing an existing entry
		# C) undoing
		# D) redoing
		# E) changing the filename
		# We can achieve a good mix of A and B just by choosing randomly from a small pool of possible options,
		# and alternate between the other options by picking randomly.
		# This allows us to generate a sequence of actions that should theoretically exercise all possibilities,
		# which we can compare against an implementation that just saves values in the script.

		s = Gaffer.ScriptNode()
		self.setupComparison( s )

		random.seed( 42 )

		fileNameCount = 0
		fileName = self.temporaryDirectory() / ( "test%i.gfr" % fileNameCount )
		s["fileName"].setValue( fileName )

		for i in range( 100 ):
			if random.random() < 0.05:
				fileNameCount += 1
				fileName = self.temporaryDirectory() / ( "test%i.gfr" % fileNameCount )
				s["fileName"].setValue( fileName )
			elif s.redoAvailable() and random.random() < 0.7:
				s.redo()
			elif s.undoAvailable() and random.random() < 0.3:
				s.undo()
			else:
				with Gaffer.UndoScope( s ) :
					self.comparisonSetEntry( s, "a%i" % random.randint( 0, 6 ), IECore.IntData( random.randint( 0, 10000 ) ) )

			self.assertComparisonValid( s )
			s.save()
			self.assertComparisonValid( s )
			self.assertSaved( s )

			loadS = Gaffer.ScriptNode()
			loadS["fileName"].setValue( fileName )
			loadS.load()
			self.assertComparisonValid( loadS )
			del loadS

	def testMovingManyEntriesToRecycleBin( self ):
		# Just wanted to double check that iterating the data store directory is working properly, by
		# moving a whole bunch of files at once to the recycle bin
		s = Gaffer.ScriptNode()
		self.setupComparison( s )

		for i in range( 1000 ):
			self.comparisonSetEntry( s, "a%i"%i, IECore.IntData( 7 * i ) )

		s["fileName"].setValue( self.temporaryDirectory() / "test.gfr" )
		self.assertComparisonValid( s )
		s.save()
		self.assertComparisonValid( s )
		self.assertSaved( s )

		for i in range( 1000 ):
			self.comparisonSetEntry( s, "a%i"%i, None )

		self.comparisonSetEntry( s, "b", IECore.IntData( 4 ) )

		self.assertEqual( s["dataStore"]["keys"].getValue(), IECore.StringVectorData( [ "b" ] ) )

		self.assertComparisonValid( s )
		s.save()
		self.assertSaved( s )
		self.assertEqual( len( os.listdir( self.temporaryDirectory() / "test.gfr.dataStore" / ".recycleBin" ) ), 1000 )

	def testNotFound( self ):

		s = Gaffer.ScriptNode()
		s["fileName"].setValue( self.temporaryDirectory() / "test.gfr" )
		s["dataStore"] = Gaffer.DataStore()
		s["dataStore"].setEntry( "a", IECore.IntData( 77 ) )
		s.save()
		del s

		# Test the error we get when the caches are deleted before reloading
		shutil.rmtree( self.temporaryDirectory() / "test.gfr.dataStore" )
		Gaffer.ValuePlug.clearCache()

		s = Gaffer.ScriptNode()
		s["fileName"].setValue( self.temporaryDirectory() / "test.gfr" )
		s.load()

		with self.assertRaisesRegex( IECore.Exception, r'Could not locate data store file .* in .*\.' ) :
			s["dataStore"].getEntry( "a" )

		s["fileName"].setValue( self.temporaryDirectory() / "test2.gfr" )

		with self.assertRaisesRegex( IECore.Exception, 'Unable to save entry "a" on "ScriptNode.dataStore" - no live value, but cannot find on disk in directory ".*".' ) :
			s.save()

	def testSaveFails( self ):

		s = Gaffer.ScriptNode()
		s["fileName"].setValue( self.temporaryDirectory() / "test.gfr" )
		s["dataStore"] = Gaffer.DataStore()
		s["dataStore"].setEntry( "a", IECore.IntData( 77 ) )

		# Add a node that will fail to serialise. Because it is added after the DataStore,
		# the DataStore will be serialised
		s["badSerialise"] = GafferTest.MultiplyNode( "badSerialise", False, True )

		with self.assertRaisesRegex( IECore.Exception, 'Testing failure during serialise' ) :
			s.save()

		# We shouldn't write out data stores if serialisation fails
		self.assertFalse( os.path.exists( self.temporaryDirectory() / "test.gfr.dataStore" ) )

	def testHardLinks( self ):

		# Test that if we hold a data store entry the same through several versions of a file, we
		# keep a link back to the original instead of duplicating the file.
		testValue = IECore.IntVectorData( [i for i in range( 100000 ) ] )
		s = Gaffer.ScriptNode()
		s["dataStore"] = Gaffer.DataStore()
		s["dataStore"].setEntry( "a", testValue )
		s["fileName"].setValue( self.temporaryDirectory() / "file1.gfr" )
		s.save()
		s["fileName"].setValue( self.temporaryDirectory() / "file2.gfr" )
		s.save()
		del s

		s = Gaffer.ScriptNode()
		s["fileName"].setValue( self.temporaryDirectory() / "file2.gfr" )
		s.load()
		s["fileName"].setValue( self.temporaryDirectory() / "file3.gfr" )
		s.save()
		del s

		self.assertEqual( os.stat( self.temporaryDirectory() / "file1.gfr.dataStore" / "2be6e2024a34d8808b87824ac350c907.cob" ).st_nlink, 3 )
		self.assertEqual( os.stat( self.temporaryDirectory() / "file2.gfr.dataStore" / "2be6e2024a34d8808b87824ac350c907.cob" ).st_nlink, 3 )
		self.assertEqual( os.stat( self.temporaryDirectory() / "file3.gfr.dataStore" / "2be6e2024a34d8808b87824ac350c907.cob" ).st_nlink, 3 )

		s = Gaffer.ScriptNode()
		s["fileName"].setValue( self.temporaryDirectory() / "file3.gfr" )
		s.load()
		self.assertEqual( s["dataStore"].getEntry( "a" ), testValue )
		del s

		s = Gaffer.ScriptNode()
		s["fileName"].setValue( self.temporaryDirectory() / "file1.gfr" )
		s.load()
		self.assertEqual( s["dataStore"].getEntry( "a" ), testValue )
		del s

	def testUndo( self ):
		s = Gaffer.ScriptNode()
		s["dataStore"] = Gaffer.DataStore()
		s["dataStore"].setEntry( "a", IECore.IntData( 7 ) )
		self.assertEqual( s["dataStore"].getEntry( "a" ), IECore.IntData( 7 ) )

		s["fileName"].setValue( self.temporaryDirectory() / "source.gfr" )
		s.save()
		del s

		s = Gaffer.ScriptNode()
		s["fileName"].setValue( self.temporaryDirectory() / "source.gfr" )
		s.load()
		s["fileName"].setValue( self.temporaryDirectory() / "test.gfr" )
		self.assertEqual( s["dataStore"].getEntry( "a" ), IECore.IntData( 7 ) )

		with Gaffer.UndoScope( s ) :
			s["dataStore"].setEntry( "a", IECore.IntData( 42 ) )

		self.assertEqual( s["dataStore"].getEntry( "a" ), IECore.IntData( 42 ) )

		s.save()

		s.undo()

		# Test that we can reload the data from disk ( even though it's now coming from
		# the recycle bin )
		Gaffer.ValuePlug.clearCache()

		self.assertEqual( s["dataStore"].getEntry( "a" ), IECore.IntData( 7 ) )

		# Now try saving - we want this to get the hard link back out of the recycle bin,
		# rather than saving a separate copy

		s.save()

		del s

		self.assertEqual( os.stat( self.temporaryDirectory() / "source.gfr.dataStore" / "22b41848d90e4f05d50ab80c68957527.cob" ).st_nlink, 2 )
		self.assertEqual( os.stat( self.temporaryDirectory() / "test.gfr.dataStore" / "22b41848d90e4f05d50ab80c68957527.cob" ).st_nlink, 2 )

	def testManyRecycleBins( self ):

		s = Gaffer.ScriptNode()
		s["counter"] = Gaffer.IntPlug()
		s["dataStore"] = Gaffer.DataStore()

		for i in range( 10 ):
			# Create a data store entry unique to each script we save as
			with Gaffer.UndoScope( s ) :
				s["dataStore"].setEntry( "a%i"%i, IECore.IntData( 1000 + i ) )

			with Gaffer.UndoScope( s ) :
				s["fileName"].setValue( self.temporaryDirectory() / ( "file%i.gfr" % i ) )
			s.save()

			# Change the entry so we move the previous value to the recycle bin
			with Gaffer.UndoScope( s ) :
				s["dataStore"].setEntry( "a%i"%i, IECore.IntData( 2000 + i ) )
			s.save()

		for i in range( 10 ):
			# Each store dir should contain the entries so far, plus a recycle bin
			self.assertEqual( len( os.listdir( self.temporaryDirectory() / ( "file%i.gfr.dataStore" % i ) ) ), 2 + i )
			# Each recycle bin should contain one file
			self.assertEqual( len( os.listdir( self.temporaryDirectory() / ( "file%i.gfr.dataStore" % i ) / ".recycleBin" ) ), 1 )

		# Ensure that we're using the values from disk
		Gaffer.ValuePlug.clearCache()

		# Check the final values
		for i in range( 10 ) :
			self.assertEqual( s["dataStore"].getEntry( "a%i"%i ), IECore.IntData( 2000 + i ) )

		# Run back through the undo stack getting all the values from the recycle bins
		for i in reversed( range( 0, 10 ) ):
			s.undo()

			self.assertEqual( s["dataStore"].getEntry( "a%i"%i ), IECore.IntData( 1000 + i ) )

			s.undo()
			s.undo()

		self.assertEqual( s["dataStore"]["keys"].getValue(), IECore.StringVectorData() )

		# Redo everything
		for i in range( 30 ):
			s.redo()

		self.assertEqual( set( s["dataStore"]["keys"].getValue() ), { "a%i"%i for i in range( 10 ) } )

		for i in range( 10 ) :
			self.assertEqual( s["dataStore"].getEntry( "a%i"%i ), IECore.IntData( 2000 + i ) )

		# Run back through the undo stack getting all the values from the recycle bins, but this
		# time we'll put new actions on the undo stack, forcing clearing of the undo stack


		for i in reversed( range( 0, 10 ) ):
			s.undo()

			self.assertEqual( s["dataStore"].getEntry( "a%i"%i ), IECore.IntData( 1000 + i ) )

			s.undo()

			self.assertTrue( os.path.exists( self.temporaryDirectory() / ( "file%i.gfr.dataStore/.recycleBin" % i ) ) )

			# Make a new edit, then immediately undo it, just to force the undo stack to be cleared
			with Gaffer.UndoScope( s ) :
				s["counter"].setValue( 10 + i )
			s.undo()

			s.undo()
			self.assertFalse( os.path.exists( self.temporaryDirectory() / ( "file%i.gfr.dataStore/.recycleBin" % i ) ) )

		self.assertEqual( s["dataStore"]["keys"].getValue(), IECore.StringVectorData() )

	# We now require that you rename the .dataStore directory to match if you rename a script,
	# so renaming just the script will fail.
	@unittest.expectedFailure
	def testRenameA( self ):
		s = Gaffer.ScriptNode()
		s["dataStore"] = Gaffer.DataStore()
		s["dataStore"].setEntry( "a", IECore.IntData( 7 ) )
		s["fileName"].setValue( self.temporaryDirectory() / "test.gfr" )
		s.save()
		del s

		os.rename( self.temporaryDirectory() / "test.gfr", self.temporaryDirectory() / "renameA.gfr" )

		s = Gaffer.ScriptNode()
		s["fileName"].setValue( self.temporaryDirectory() / "renameA.gfr" )
		s.load()
		self.assertEqual( s["dataStore"].getEntry( "a" ), IECore.IntData( 7 ) )

	def testRenameB( self ):
		s = Gaffer.ScriptNode()
		s["dataStore"] = Gaffer.DataStore()
		s["dataStore"].setEntry( "a", IECore.IntData( 42 ) )
		s["fileName"].setValue( self.temporaryDirectory() / "test.gfr" )
		s.save()
		del s

		os.rename( self.temporaryDirectory() / "test.gfr", self.temporaryDirectory() / "renameB.gfr" )
		os.rename( self.temporaryDirectory() / "test.gfr.dataStore", self.temporaryDirectory() / "renameB.gfr.dataStore" )

		# If we move a file and its data store together, it should be able to find the new data locations when
		# we load.
		s = Gaffer.ScriptNode()
		s["fileName"].setValue( self.temporaryDirectory() / "renameB.gfr" )
		s.load()
		self.assertEqual( s["dataStore"].getEntry( "a" ), IECore.IntData( 42 ) )

	def testCopyPasteWithin( self ):

		app = Gaffer.ApplicationRoot()

		s = Gaffer.ScriptNode()

		app["scripts"]["s"] = s

		s["dataStore"] = Gaffer.DataStore()
		s["dataStore"].setEntry( "a", IECore.IntData( 7 ) )
		s["dataStore"].setEntry( "b", IECore.FloatData( 123.456 ) )
		s["fileName"].setValue( self.temporaryDirectory() / "test.gfr" )

		with self.assertRaisesRegex( IECore.Exception, 'Cannot copy, DataStore "ApplicationRoot.scripts.s.dataStore" is not saved yet.' ) :
			s.copy()

		s.save()

		s.copy()

		s.paste()

		self.assertEqual( s["dataStore"].getEntry( "a" ), IECore.IntData( 7 ) )
		self.assertEqual( s["dataStore"].getEntry( "b" ), IECore.FloatData( 123.456 ) )
		self.assertFalse( s["dataStore"].isLive( "a" ) )
		self.assertFalse( s["dataStore"].isLive( "b" ) )
		self.assertEqual( s["dataStore1"].getEntry( "a" ), IECore.IntData( 7 ) )
		self.assertEqual( s["dataStore1"].getEntry( "b" ), IECore.FloatData( 123.456 ) )
		self.assertFalse( s["dataStore1"].isLive( "a" ) )
		self.assertFalse( s["dataStore1"].isLive( "b" ) )

	def testCopyPasteBetween( self ):

		app = Gaffer.ApplicationRoot()

		s = Gaffer.ScriptNode()

		app["scripts"]["s"] = s

		s["dataStore"] = Gaffer.DataStore()
		s["dataStore"].setEntry( "a", IECore.IntData( 7 ) )
		s["dataStore"].setEntry( "b", IECore.FloatData( 123.456 ) )
		s["fileName"].setValue( self.temporaryDirectory() / "test.gfr" )

		with self.assertRaisesRegex( IECore.Exception, 'Cannot copy, DataStore "ApplicationRoot.scripts.s.dataStore" is not saved yet.' ) :
			s.copy()

		s.save()
		s.copy()
		del s

		t = Gaffer.ScriptNode()
		app["scripts"]["t"] = t
		t.paste()

		self.assertEqual( t["dataStore"].getEntry( "a" ), IECore.IntData( 7 ) )
		self.assertEqual( t["dataStore"].getEntry( "b" ), IECore.FloatData( 123.456 ) )

		t["fileName"].setValue( self.temporaryDirectory() / "copied.gfr" )
		t.save()

		# Check that we find the source files, and link back to them.
		self.assertEqual( os.stat( self.temporaryDirectory() / "copied.gfr.dataStore" / "5f4ab9972edafa975a49cad56ad69070.cob" ).st_nlink, 2 )
		self.assertEqual( os.stat( self.temporaryDirectory() / "copied.gfr.dataStore" / "22b41848d90e4f05d50ab80c68957527.cob" ).st_nlink, 2 )

		del t

		shutil.rmtree( self.temporaryDirectory() / "copied.gfr.dataStore" )

		# Try again, but this time we delete the source files after loading. This could happen if the
		# data stores were managed by another Gaffer session.
		t = Gaffer.ScriptNode()
		app["scripts"]["t"] = t
		t.paste()

		self.assertEqual( t["dataStore"].getEntry( "a" ), IECore.IntData( 7 ) )
		self.assertEqual( t["dataStore"].getEntry( "b" ), IECore.FloatData( 123.456 ) )

		shutil.rmtree( self.temporaryDirectory() / "test.gfr.dataStore" )
		Gaffer.ValuePlug.clearCache()

		# We force loaded the data stores as soon as the paste happened, so the values are safe.
		self.assertEqual( t["dataStore"].getEntry( "a" ), IECore.IntData( 7 ) )
		self.assertEqual( t["dataStore"].getEntry( "b" ), IECore.FloatData( 123.456 ) )

		t["fileName"].setValue( self.temporaryDirectory() / "copied.gfr" )
		t.save()

		# But we can't link any more, since we can't find the sources on disk - but we can still correctly
		# write from the data that was loaded
		self.assertEqual( os.stat( self.temporaryDirectory() / "copied.gfr.dataStore" / "5f4ab9972edafa975a49cad56ad69070.cob" ).st_nlink, 1 )
		self.assertEqual( os.stat( self.temporaryDirectory() / "copied.gfr.dataStore" / "22b41848d90e4f05d50ab80c68957527.cob" ).st_nlink, 1 )

		del t

		# Now that the source data is gone though, trying to paste won't work
		t = Gaffer.ScriptNode()
		app["scripts"]["t"] = t

		with self.assertRaisesRegex( IECore.Exception, "Cannot paste - source file uses data stores which are not accessible, or have been modified." ) :
			t.paste()

	def testReference( self ):

		orig = Gaffer.ScriptNode()
		orig["b"] = Gaffer.Box()
		orig["b"]["dataStore"] = Gaffer.DataStore()
		orig["b"]["dataStore"].setEntry( "a", IECore.StringData( "aa" ) )
		orig["b"]["dataStore"].setEntry( "b", IECore.StringData( "bb" ) )
		orig["b"]["dataStore"].setEntry( "c", IECore.StringData( "cc" ) )

		orig["b"].exportForReference( self.temporaryDirectory() / "ref.grf" )

		# Data is stored with reference
		self.assertEqual( len( os.listdir( self.temporaryDirectory() / "ref.grf.dataStore" ) ), 3 )

		s = Gaffer.ScriptNode()
		s["r"] = Gaffer.Reference()
		s["r"].load( self.temporaryDirectory() / "ref.grf" )

		self.assertEqual( s["r"]["dataStore"].getEntry( "a" ), IECore.StringData( "aa" ) )
		self.assertEqual( s["r"]["dataStore"].getEntry( "b" ), IECore.StringData( "bb" ) )
		self.assertEqual( s["r"]["dataStore"].getEntry( "c" ), IECore.StringData( "cc" ) )

		s["dataStore"] = Gaffer.DataStore()
		s["dataStore"].setEntry( "d", IECore.StringData( "dd" ) )

		s["fileName"].setValue( self.temporaryDirectory() / "test.gfr" )
		s.save()

		del s

		s = Gaffer.ScriptNode()
		s["fileName"].setValue( self.temporaryDirectory() / "test.gfr" )
		s.load()

		self.assertEqual( s["r"]["dataStore"].getEntry( "a" ), IECore.StringData( "aa" ) )
		self.assertEqual( s["r"]["dataStore"].getEntry( "b" ), IECore.StringData( "bb" ) )
		self.assertEqual( s["r"]["dataStore"].getEntry( "c" ), IECore.StringData( "cc" ) )
		self.assertEqual( s["dataStore"].getEntry( "d" ), IECore.StringData( "dd" ) )

		# Check that we're still using the data files from the reference, and we only save out
		# the one data file for the local DataStore
		self.assertEqual( len( os.listdir( self.temporaryDirectory() / "test.gfr.dataStore" ) ), 1 )


		# Delete the reference we exported.
		( self.temporaryDirectory() / "ref.grf" ).unlink()
		shutil.rmtree( self.temporaryDirectory() / "ref.grf.dataStore" )

		Gaffer.ValuePlug.clearCache()

		# Check that the original file is still fine - exporting a reference shouldn't have affected it.

		self.assertEqual( orig["b"]["dataStore"].getEntry( "a" ), IECore.StringData( "aa" ) )
		self.assertEqual( orig["b"]["dataStore"].getEntry( "b" ), IECore.StringData( "bb" ) )
		self.assertEqual( orig["b"]["dataStore"].getEntry( "c" ), IECore.StringData( "cc" ) )

	@unittest.skipIf( GafferTest.TestCase.alternateMount() is None, "Cannot find directory with alternate mount on this OS, can't test linking across different mounts" )
	def testHardLinkFailure( self ):

		s = Gaffer.ScriptNode()
		s["dataStore"] = Gaffer.DataStore()
		s["dataStore"].setEntry( "a", IECore.IntData( 7 ) )
		s["dataStore"].setEntry( "b", IECore.FloatData( 123.456 ) )
		s["dataStore"].setEntry( "c", IECore.StringData( "Hello world" ) )
		s["fileName"].setValue( self.temporaryDirectory() / "test.gfr" )
		s.save()

		s["fileName"].setValue( self.alternateMountTemporaryDirectory() / "test.gfr" )

		# Saving as a new file on a different mount will mean we can't use hardlinks, so we should get a warning.
		with IECore.CapturingMessageHandler() as mh :
			s.save()

		self.assertEqual( len( mh.messages ), 1 )
		self.assertRegex( mh.messages[0].message, 'During saving, could not create hardlink at ".*" pointing to ".*", falling back to copying file.' )

		del s

		Gaffer.ValuePlug.clearCache()

		# But everything should still work

		s = Gaffer.ScriptNode()
		s["fileName"].setValue( self.alternateMountTemporaryDirectory() / "test.gfr" )
		s.load()

		self.assertEqual( s["dataStore"].getEntry( "a" ), IECore.IntData( 7 ) )
		self.assertEqual( s["dataStore"].getEntry( "b" ), IECore.FloatData( 123.456 ) )
		self.assertEqual( s["dataStore"].getEntry( "c" ), IECore.StringData( "Hello world" ) )

	def testDocumentUndoLiveValueWeirdness( self ):

		# Saving flags a value as no longer live, since it can then be read from disk and stored
		# in the regular ValuePlug cache - we don't need to dedicate special memory to storing it.
		# But currently, the undo queue still holds the live value, so undoing can cause a value
		# to become live again, even if that value was previously written to disk.
		# This may be tolerable in a first release, but doesn't feel right long term.
		# The solution may be that saving needs to process the undo queue, and discard any live
		# values that are now found on disk. If we were doing that process, then maybe it would
		# be correct to save all values from the undo queue to disk? ( Any values that are not
		# actually used currently would go in a .recycleBin and be deleted when the ScriptNode
		# is closed ). It could make for a slow save, but in a long paint session, it might be
		# better to use some extra disk space ( temporarily ), rather than running out of memory?

		s = Gaffer.ScriptNode()
		s["fileName"].setValue( self.temporaryDirectory() / "test.gfr" )

		s["dataStore"] = Gaffer.DataStore()
		with Gaffer.UndoScope( s ) :
			s["dataStore"].setEntry( "a", IECore.IntData( 77777 ) )

		self.assertTrue( s["dataStore"].isLive( "a" ) )
		s.save()
		self.assertFalse( s["dataStore"].isLive( "a" ) )
		self.assertEqual( s["dataStore"].getEntry( "a" ), IECore.IntData( 77777 ) )

		with Gaffer.UndoScope( s ) :
			s["dataStore"].setEntry( "a", IECore.IntData( 77778 ) )

		self.assertTrue( s["dataStore"].isLive( "a" ) )
		s.save()
		self.assertFalse( s["dataStore"].isLive( "a" ) )

		s.undo()
		s.undo()
		s.redo()

		self.assertEqual( s["dataStore"].getEntry( "a" ), IECore.IntData( 77777 ) )

		# Ideally, this would probably still be false somehow , since the first save() wrote
		# this value to disk.
		self.assertTrue( s["dataStore"].isLive( "a" ) )

	def testSaveAs( self ):

		# Create an entry with no live value by writing a value to disk and reloading.
		s = Gaffer.ScriptNode()
		s["fileName"].setValue( self.temporaryDirectory() / "test.gfr" )
		s["dataStore"] = Gaffer.DataStore()
		s["dataStore"].setEntry( "a", IECore.IntData( 77777 ) )
		s.save()
		del s

		s = Gaffer.ScriptNode()
		s["fileName"].setValue( self.temporaryDirectory() / "test.gfr" )
		s.load()

		with Gaffer.UndoScope( s ) :
			s["dataStore"].setEntry( "a", IECore.IntData( 77778 ) )

		s.save()
		self.assertFalse( s["dataStore"].isLive( "a" ) )

		# When we save as a new file, we point our data stores to the new data
		# store directory ( but the undo queue also knows to point back to the
		# old filename when necessary to retrieve old values )
		s["fileName"].setValue( self.temporaryDirectory() / "test2.gfr" )
		s.save()

		Gaffer.ValuePlug.clearCache()

		self.assertFalse( s["dataStore"].isLive( "a" ) )
		self.assertEqual( s["dataStore"].getEntry( "a" ), IECore.IntData( 77778 ) )

		s.undo()
		Gaffer.ValuePlug.clearCache()

		# Retrieve value from original files recycle bin
		self.assertFalse( s["dataStore"].isLive( "a" ) )
		self.assertEqual( s["dataStore"].getEntry( "a" ), IECore.IntData( 77777 ) )

		del s

		# Make sure that the up to date values are all stored with the new script though
		shutil.rmtree( self.temporaryDirectory() / "test.gfr.dataStore" )
		Gaffer.ValuePlug.clearCache()

		s = Gaffer.ScriptNode()
		s["fileName"].setValue( self.temporaryDirectory() / "test2.gfr" )
		s.load()
		self.assertFalse( s["dataStore"].isLive( "a" ) )
		self.assertEqual( s["dataStore"].getEntry( "a" ), IECore.IntData( 77778 ) )

	def testDispatch( self ):

		# Dispatch a task that will serialise the environment it finds itself running in.

		outputFile = self.temporaryDirectory() / "outputFile.txt"

		s = Gaffer.ScriptNode()

		s["dataStore"] = Gaffer.DataStore()
		s["dataStore"].setEntry( "a", IECore.StringData( "text from data store" ) )
		s["dataStore"]["selector"].setValue( "a" )

		s["command"] = GafferDispatch.PythonCommand()
		s["command"]["variables"].addChild( Gaffer.NameValuePlug( "testVar", Gaffer.StringPlug( "value", defaultValue = '', ), True, "member0", Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )

		s["expression"] = Gaffer.Expression()
		s["expression"].setExpression( 'parent["command"]["variables"]["member0"]["value"] = parent["dataStore"]["out"]' )

		s["command"]["command"].setValue(
			inspect.cleandoc(
				f"""
				with open( r"{outputFile}", "w" ) as f :
					f.write( variables["testVar"] )
				"""
			)
		)

		s["dispatcher"] = GafferDispatch.LocalDispatcher( jobPool = GafferDispatch.LocalDispatcher.JobPool() )
		s["dispatcher"]["jobsDirectory"].setValue( self.temporaryDirectory() )
		s["dispatcher"]["tasks"][0].setInput( s["command"]["task"] )
		s["dispatcher"]["executeInBackground"].setValue( True )
		s["dispatcher"]["task"].execute()
		s["dispatcher"].jobPool().waitForAll()

		# The dispatch saved out the data correctly
		with open( outputFile, encoding = "utf-8" ) as f :
			self.assertEqual( f.read(), "text from data store" )

		# But this didn't affect the current script, so it still isn't saved.
		with self.assertRaisesRegex( IECore.Exception, 'Cannot copy, DataStore "ScriptNode.dataStore" is not saved yet.' ) :
			s.serialise()

if __name__ == "__main__":
	unittest.main()
