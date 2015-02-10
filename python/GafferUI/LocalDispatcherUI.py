##########################################################################
#
#  Copyright (c) 2014, Image Engine Design Inc. All rights reserved.
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

import weakref

import IECore

import Gaffer
import GafferUI

QtCore = GafferUI._qtImport( "QtCore" )
QtGui = GafferUI._qtImport( "QtGui" )

Gaffer.Metadata.registerNode(

	Gaffer.LocalDispatcher,

	"description",
	"""
	Schedules execution of task graphs on the local machine. Tasks
	may be dispatched in the background to keep the UI responsive.
	""",

	plugs = {

		"executeInBackground" : (

			"description",
			"""
			Executes the dispatched tasks in separate processes via a
			background thread. Foreground execution may still be forced
			for specific nodes using the dispatcher.local.executeInForeground
			plug on the node itself.
			""",

		),

		"ignoreScriptLoadErrors" : (

			"description",
			"""
			Ignores errors loading the script when executing in the background.
			This is not recommended - fix the problem instead.
			""",

		)

	}

)

Gaffer.Metadata.registerPlugDescription( Gaffer.ExecutableNode, "dispatcher.local", "Settings used by the local dispatcher." )
Gaffer.Metadata.registerPlugDescription( Gaffer.ExecutableNode, "dispatcher.local.executeInForeground", "Forces the tasks from this node (and all preceding tasks) to execute on the current thread." )

##########################################################################
# Public functions
##########################################################################

def appendMenuDefinitions( menuDefinition, prefix="" ) :
	
	menuDefinition.append( prefix + "/View Local Jobs", { "command" : __showLocalDispatcherWindow } )

##################################################################################
# Dispatcher Window
##################################################################################

class _LocalJobsPath( Gaffer.Path ) :
	
	def __init__( self, jobPool, job = None, path = None, root = "/" ) :
		
		Gaffer.Path.__init__( self, path = path, root = root )
		
		self.__jobPool = jobPool
		self.__job = job
	
	def copy( self ) :
		
		c = self.__class__( self.__jobPool, self.__job )
		
		return c
	
	def info( self ) :
		
		result = Gaffer.Path.info( self )
		
		if result is not None and self.__job is not None :
			
			if self.__job.failed() :
				result["localDispatcher:status"] = "Failed"
			elif self.__job.killed() :
				result["localDispatcher:status"] = "Killed"
			else :
				result["localDispatcher:status"] = "Running"
			
			result["localDispatcher:id"] = self.__job.id()
			result["localDispatcher:jobName"] = self.__job.name()
			result["localDispatcher:directory"] = self.__job.directory()
			stats = self.__job.statistics()
			result["localDispatcher:cpu"] = "{0:.2f} %".format( stats["pcpu"] ) if "pcpu" in stats.keys() else "N/A"
			result["localDispatcher:memory"] = "{0:.2f} GB".format( stats["rss"] / 1024.0  / 1024.0 ) if "rss" in stats.keys() else "N/A"
		
		return result
	
	def job( self ) :
		
		return self.__job
	
	def jobPool( self ) :
		
		return self.__jobPool
	
	def isLeaf( self ) :
		
		return len( self )
	
	def _children( self ) :
		
		if self.isLeaf() :
			return []
		
		result = []
		jobs = self.__jobPool.jobs() + self.__jobPool.failedJobs()
		for job in jobs :
			result.append(
				_LocalJobsPath(
					jobPool = self.__jobPool,
					job = job,
					path = [ str(jobs.index(job)) ],
				)
			)
		
		return result

class _LocalJobsWindow( GafferUI.Window ) :
	
	def __init__( self, jobPool, **kw ) :
		
		GafferUI.Window.__init__( self, **kw )
		
		with self :
			with GafferUI.SplitContainer() :
				
				self.__jobListingWidget = GafferUI.PathListingWidget(
					_LocalJobsPath( jobPool ),
					columns = (
						GafferUI.PathListingWidget.IconColumn( "Status", "localDispatcherStatus", "localDispatcher:status" ),
						GafferUI.PathListingWidget.StandardColumn( "Name", "localDispatcher:jobName" ),
						GafferUI.PathListingWidget.StandardColumn( "Id", "localDispatcher:id" ),
						GafferUI.PathListingWidget.StandardColumn( "CPU", "localDispatcher:cpu" ),
						GafferUI.PathListingWidget.StandardColumn( "Memory", "localDispatcher:memory" ),
					),
					allowMultipleSelection=True
				)
				self.__jobListingWidget._qtWidget().header().setSortIndicator( 1, QtCore.Qt.AscendingOrder )
				self.__jobSelectionChangedConnection = self.__jobListingWidget.selectionChangedSignal().connect( Gaffer.WeakMethod( self.__jobSelectionChanged ) )
				
				with GafferUI.TabbedContainer() as self.__tabs :
					
					with GafferUI.ScrolledContainer( parenting = { "label"  : "Details" } ) as self.__detailsTab :
						
						with GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Vertical, spacing=10, borderWidth=10 ) :
							
							with GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing=15 ) :
								GafferUI.Label( "<h3>Current Batch</h3>" )
								self.__detailsCurrentDescription = GafferUI.Label( "N/A" )
								self.__detailsCurrentDescription.setTextSelectable( True )
							
							with GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing=15 ) :
								GafferUI.Label( "<h3>Directory</h3>" )
								self.__detailsDirectory = GafferUI.Label( "N/A" )
								self.__detailsDirectory.setTextSelectable( True )
					
					with GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Vertical, spacing=10, borderWidth=10, parenting = { "label"  : "Messages" } ) as self.__messagesTab :
						self.__messageWidget = GafferUI.MessageWidget()
				
				self.__tabChangedConnection = self.__tabs.currentChangedSignal().connect( Gaffer.WeakMethod( self.__tabChanged ) )
				
				with GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing=5 ) :
					self.__killButton = GafferUI.Button( "Kill Selected Jobs" )
					self.__killButton.setEnabled( False )
					self.__killClickedConnection = self.__killButton.clickedSignal().connect( Gaffer.WeakMethod( self.__killClicked ) )
					self.__removeButton = GafferUI.Button( "Remove Failed Jobs" )
					self.__removeButton.setEnabled( False )
					self.__removedClickedConnection = self.__removeButton.clickedSignal().connect( Gaffer.WeakMethod( self.__removeClicked ) )
		
		self.setTitle( "Local Dispatcher Jobs" )
		
		self.__updateTimer = QtCore.QTimer()
		self.__updateTimer.timeout.connect( Gaffer.WeakMethod( self.__update ) )
		self.__visibilityChangedConnection = self.visibilityChangedSignal().connect( Gaffer.WeakMethod( self.__visibilityChanged ) )
		
		self.__jobAddedConnection = jobPool.jobAddedSignal().connect( Gaffer.WeakMethod( self.__jobAdded ) )
		self.__jobRemovedConnection = jobPool.jobRemovedSignal().connect( Gaffer.WeakMethod( self.__jobRemoved ) )
	
	## Acquires the LocalJobsWindow for the specified application.
	@staticmethod
	def acquire( jobPool ) :
		
		assert( isinstance( jobPool, Gaffer.LocalDispatcher.JobPool ) )
		
		window = getattr( jobPool, "_window", None )
		if window is not None and window() :
			return window()
		
		window = _LocalJobsWindow( jobPool )
		jobPool._window = weakref.ref( window )
		
		return window
		
	def __visibilityChanged( self, widget ) :
		
		if widget.visible() :
			self.__updateTimer.start( 5000 )
		else :
			self.__updateTimer.stop()
	
	def __jobAdded( self, job ) :
		
		GafferUI.EventLoop.executeOnUIThread( self.__update )
	
	def __jobRemoved( self, job ) :
		
		GafferUI.EventLoop.executeOnUIThread( self.__update )
	
	def __update( self ) :
		
		self.__jobListingWidget.getPath()._emitPathChanged()
	
	def __updateDetails( self ) :
		
		paths = self.__jobListingWidget.getSelectedPaths()
		if not len(paths) :
			self.__detailsCurrentDescription.setText( "N/A" )
			self.__detailsDirectory.setText( "N/A" )
			return
		
		job = paths[0].job()
		self.__detailsCurrentDescription.setText( job.description() )
		self.__detailsDirectory.setText( job.directory() )
	
	def __updateMessages( self ) :
		
		self.__messageWidget.clear()
		
		paths = self.__jobListingWidget.getSelectedPaths()
		if not len(paths) :
			return
		
		for m in paths[0].job().messageHandler().messages :
			self.__messageWidget.appendMessage( m.level, m.context, m.message )
	
	def __killClicked( self, button ) :
		
		for path in self.__jobListingWidget.getSelectedPaths() :
			path.job().kill()
		
		self.__update()
	
	def __removeClicked( self, button ) :
		
		for path in self.__jobListingWidget.getSelectedPaths() :
			if path.job().failed() :
				path.jobPool()._remove( path.job(), force = True )
		
		self.__update()
	
	def __jobSelectionChanged( self, widget ) :	
		
		paths = self.__jobListingWidget.getSelectedPaths()
		numFailed = len([ x for x in paths if x.job().failed() ])
		self.__removeButton.setEnabled( numFailed )
		self.__killButton.setEnabled( len(paths) - numFailed > 0 )
		
		currentTab = self.__tabs.getCurrent()
		if currentTab is self.__detailsTab :
			self.__updateDetails()
		elif currentTab is self.__messagesTab :
			self.__updateMessages()
	
	def __tabChanged( self, tabs, currentTab ) :
		
		if currentTab is self.__detailsTab :
			self.__updateDetails()
		elif currentTab is self.__messagesTab :
			self.__updateMessages()

##########################################################################
# Implementation Details
##########################################################################

def __showLocalDispatcherWindow( menu ) :
	
	window = _LocalJobsWindow.acquire( Gaffer.LocalDispatcher.defaultJobPool() )
	scriptWindow = menu.ancestor( GafferUI.ScriptWindow )
	scriptWindow.addChildWindow( window )
	window.setVisible( True )
