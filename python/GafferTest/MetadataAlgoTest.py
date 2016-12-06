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

import unittest

import Gaffer
import GafferTest

class MetadataAlgoTest( GafferTest.TestCase ) :

	def testReadOnly( self ) :

		n = GafferTest.AddNode()

		self.assertEqual( Gaffer.MetadataAlgo.getReadOnly( n ), False )
		self.assertEqual( Gaffer.MetadataAlgo.getReadOnly( n["op1"] ), False )
		self.assertEqual( Gaffer.MetadataAlgo.readOnly( n ), False )
		self.assertEqual( Gaffer.MetadataAlgo.readOnly( n["op1"] ), False )

		Gaffer.MetadataAlgo.setReadOnly( n["op1"], True )

		self.assertEqual( Gaffer.MetadataAlgo.getReadOnly( n ), False )
		self.assertEqual( Gaffer.MetadataAlgo.getReadOnly( n["op1"] ), True )
		self.assertEqual( Gaffer.MetadataAlgo.readOnly( n ), False )
		self.assertEqual( Gaffer.MetadataAlgo.readOnly( n["op1"] ), True )

		Gaffer.MetadataAlgo.setReadOnly( n, True )

		self.assertEqual( Gaffer.MetadataAlgo.getReadOnly( n ), True )
		self.assertEqual( Gaffer.MetadataAlgo.getReadOnly( n["op1"] ), True )
		self.assertEqual( Gaffer.MetadataAlgo.readOnly( n ), True )
		self.assertEqual( Gaffer.MetadataAlgo.readOnly( n["op1"] ), True )

		Gaffer.MetadataAlgo.setReadOnly( n["op1"], False )

		self.assertEqual( Gaffer.MetadataAlgo.getReadOnly( n ), True )
		self.assertEqual( Gaffer.MetadataAlgo.getReadOnly( n["op1"] ), False )
		self.assertEqual( Gaffer.MetadataAlgo.readOnly( n ), True )
		self.assertEqual( Gaffer.MetadataAlgo.readOnly( n["op1"] ), True )

	def testAffected( self ) :

		n = GafferTest.CompoundPlugNode()

		affected = []
		ancestorAffected = []
		childAffected = []
		def plugValueChanged( nodeTypeId, plugPath, key, plug ) :
			affected.append( Gaffer.MetadataAlgo.affectedByChange( n["p"]["s"], nodeTypeId, plugPath, plug ) )
			ancestorAffected.append( Gaffer.MetadataAlgo.ancestorAffectedByChange( n["p"]["s"], nodeTypeId, plugPath, plug ) )
			childAffected.append( Gaffer.MetadataAlgo.childAffectedByChange( n["p"], nodeTypeId, plugPath, plug ) )

		c = Gaffer.Metadata.plugValueChangedSignal().connect( plugValueChanged )

		Gaffer.Metadata.registerValue( Gaffer.Node, "user", "test", 1 )
		self.assertEqual( affected, [ False ] )
		self.assertEqual( ancestorAffected, [ False ] )
		self.assertEqual( childAffected, [ False ] )

		Gaffer.Metadata.registerValue( GafferTest.SphereNode, "p.s", "test", 1 )
		self.assertEqual( affected, [ False, False ] )
		self.assertEqual( ancestorAffected, [ False, False ] )
		self.assertEqual( childAffected, [ False, False ] )

		Gaffer.Metadata.registerValue( GafferTest.CompoundPlugNode, "p.s", "test", 1 )
		self.assertEqual( affected, [ False, False, True ] )
		self.assertEqual( ancestorAffected, [ False, False, False ] )
		self.assertEqual( childAffected, [ False, False, True ] )

		Gaffer.Metadata.registerValue( GafferTest.CompoundPlugNode, "p", "test", 2 )
		self.assertEqual( affected, [ False, False, True, False ] )
		self.assertEqual( ancestorAffected, [ False, False, False, True ] )
		self.assertEqual( childAffected, [ False, False, True, False ] )

		del affected[:]
		del ancestorAffected[:]
		del childAffected[:]

		Gaffer.Metadata.registerValue( n["user"], "test", 3 )
		self.assertEqual( affected, [ False ] )
		self.assertEqual( ancestorAffected, [ False ] )
		self.assertEqual( childAffected, [ False ] )

		Gaffer.Metadata.registerValue( n["p"]["s"], "test", 4 )
		self.assertEqual( affected, [ False, True ] )
		self.assertEqual( ancestorAffected, [ False, False ] )
		self.assertEqual( childAffected, [ False, True ] )

		Gaffer.Metadata.registerValue( n["p"], "test", 5 )
		self.assertEqual( affected, [ False, True, False ] )
		self.assertEqual( ancestorAffected, [ False, False, True ] )
		self.assertEqual( childAffected, [ False, True, False ] )

	def testNodeAffected( self ) :

		n = GafferTest.CompoundPlugNode()

		affected = []
		def nodeValueChanged( nodeTypeId, key, node ) :
			affected.append( Gaffer.MetadataAlgo.affectedByChange( n, nodeTypeId, node ) )

		c = Gaffer.Metadata.nodeValueChangedSignal().connect( nodeValueChanged )

		Gaffer.Metadata.registerValue( Gaffer.Node, "metadataAlgoTest", 1 )
		self.assertEqual( affected, [ True ] )

		Gaffer.Metadata.registerValue( GafferTest.AddNode, "metadataAlgoTest", 2 )
		self.assertEqual( affected, [ True, False ] )

		Gaffer.Metadata.registerValue( n, "metadataAlgoTest", 3 )
		self.assertEqual( affected, [ True, False, True ] )

		a = GafferTest.AddNode()
		Gaffer.Metadata.registerValue( a, "metadataAlgoTest", 4 )
		self.assertEqual( affected, [ True, False, True, False ] )

	def tearDown( self ) :

		for n in ( Gaffer.Node, GafferTest.AddNode ) :
			Gaffer.Metadata.deregisterValue( n, "metadataAlgoTest" )

if __name__ == "__main__":
	unittest.main()
