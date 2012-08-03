##########################################################################
#  
#  Copyright (c) 2012, John Haddon. All rights reserved.
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

import IECore

import GafferScene

class SceneTestCase( unittest.TestCase ) :

	def assertSceneValid( self, scenePlug ) :
	
		# check that the root doesn't have any properties it shouldn't
		self.assertEqual( scenePlug.attributes( "/" ), None )
		self.assertEqual( scenePlug.transform( "/" ), IECore.M44f() )
		self.assertEqual( scenePlug.object( "/" ), None )
		
		# then walk the scene to check the bounds
		self.__walkScene( scenePlug, "/" )
		
	def __walkScene( self, scenePlug, scenePath ) :
	
		thisBound = scenePlug.bound( scenePath )
		
		o = scenePlug.object( "/" )
		if isinstance( o, IECore.VisibleRenderable ) :
			 if not thisBound.contains( o.bound() ) :
				self.fail( "Bound %s does not contain object %s at %s" % ( thisBound, o.bound(), scenePath ) )

		unionOfTransformedChildBounds = IECore.Box3f()
		for childName in scenePlug.childNames( scenePath ) :
			
			if scenePath == "/" :
				childPath = scenePath + childName
			else :
				childPath = scenePath + "/" + childName
			
			childBound = scenePlug.bound( childPath )
			childTransform = scenePlug.transform( childPath )
			childBound = childBound.transform( childTransform )
			
			unionOfTransformedChildBounds.extendBy( childBound )
			
			self.__walkScene( scenePlug, childPath )
		
 		if not thisBound.contains( unionOfTransformedChildBounds ) :
			self.fail( "Bound ( %s ) does not contain children ( %s ) at %s" % ( thisBound, unionOfTransformedChildBounds, scenePath ) )
