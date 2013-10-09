##########################################################################
#  
#  Copyright (c) 2011-2012, Image Engine Design Inc. All rights reserved.
#  Copyright (c) 2011-2012, John Haddon. All rights reserved.
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

from __future__ import with_statement

import IECore

import Gaffer
import GafferUI

## A dialogue which allows a user to edit the parameters of an
# IECore.Op instance and then execute it.
class OpDialogue( GafferUI.Dialogue ) :

	## Defines what happens when the op has been successfully executed :
	#
	# FromUserData : Get behaviour from ["UI"]["postExecuteBehaviour"] userData, which should
	#	contain a string value specifying one of the other Enum values. If no userData is found,
	#	it defaults to CloseByDefault.
	# 
	# None : Do nothing. The dialogue stays open.
	#
	# Close : The dialogue is closed.
	#
	# NoneByDefault : The dialogue will remain open by default, but the user can override this.
	#
	# CloseByDefault : The dialogue will be closed by default, but the user can override this.
	PostExecuteBehaviour = IECore.Enum.create( "FromUserData", "None", "Close", "NoneByDefault", "CloseByDefault" )

	def __init__(
		self,
		opInstance,
		title=None,
		sizeMode=GafferUI.Window.SizeMode.Manual,
		postExecuteBehaviour = PostExecuteBehaviour.FromUserData,
		**kw
	) :

		# initialise the dialogue

		if title is None :
			title = IECore.CamelCase.toSpaced( opInstance.typeName() )

		GafferUI.Dialogue.__init__( self, title, sizeMode=sizeMode, **kw )
		
		# decide what we'll do after execution.
		
		if postExecuteBehaviour == self.PostExecuteBehaviour.FromUserData :
			
			postExecuteBehaviour = self.PostExecuteBehaviour.CloseByDefault
			
			d = None
			with IECore.IgnoredExceptions( KeyError ) :
				d = opInstance.userData()["UI"]["postExecuteBehaviour"]
			if d is not None :
				for v in self.PostExecuteBehaviour.values() :
					if str( v ).lower() == d.value.lower() :
						postExecuteBehaviour = v
						break
			else :
				# backwards compatibility with batata
				with IECore.IgnoredExceptions( KeyError ) :
					d = opInstance.userData()["UI"]["closeAfterExecution"]
				if d is not None :
					postExecuteBehaviour = self.PostExecuteBehaviour.Close if d.value else self.PostExecuteBehaviour.None
						
		self.__postExecuteBehaviour = postExecuteBehaviour
		
		# make a node to hold the op and get a ui from it
		
		self.__node = Gaffer.ParameterisedHolderNode()
		self.__node.setParameterised( opInstance )
		nodeUI = GafferUI.NodeUI.create( self.__node )

		# build our main ui
		
		with GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Vertical, spacing=8 ) as column :
		
			GafferUI.Frame( child = nodeUI )
		
			if self.__postExecuteBehaviour in ( self.PostExecuteBehaviour.NoneByDefault, self.PostExecuteBehaviour.CloseByDefault ) :
				with GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal ) :
					self.__keepWindowOpen = GafferUI.BoolWidget(
						"Keep window open",
						self.__postExecuteBehaviour == self.PostExecuteBehaviour.NoneByDefault
					)
		
		self._setWidget( column )
		
		# add buttons
		
		self.__cancelButton = self._addButton( "Cancel" )
		self.__cancelButtonConnection = self.__cancelButton.clickedSignal().connect( Gaffer.WeakMethod( self.__buttonClicked ) )
		
		executeLabel = "OK"
		with IECore.IgnoredExceptions( KeyError ) :
			executeLabel = opInstance.userData()["UI"]["buttonLabel"].value
		self.__executeButton = self._addButton( executeLabel )
		self.__executeButtonConnection = self.__executeButton.clickedSignal().connect( Gaffer.WeakMethod( self.__buttonClicked ) )
		
		self.__opExecutedSignal = Gaffer.Signal1()
					
	## A signal called when the user has pressed the execute button
	# and the Op has been successfully executed. This is passed the
	# result of the execution.
	def opExecutedSignal( self ) :
	
		return self.__opExecutedSignal
	
	## Causes the dialogue to enter a modal state, returning the result
	# of executing the Op, or None if the user cancelled the operation. Any
	# validation or execution errors will be reported to the user and return
	# to the dialogue for them to cancel or try again.
	def waitForResult( self, **kw ) :
	
		# block our button connection so we don't end up executing twice
		with Gaffer.BlockedConnection( self.__executeButtonConnection ) :
		
			while 1 :
				button = self.waitForButton( **kw )					
				if button is self.__executeButton :
					result = self.__execute()
					if result is not None :
						return result
				else :
					return None

	def __execute( self ) :
				
		try :
			
			self.__node.setParameterisedValues()
			result =  self.__node.getParameterised()[0]()
			self.opExecutedSignal()( result )
			
			behaviour = self.__postExecuteBehaviour
			if behaviour in ( behaviour.NoneByDefault, behaviour.CloseByDefault ) :
				behaviour = behaviour.None if self.__keepWindowOpen.getState() else behaviour.Close
				
			if behaviour == behaviour.Close :
				self.close()
			
			return result
			
		except :
			
			GafferUI.ErrorDialogue.displayException( parentWindow=self )
			
			return None
	
	def __buttonClicked( self, button ) :
	
		if button is self.__executeButton :
			self.__execute()
		else :
			self.close()
