##########################################################################
#  
#  Copyright (c) 2011, John Haddon. All rights reserved.
#  Copyright (c) 2011, Image Engine Design Inc. All rights reserved.
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

import os

import IECore

import Gaffer
import GafferUI

class PathWidget( GafferUI.TextWidget ) :

	def __init__( self, path ) :
	
		GafferUI.TextWidget.__init__( self, str( path ) )
		
		self.__keyPressConnection = self.keyPressSignal().connect( Gaffer.WeakMethod( self.__keyPress ) )
		self.__buttonPressConnection = self.buttonPressSignal().connect( Gaffer.WeakMethod( self.__buttonPress ) )
				
		self.__path = path
		self.__pathChangedConnection = self.__path.pathChangedSignal().connect( Gaffer.WeakMethod( self.__pathChanged ) )
		
		self.__textChangedConnection = self.textChangedSignal().connect( Gaffer.WeakMethod( self.__textChanged ) )
	
	def path( self ) :
	
		return self.__path
				
	def __keyPress( self, widget, event ) :
				
		if event.key=="Tab" :

			# do tab completion
			
			position = self.getCursorPosition()

			truncatedPath = self.__path.copy()
			truncatedPath.setFromString( str( truncatedPath )[:position] )
			if len( truncatedPath ) :
				matchStart = truncatedPath[-1]
				del truncatedPath[-1]
			else :
				matchStart = ""
				
			matches = [ x[-1] for x in truncatedPath.children() if x[-1].startswith( matchStart ) ]
			match = os.path.commonprefix( matches )
			
			if match :

				self.__path[:] = truncatedPath[:] + [ match ]
				if len( matches )==1 and not self.__path.isLeaf() :
					text = self.getText()
					if not text.endswith( "/" ) :
						self.setText( text + "/" )
				
				self.setCursorPosition( len( self.getText() ) )
						
			return True
			
		return False
		
	def __buttonPress( self, widget, event ) :
				
		if event.modifiers & event.Modifiers.Control :
		
			# ctrl click
			
			position = self._eventPosition( event )			
			dirPath = self.__path.copy()
			n = os.path.dirname( self.getText()[:position] ) or "/"
			dirPath.setFromString( n )
			
			options = dirPath.children()
			options = [ x[-1] for x in options ]
			
			if len( options ) :
							
				md = IECore.MenuDefinition()
				for o in options :
					md.append( "/" + o,
						IECore.MenuItemDefinition(
							label=o,
							command = IECore.curry( self.__replacePathEntry, len( dirPath ), o )
						)
					)
					
				m = GafferUI.Menu( md )
				m.popup()
			
		return False
		
	def __replacePathEntry( self, position, newEntry ) :
	
		if position==len( self.__path ) :
			self.__path.append( newEntry )
		else :
			self.__path[position] = newEntry
			self.__path.truncateUntilValid()			
	
		if position==len( self.__path )-1 and not self.__path.isLeaf() :
			self.setText( self.getText() + "/" )
				
	def __pathChanged( self, path ) :
	
		self.setText( str( path ) )

	def __textChanged( self, widget ) :
	
		text = self.getText()
		with Gaffer.BlockedConnection( self.__pathChangedConnection ) :
			try :
				self.__path.setFromString( self.getText() )
			except :
				# no need to worry too much - it's up to the user to enter
				# something valid. maybe they'll get it right next time.
				pass
