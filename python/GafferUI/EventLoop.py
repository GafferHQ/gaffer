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

import GafferUI

QtCore = GafferUI._qtImport( "QtCore" )
QtGui = GafferUI._qtImport( "QtGui" )

## This class manages the event loop used to run GafferUI based applications.
## \todo I don't know that this makes sense with the new Qt shit going on
class EventLoop() :

	__qtApplication = QtGui.QApplication( [] )
	__eventLoops = []

	## Starts the event loop, passing control to the UI code. This will return when
	# EventLoop.stop() is called. This may be called recursively.
	@classmethod
	def start( cls ) :
	
		if len( cls.__eventLoops )==0 :
			cls.__eventLoops.append( cls.__qtApplication )
		else :
			cls.__eventLoops.append( QtCore.QEventLoop() )
	
		cls.__eventLoops[-1].exec_()
	
	## Stops the event loop last started using start().
	@classmethod
	def stop( cls ) :
	
		cls.__eventLoops.pop().exit()
	
	## Adds a function to be called when the event loop is idle (has no events
	# remaining to be processed). Returns an id which can be used with removeIdleCallback().
	# If callback returns False then it will be removed automatically after running,
	# if it returns True it will be called again until it returns False, or until
	# removeIdleCallback() is called.
	@staticmethod
	def addIdleCallback( callback ) :
		
		return gobject.idle_add( callback )
	
	## Removes an idle callback previously created with addIdleCallback().
	@staticmethod
	def removeIdleCallback( callbackId ) :
	
		gobject.source_remove( callbackId )
