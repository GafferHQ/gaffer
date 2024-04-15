##########################################################################
#
#  Copyright (c) 2020, Image Engine Design Inc. All rights reserved.
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

import imath
import inspect
import unittest
import os
import subprocess
import threading

import IECore

import Gaffer
import GafferScene
import GafferSceneTest

class UnencapsulateTest( GafferSceneTest.SceneTestCase ) :

	def test( self ) :

		# - groupA
		#    - group1
		#       - sphere
		#       - cube
		#    - group2
		#       - sphere
		#       - cube
		#       - sometimesCube
		#    - group3
		#       - sphere
		#       - cube
		#    - group4
		#       - sphere
		#       - cube

		box = Gaffer.Node()

		box["sphere"] = GafferScene.Sphere()
		box["sphere"]["sets"].setValue( "sphereSet" )

		box["cube"] = GafferScene.Cube()
		box["cube"]["sets"].setValue( "cubeSet" )

		box["sometimesCube"] = GafferScene.Cube()
		box["sometimesCube"]["name"].setValue( "sometimesCube" )
		box["sometimesCube"]["sets"].setValue( "cubeSet" )

		box["group"] = GafferScene.Group()
		box["group"]["in"][0].setInput( box["sphere"]["out"] )
		box["group"]["in"][1].setInput( box["cube"]["out"] )
		box["group"]["in"][1].setInput( box["sometimesCube"]["out"] )

		box["e"] = Gaffer.Expression()
		box["e"].setExpression( inspect.cleandoc(
			"""
			n = context["collect:rootName"]
			i = int( n[-1] ) - 1
			parent["sphere"]["radius"] = 1 + i * 0.1
			parent["sphere"]["transform"]["translate"] = imath.V3f( 1 + i, 0, 0 )
			parent["cube"]["transform"]["translate"] = imath.V3f( 0, 1 + i, 0 )
			parent["sometimesCube"]["enabled"] = n == "group2"
			parent["group"]["transform"]["translate"] = imath.V3f( 0, 0, 1 + i )
			"""
		) )


		collect = GafferScene.CollectScenes()
		collect["in"].setInput( box["group"]["out"] )
		collect["rootNames"].setValue( IECore.StringVectorData( [ "group1", "group2", "group3", "group4" ] ) )
		collect["sourceRoot"].setValue( "/group" )

		groupA = GafferScene.Group()
		groupA["name"].setValue( "groupA" )
		groupA["in"][0].setInput( collect["out"] )

		encapsulateFilter = GafferScene.PathFilter()
		encapsulateFilter["paths"].setValue( IECore.StringVectorData( [ "/groupA/*" ] ) )

		encapsulateCollect = GafferScene.Encapsulate()
		encapsulateCollect["in"].setInput( groupA["out"] )
		encapsulateCollect["filter"].setInput( encapsulateFilter["out"] )


		preEncapsulateFilter = GafferScene.PathFilter()
		preEncapsulateFilter["paths"].setValue( IECore.StringVectorData( [ "/group" ] ) )

		preEncapsulate = GafferScene.Encapsulate()
		preEncapsulate["in"].setInput( box["group"]["out"] )
		preEncapsulate["filter"].setInput( preEncapsulateFilter["out"] )

		collectEncapsulate = GafferScene.CollectScenes()
		collectEncapsulate["in"].setInput( preEncapsulate["out"] )
		collectEncapsulate["rootNames"].setValue( IECore.StringVectorData( [ "group1", "group2", "group3", "group4" ] ) )
		collectEncapsulate["sourceRoot"].setValue( "/group" )

		collectEncapsulateGroup = GafferScene.Group()
		collectEncapsulateGroup["name"].setValue( "groupA" )
		collectEncapsulateGroup["in"][0].setInput( collectEncapsulate["out"] )

		unencapsulateFilter = GafferScene.PathFilter()

		unencapsulate1 = GafferScene.Unencapsulate()
		unencapsulate1["in"].setInput( encapsulateCollect["out"] )
		unencapsulate1["filter"].setInput( unencapsulateFilter["out"] )

		unencapsulate2 = GafferScene.Unencapsulate()
		unencapsulate2["in"].setInput( collectEncapsulateGroup["out"] )
		unencapsulate2["filter"].setInput( unencapsulateFilter["out"] )


		# We can reverse the encapsulate by unencapsulating everything
		unencapsulateFilter["paths"].setValue( IECore.StringVectorData( [ "..." ] ) )
		self.assertScenesEqual( groupA["out"], unencapsulate1["out"] )

		# Unencapsulate should work the same whether the capsules come from before or after the collect
		self.assertScenesEqual( unencapsulate1["out"], unencapsulate2["out"] )

		# Or just unencapsulate one thing
		unencapsulateFilter["paths"].setValue( IECore.StringVectorData( [ "/groupA/group3" ] ) )
		self.assertScenesEqual( encapsulateCollect["out"], unencapsulate1["out"], pathsToPrune = [ "/groupA/group3" ] )
		self.assertScenesEqual( groupA["out"], unencapsulate1["out"],
			pathsToPrune = [ "/groupA/group1", "/groupA/group2", "/groupA/group4" ] )

		# Whichever place we encapsulate, we still get the same results, except that the capsule objects themselves
		# which weren't encapsulated will appear different ( because they were computed in different places, and
		# reference different source plugs
		self.assertScenesEqual( unencapsulate1["out"], unencapsulate2["out"], checks = self.allSceneChecks - { "object" } )
		self.assertScenesEqual( unencapsulate1["out"], unencapsulate2["out"], pathsToPrune = [ "/groupA/group1", "/groupA/group2", "/groupA/group4" ] )


		unencapsulateFilter["paths"].setValue( IECore.StringVectorData( [ "..." ] ) )


		# Test modifying the hierarchy after making capsules by duplicating a location

		duplicate = GafferScene.Duplicate()
		duplicate["target"].setValue( "/groupA/group3" )
		duplicate["in"].setInput( collectEncapsulateGroup["out"] )

		unencapsulateDuplicated = GafferScene.Unencapsulate()
		unencapsulateDuplicated["in"].setInput( duplicate["out"] )
		unencapsulateDuplicated["filter"].setInput( unencapsulateFilter["out"] )

		# This copies group3 as group5
		self.assertEqual(
			unencapsulateDuplicated["out"].fullTransform( "/groupA/group5/sphere" ),
			groupA["out"].fullTransform( "/groupA/group3/sphere" )
		)
		# Sanity check that groups do have unique transforms
		self.assertNotEqual(
			unencapsulateDuplicated["out"].fullTransform( "/groupA/group5/sphere" ),
			groupA["out"].fullTransform( "/groupA/group4/sphere" )
		)

		# This should be same result as copying group3 to group5 without any encapsulation
		preDuplicate = GafferScene.Duplicate()
		preDuplicate["target"].setValue( "/groupA/group3" )
		preDuplicate["in"].setInput( groupA["out"] )

		self.assertScenesEqual( unencapsulateDuplicated["out"], preDuplicate["out"] )


		# Some tests where we merge an extra location into the scene amongst the capsules,
		# which should give the same result whether it's done before or after unencapsulating
		extraSphere = GafferScene.Sphere()
		extraSphere["name"].setValue( "extra" )
		extraSphere["sets"].setValue( "sphereSet" )

		extraSpherePostParent = GafferScene.Parent()
		extraSpherePostParent["in"].setInput( unencapsulate2["out"] )
		extraSpherePostParent["children"][0].setInput( extraSphere["out"] )


		extraSpherePreParent = GafferScene.Parent()
		extraSpherePreParent["in"].setInput( collectEncapsulateGroup["out"] )
		extraSpherePreParent["children"][0].setInput( extraSphere["out"] )

		unencapsulateAfter = GafferScene.Unencapsulate()
		unencapsulateAfter["in"].setInput( extraSpherePreParent["out"] )
		unencapsulateAfter["filter"].setInput( unencapsulateFilter["out"] )

		# Test parenting in a sphere at a the same level as a capsule
		extraSpherePostParent["parent"].setValue( "/groupA" )
		extraSpherePreParent["parent"].setValue( "/groupA" )
		self.assertScenesEqual( extraSpherePostParent["out"], unencapsulateAfter["out"], checks = self.allSceneChecks - { "childNames" } )

		# Test a weird case: parenting the sphere under a capsule, so that when the capsule is expanded,
		# it gets merged with the children of the capsule.  It's arguable that this shouldn't need to
		# work, and maybe there would be some extra optimizations available if it wasn't allowed, but for
		# the moment, it works
		extraSpherePostParent["parent"].setValue( "/groupA/group2" )
		extraSpherePreParent["parent"].setValue( "/groupA/group2" )
		self.assertScenesEqual( extraSpherePostParent["out"], unencapsulateAfter["out"], checks = self.allSceneChecks - { "childNames" } )


	def testRootObject( self ) :

		sphere = GafferScene.Sphere()
		sphere["radius"].setValue( 42 )

		f = GafferScene.PathFilter()
		f["paths"].setValue( IECore.StringVectorData( [ "/sphere" ] ) )

		encapsulate= GafferScene.Encapsulate()
		encapsulate["in"].setInput( sphere["out"] )
		encapsulate["filter"].setInput( f["out"] )

		unencapsulate = GafferScene.Unencapsulate()
		unencapsulate["in"].setInput( encapsulate["out"] )
		unencapsulate["filter"].setInput( f["out"] )

		# Test unencapsulating the object at the root of the capsule
		self.assertScenesEqual( sphere["out"], unencapsulate["out"] )

	def testNoUnwantedCancellation( self ) :

		sphere = GafferScene.Sphere()

		sphereFilter = GafferScene.PathFilter()
		sphereFilter["paths"].setValue( IECore.StringVectorData( [ "/sphere" ] ) )

		encapsulate = GafferScene.Encapsulate()
		encapsulate["in"].setInput( sphere["out"] )
		encapsulate["filter"].setInput( sphereFilter["out"] )

		unencapsulate = GafferScene.Unencapsulate()
		unencapsulate["in"].setInput( encapsulate["out"] )
		unencapsulate["filter"].setInput( sphereFilter["out"] )

		# Generate (and cache) the capsule in a context where
		# a canceller is present.

		context = Gaffer.Context()
		canceller = IECore.Canceller()

		with Gaffer.Context( context, canceller ) :
			capsule = encapsulate["out"].object( "/sphere" )

		# That cached capsule must be usable by a new client,
		# completely independent of the previous canceller.

		canceller.cancel()

		with context :
			self.assertScenesEqual( sphere["out"], unencapsulate["out"] )

	def testCancelUnencapsulation( self ) :

		script = Gaffer.ScriptNode()

		script["sphere"] = GafferScene.Sphere()

		script["standardAttributes"] = GafferScene.StandardAttributes()
		script["standardAttributes"]["in"].setInput( script["sphere"]["out"] )

		UnencapsulateTest.expressionStartedCondition = threading.Condition()

		script["displayColorExpression"] = Gaffer.Expression()
		script["displayColorExpression"].setExpression( inspect.cleandoc(
			"""
			# Let the test know the expression has started running.
			import GafferSceneTest
			with GafferSceneTest.UnencapsulateTest.expressionStartedCondition :
				GafferSceneTest.UnencapsulateTest.expressionStartedCondition.notify()

			# And loop forever unless the compute has been cancelled.
			while True :
				IECore.Canceller.check( context.canceller() )

			parent["standardAttributes"]["attributes"]["displayColor"] = imath.Color3f( 1, 2, 3)
			"""
		) )

		script["group"] = GafferScene.Group()
		script["group"]["in"][0].setInput( script["standardAttributes"]["out"] )

		script["groupFilter"] = GafferScene.PathFilter()
		script["groupFilter"]["paths"].setValue( IECore.StringVectorData( [ "/group" ] ) )

		script["encapsulate"] = GafferScene.Encapsulate()
		script["encapsulate"]["in"].setInput( script["group"]["out"] )
		script["encapsulate"]["filter"].setInput( script["groupFilter"]["out"] )

		script["unencapsulate"] = GafferScene.Unencapsulate()
		script["unencapsulate"]["in"].setInput( script["encapsulate"]["out"] )
		script["unencapsulate"]["filter"].setInput( script["groupFilter"]["out"] )


		# Generate (and cache) the capsule in a context where
		# a canceller isn't present.

		context = Gaffer.Context()
		with context :
			self.assertIsInstance(
				script["encapsulate"]["out"].object( "/group" ),
				GafferScene.Capsule
			)

		# A new client must be able to cancel the unencapsulation
		# process using a new canceller.

		with context :

			# Launch compute in background and wait for the expression
			# from the capsule to start executing.
			backgroundTask = Gaffer.ParallelAlgo.callOnBackgroundThread(
				script["encapsulate"]["out"],
				lambda : script["unencapsulate"]["out"].attributes( "/group/sphere" )
			)
			with UnencapsulateTest.expressionStartedCondition :
				UnencapsulateTest.expressionStartedCondition.wait()

			# Check that we can cancel the compute.
			backgroundTask.cancelAndWait()
			self.assertEqual( backgroundTask.status(), backgroundTask.Status.Cancelled )

if __name__ == "__main__":
	unittest.main()
