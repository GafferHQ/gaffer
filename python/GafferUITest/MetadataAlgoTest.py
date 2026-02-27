##########################################################################
#
#  Copyright (c) 2026, Cinesite VFX Ltd. All rights reserved.
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
import GafferUITest

class MetadataAlgoTest( GafferUITest.TestCase ) :

	# We run this Gaffer.MetadataAlgo test as a GafferUITest in order for the
	# "ui:childNodesAreViewable" metadata registrations to exist as they are registered
	# in GafferUI.
	def testFirstViewableWithDefaultMetadata( self ) :

		s = Gaffer.ScriptNode()
		s["b"] = Gaffer.Box()
		s["b"]["e"] = Gaffer.EditScope()
		s["b"]["e"]["b"] = Gaffer.Box()
		s["b"]["e"]["b"]["a"] = GafferTest.AddNode()

		self.assertTrue( Gaffer.Metadata.value( s, "ui:childNodesAreViewable" ) )
		self.assertTrue( Gaffer.Metadata.value( s["b"], "ui:childNodesAreViewable" ) )
		self.assertTrue( Gaffer.Metadata.value( s["b"]["e"], "ui:childNodesAreViewable" ) )
		self.assertTrue( Gaffer.Metadata.value( s["b"]["e"]["b"], "ui:childNodesAreViewable" ) )

		self.assertEqual( Gaffer.MetadataAlgo.firstViewableNode( s["b"] ), s["b"] )
		self.assertEqual( Gaffer.MetadataAlgo.firstViewableNode( s["b"]["e"] ), s["b"]["e"] )
		self.assertEqual( Gaffer.MetadataAlgo.firstViewableNode( s["b"]["e"]["b"] ), s["b"]["e"]["b"] )
		self.assertEqual( Gaffer.MetadataAlgo.firstViewableNode( s["b"]["e"]["b"]["a"] ), s["b"]["e"]["b"]["a"] )
		self.assertEqual( Gaffer.MetadataAlgo.firstViewableNode( s["b"]["e"]["b"]["a"]["op1"] ), s["b"]["e"]["b"]["a"] )

		self.assertEqual( Gaffer.MetadataAlgo.firstViewableAncestor( s["b"], Gaffer.Box ), s["b"] )
		self.assertEqual( Gaffer.MetadataAlgo.firstViewableAncestor( s["b"]["e"], Gaffer.Box ), s["b"]["e"] )
		self.assertEqual( Gaffer.MetadataAlgo.firstViewableAncestor( s["b"]["e"]["b"], Gaffer.Box ), s["b"]["e"]["b"] )
		self.assertEqual( Gaffer.MetadataAlgo.firstViewableAncestor( s["b"]["e"]["b"], Gaffer.EditScope ), s["b"]["e"] )
		self.assertEqual( Gaffer.MetadataAlgo.firstViewableAncestor( s["b"]["e"]["b"]["a"], Gaffer.Node ), s["b"]["e"]["b"]["a"] )
		self.assertEqual( Gaffer.MetadataAlgo.firstViewableAncestor( s["b"]["e"]["b"]["a"], Gaffer.Box ), s["b"]["e"]["b"] )
		self.assertEqual( Gaffer.MetadataAlgo.firstViewableAncestor( s["b"]["e"]["b"]["a"], Gaffer.EditScope ), s["b"]["e"] )
		self.assertEqual( Gaffer.MetadataAlgo.firstViewableAncestor( s["b"]["e"]["b"]["a"]["op1"], Gaffer.Node ), s["b"]["e"]["b"]["a"] )
		self.assertEqual( Gaffer.MetadataAlgo.firstViewableAncestor( s["b"]["e"]["b"]["a"]["op1"], Gaffer.Plug ), s["b"]["e"]["b"]["a"]["op1"] )

		Gaffer.Metadata.registerValue( s["b"], "ui:childNodesAreViewable", False )
		# Although children of `s["b"]` have "ui:childNodesAreViewable" metadata registrations
		# making their children viewable, `s["b"]` is considered the first viewable as it
		# doesn't have viewable children.
		self.assertEqual( Gaffer.MetadataAlgo.firstViewableNode( s["b"]["e"] ), s["b"] )
		self.assertEqual( Gaffer.MetadataAlgo.firstViewableNode( s["b"]["e"]["b"]["a"]["op1"] ), s["b"] )

		self.assertEqual( Gaffer.MetadataAlgo.firstViewableAncestor( s["b"]["e"], Gaffer.Box ), s["b"] )
		self.assertEqual( Gaffer.MetadataAlgo.firstViewableAncestor( s["b"]["e"]["b"]["a"]["op1"], Gaffer.Box ), s["b"] )
		self.assertEqual( Gaffer.MetadataAlgo.firstViewableAncestor( s["b"]["e"]["b"]["a"]["op1"], Gaffer.Node ), s["b"] )

		# Registering `"ui:childNodesAreViewable", None` here will cause us to fall back to the
		# legacy "graphEditor:childrenViewable" metadata, which does define the children of
		# `s["b"]` as viewable.
		Gaffer.Metadata.registerValue( s["b"], "ui:childNodesAreViewable", None )
		self.assertTrue( Gaffer.Metadata.value( s["b"], "graphEditor:childrenViewable" ) )
		self.assertEqual( Gaffer.MetadataAlgo.firstViewableNode( s["b"]["e"] ), s["b"]["e"] )
		self.assertEqual( Gaffer.MetadataAlgo.firstViewableNode( s["b"]["e"]["b"]["a"]["op1"] ), s["b"]["e"]["b"]["a"] )

		self.assertEqual( Gaffer.MetadataAlgo.firstViewableAncestor( s["b"]["e"], Gaffer.Box ), s["b"]["e"] )
		self.assertEqual( Gaffer.MetadataAlgo.firstViewableAncestor( s["b"]["e"]["b"]["a"]["op1"], Gaffer.Box ), s["b"]["e"]["b"] )
		self.assertEqual( Gaffer.MetadataAlgo.firstViewableAncestor( s["b"]["e"]["b"]["a"]["op1"], Gaffer.Node ), s["b"]["e"]["b"]["a"] )

		Gaffer.Metadata.registerValue( s["b"], "graphEditor:childrenViewable", False )
		self.assertEqual( Gaffer.MetadataAlgo.firstViewableNode( s["b"]["e"] ), s["b"] )
		self.assertEqual( Gaffer.MetadataAlgo.firstViewableNode( s["b"]["e"]["b"]["a"]["op1"] ), s["b"] )

		self.assertEqual( Gaffer.MetadataAlgo.firstViewableAncestor( s["b"]["e"], Gaffer.Box ), s["b"] )
		self.assertEqual( Gaffer.MetadataAlgo.firstViewableAncestor( s["b"]["e"]["b"]["a"]["op1"], Gaffer.Box ), s["b"] )
		self.assertEqual( Gaffer.MetadataAlgo.firstViewableAncestor( s["b"]["e"]["b"]["a"]["op1"], Gaffer.Node ), s["b"] )

		# Registering `"graphEditor:childrenViewable", None` here will cause us to no
		# longer fall back to the legacy metadata, and resume our default state, which
		# leaves the children of `s["b"]` as non-viewable.
		Gaffer.Metadata.registerValue( s["b"], "graphEditor:childrenViewable", None )
		self.assertEqual( Gaffer.MetadataAlgo.firstViewableNode( s["b"]["e"] ), s["b"] )
		self.assertEqual( Gaffer.MetadataAlgo.firstViewableNode( s["b"]["e"]["b"]["a"]["op1"] ), s["b"] )

		self.assertEqual( Gaffer.MetadataAlgo.firstViewableAncestor( s["b"]["e"], Gaffer.Box ), s["b"] )
		self.assertEqual( Gaffer.MetadataAlgo.firstViewableAncestor( s["b"]["e"]["b"]["a"]["op1"], Gaffer.Box ), s["b"] )
		self.assertEqual( Gaffer.MetadataAlgo.firstViewableAncestor( s["b"]["e"]["b"]["a"]["op1"], Gaffer.Node ), s["b"] )

if __name__ == "__main__":
	unittest.main()
