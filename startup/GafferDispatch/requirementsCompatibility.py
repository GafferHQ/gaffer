##########################################################################
#
#  Copyright (c) 2015, Image Engine Design Inc. All rights reserved.
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

import Gaffer
import GafferDispatch

def __isPreTasksPlug( plug ) :

	return plug.getName() == "preTasks" and isinstance( plug.parent(), GafferDispatch.TaskNode )

def __preTasksPlugGetItemWrapper( originalGetItem ) :

	def getItem( self, key ) :

		if isinstance( key, str ) and __isPreTasksPlug( self ) :
			if key not in self :
				key = key.replace( "requirement", "preTask" )

		return originalGetItem( self, key )

	return getItem

def __preTasksPlugAddChildWrapper( originalAddChild ) :

	def addChild( self, child ) :

		if __isPreTasksPlug( self ) :
			child.setName( child.getName().replace( "requirement", "preTask" ) )
			if child.__class__ is Gaffer.Plug :
				# Replace ancient plugs from files prior to version 0.15 with proper TaskPlugs.
				child = Gaffer.TaskNode.TaskPlug( child.getName(), child.direction(), child.getFlags() )

		return originalAddChild( self, child )

	return addChild

def __taskNodeGetItemWrapper( originalGetItem ) :

	def getItem( self, key ) :

		key = {
			"requirement" : "task",
			"requirements" : "preTasks",
		}.get( key, key )

		return originalGetItem( self, key )

	return getItem

GafferDispatch.TaskNode.__getitem__ = __taskNodeGetItemWrapper( GafferDispatch.TaskNode.__getitem__ )
Gaffer.ArrayPlug.__getitem__ = __preTasksPlugGetItemWrapper( Gaffer.ArrayPlug.__getitem__ )
Gaffer.ArrayPlug.addChild = __preTasksPlugAddChildWrapper( Gaffer.ArrayPlug.addChild )
GafferDispatch.TaskNode.RequirementPlug = GafferDispatch.TaskNode.TaskPlug
GafferDispatch.TaskNode.requirements = GafferDispatch.TaskNode.preTasks
GafferDispatch.Dispatcher._TaskBatch.requirements = GafferDispatch.Dispatcher._TaskBatch.preTasks
