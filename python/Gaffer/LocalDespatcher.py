##########################################################################
#  
#  Copyright (c) 2013, Image Engine Design Inc. All rights reserved.
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
import IECore

class LocalDespatcher( Gaffer.Despatcher ) :

	__despatcher = None

	def __init__( self ) :

		Gaffer.Despatcher.__init__( self )

	def _doDespatch( self, nodes ) :

		if not nodes :
			return

		script = nodes[0].scriptNode()
		if script is None :
			c = Gaffer.Context()
		else :
			c = script.context()

		taskList = map( lambda n: Gaffer.ExecutableNode.Task(n,c), nodes )

		allTasksAndRequirements = Gaffer.Despatcher._uniqueTasks( taskList )

		for (task,requirements) in allTasksAndRequirements :

			task.node.execute( [ task.context ] )

	def _addPlugs( self, despatcherPlug ) :

		pass

	@staticmethod
	def _singleton():

		if LocalDespatcher.__despatcher is None :

			LocalDespatcher.__despatcher = LocalDespatcher()

		return LocalDespatcher.__despatcher

IECore.registerRunTimeTyped( LocalDespatcher, typeName = "Gaffer::LocalDespatcher" )

Gaffer.Despatcher._registerDespatcher( "local", LocalDespatcher._singleton() )
