##########################################################################
#
#  Copyright (c) 2021, Cinesite VFX Ltd. All rights reserved.
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
import imath

import Gaffer
import GafferScene
import GafferSceneTest

def randomName( gen, mnc, mxc ):

	from string import ascii_lowercase

	return ''.join( gen.choice( ascii_lowercase )
		for _ in range( gen.randrange( mnc, mxc ) ) )

class ExistenceQueryTest( GafferSceneTest.SceneTestCase ):

	def testDefault( self ):

		eq = GafferScene.ExistenceQuery()

		self.assertTrue( eq["exists"].getValue() == False )
		self.assertTrue( eq["closestAncestor"].getValue() == "" )

	def testLocationSlashSceneInvalid( self ):

		from random import Random
		from datetime import datetime

		r = Random( datetime.now() )

		name1 = randomName( r, 5, 10 )
		name2 = randomName( r, 5, 10 )

		eq = GafferScene.ExistenceQuery()
		eq["location"].setValue( "/" )

		self.assertFalse( eq["exists"].getValue() )
		self.assertEqual( eq["closestAncestor"].getValue(), "/" )

		eq["location"].setValue( "/" + name1 )

		self.assertFalse( eq["exists"].getValue() )
		self.assertEqual( eq["closestAncestor"].getValue(), "/" )

		eq["location"].setValue( "/" + name1 + "/" + name2 )

		self.assertFalse( eq["exists"].getValue() )
		self.assertEqual( eq["closestAncestor"].getValue(), "/" )

	def testLocationNoSlashSceneInvalid( self ):

		from random import Random
		from datetime import datetime

		r = Random( datetime.now() )

		name1 = randomName( r, 5, 10 )
		name2 = randomName( r, 5, 10 )

		eq = GafferScene.ExistenceQuery()
		eq["location"].setValue( "" )

		self.assertFalse( eq["exists"].getValue() )
		self.assertEqual( eq["closestAncestor"].getValue(), "" )

		eq["location"].setValue( name1 )

		self.assertFalse( eq["exists"].getValue() )
		self.assertEqual( eq["closestAncestor"].getValue(), "/" )

		eq["location"].setValue( name1 + "/" + name2 )

		self.assertFalse( eq["exists"].getValue() )
		self.assertEqual( eq["closestAncestor"].getValue(), "/" )

	def testLocationEmptySceneValid( self ):

		s = GafferScene.Sphere()

		eq = GafferScene.ExistenceQuery()
		eq["scene"].setInput( s["out"] )
		eq["location"].setValue( "" )

		self.assertFalse( eq["exists"].getValue() )
		self.assertEqual( eq["closestAncestor"].getValue(), "" )

	def testLocationSlashSceneValid( self ):

		s = GafferScene.Sphere()

		eq = GafferScene.ExistenceQuery()
		eq["scene"].setInput( s["out"] )
		eq["location"].setValue( "/" )

		self.assertTrue( eq["exists"].getValue() )
		self.assertEqual( eq["closestAncestor"].getValue(), "/" )

	def testLocationNoSlashValid( self ):

		from random import Random
		from datetime import datetime

		r = Random( datetime.now() )

		name1 = randomName( r, 5, 10 )
		name2 = randomName( r, 5, 10 )

		s = GafferScene.Sphere()
		s["name"].setValue( name2 )
		g = GafferScene.Group()
		g["name"].setValue( name1 )
		g["in"][0].setInput( s["out"] )

		eq = GafferScene.ExistenceQuery()
		eq["scene"].setInput( g["out"] )
		eq["location"].setValue( name1 )

		self.assertTrue( eq["exists"].getValue() )
		self.assertEqual( eq["closestAncestor"].getValue(), "/" + name1 )

		eq["location"].setValue( name1 + "/" + name2 )

		self.assertTrue( eq["exists"].getValue() )
		self.assertEqual( eq["closestAncestor"].getValue(), "/" + name1 + "/" + name2 )

	def testLocationSlashValid( self ):

		from random import Random
		from datetime import datetime

		r = Random( datetime.now() )

		name1 = randomName( r, 5, 10 )
		name2 = randomName( r, 5, 10 )

		s = GafferScene.Sphere()
		s["name"].setValue( name2 )
		g = GafferScene.Group()
		g["name"].setValue( name1 )
		g["in"][0].setInput( s["out"] )

		eq = GafferScene.ExistenceQuery()
		eq["scene"].setInput( g["out"] )
		eq["location"].setValue( "/" + name1 )

		self.assertTrue( eq["exists"].getValue() )
		self.assertEqual( eq["closestAncestor"].getValue(), "/" + name1 )

		eq["location"].setValue( "/" + name1 + "/" + name2 )

		self.assertTrue( eq["exists"].getValue() )
		self.assertEqual( eq["closestAncestor"].getValue(), "/" + name1 + "/" + name2 )

	def testLocationNoSlashInValid( self ):

		from random import Random
		from datetime import datetime

		r = Random( datetime.now() )

		name1 = randomName( r, 5, 6 )
		name2 = randomName( r, 5, 6 )
		name3 = randomName( r, 5, 6 )

		s = GafferScene.Sphere()
		s["name"].setValue( name2 )
		g = GafferScene.Group()
		g["name"].setValue( name1 )
		g["in"][0].setInput( s["out"] )

		eq = GafferScene.ExistenceQuery()
		eq["scene"].setInput( g["out"] )
		eq["location"].setValue( name1 + name2 )

		self.assertFalse( eq["exists"].getValue() )
		self.assertEqual( eq["closestAncestor"].getValue(), "/" )

		eq["location"].setValue( name1 + name2 + "/" + name1 + name3 )

		self.assertFalse( eq["exists"].getValue() )
		self.assertEqual( eq["closestAncestor"].getValue(), "/" )

	def testLocationSlashInValid( self ):

		from random import Random
		from datetime import datetime

		r = Random( datetime.now() )

		name1 = randomName( r, 5, 6 )
		name2 = randomName( r, 5, 6 )
		name3 = randomName( r, 5, 6 )

		s = GafferScene.Sphere()
		s["name"].setValue( name2 )
		g = GafferScene.Group()
		g["name"].setValue( name1 )
		g["in"][0].setInput( s["out"] )

		eq = GafferScene.ExistenceQuery()
		eq["scene"].setInput( g["out"] )
		eq["location"].setValue( "/" + name1 + name2 )

		self.assertFalse( eq["exists"].getValue() )
		self.assertEqual( eq["closestAncestor"].getValue(), "/" )

		eq["location"].setValue( "/" + name1 + name2 + "/" + name1 + name3 )

		self.assertFalse( eq["exists"].getValue() )
		self.assertEqual( eq["closestAncestor"].getValue(), "/" )

	def testLocationNoSlashPartial( self ):

		from random import Random
		from datetime import datetime

		r = Random( datetime.now() )

		name1 = randomName( r, 5, 10 )
		name2 = randomName( r, 5, 10 )
		name3 = randomName( r, 2, 4 )

		s = GafferScene.Sphere()
		s["name"].setValue( name2 )
		g = GafferScene.Group()
		g["name"].setValue( name1 )
		g["in"][0].setInput( s["out"] )

		eq = GafferScene.ExistenceQuery()
		eq["scene"].setInput( g["out"] )
		eq["location"].setValue( name1 + "/" + name3 )

		self.assertFalse( eq["exists"].getValue() )
		self.assertEqual( eq["closestAncestor"].getValue(), "/" + name1 )

		eq["location"].setValue( name1 + "/" + name2 + "/" + name3 )

		self.assertFalse( eq["exists"].getValue() )
		self.assertEqual( eq["closestAncestor"].getValue(), "/" + name1 + "/" + name2 )

	def testLocationSlashPartial( self ):

		from random import Random
		from datetime import datetime

		r = Random( datetime.now() )

		name1 = randomName( r, 5, 10 )
		name2 = randomName( r, 5, 10 )
		name3 = randomName( r, 2, 4 )

		s = GafferScene.Sphere()
		s["name"].setValue( name2 )
		g = GafferScene.Group()
		g["name"].setValue( name1 )
		g["in"][0].setInput( s["out"] )

		eq = GafferScene.ExistenceQuery()
		eq["scene"].setInput( g["out"] )
		eq["location"].setValue( "/" + name1 + "/" + name3 )

		self.assertFalse( eq["exists"].getValue() )
		self.assertEqual( eq["closestAncestor"].getValue(), "/" + name1)

		eq["location"].setValue( "/" + name1 + "/" + name2 + "/" + name3 )

		self.assertFalse( eq["exists"].getValue() )
		self.assertEqual( eq["closestAncestor"].getValue(), "/" + name1 + "/" + name2 )

	def testEmptyLocationThenMissingLocation( self ) :

		p = GafferScene.Plane()
		q = GafferScene.ExistenceQuery()
		q["scene"].setInput( p["out"] )
		self.assertEqual( q["closestAncestor"].getValue(), "" )

		q["location"].setValue( "/iDontExist" )
		self.assertEqual( q["closestAncestor"].getValue(), "/" )

if __name__ == "__main__":
	unittest.main()
