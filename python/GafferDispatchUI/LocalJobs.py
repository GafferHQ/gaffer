##########################################################################
#
#  Copyright (c) 2023, Cinesite VFX Ltd. All rights reserved.
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

import datetime
import threading

import imath

import Gaffer
import GafferUI
import GafferDispatch

from GafferUI.PlugValueWidget import sole

from Qt import QtCore
from Qt import QtGui

class _LocalJobsPath( Gaffer.Path ) :

	def __init__( self, jobPool, job = None, path = None, root = "/" ) :

		Gaffer.Path.__init__( self, path = path, root = root )

		self.__jobPool = jobPool
		self.__job = job

	def copy( self ) :

		c = self.__class__( self.__jobPool, self.__job )

		return c

	def propertyNames( self, canceller = None ) :

		return Gaffer.Path.propertyNames() + [
			"localDispatcher:status",
			"localDispatcher:id",
			"localDispatcher:jobName",
			"localDispatcher:directory",
			"localDispatcher:cpu",
			"localDispatcher:memory",
		]

	def property( self, name, canceller = None ) :

		result = Gaffer.Path.property( self, name )
		if result is not None :
			return result

		if self.__job is None :
			return None

		if name == "localDispatcher:status" :
			return self.__job.status().name
		elif name == "localDispatcher:id" :
			return self.__job.id()
		elif name == "localDispatcher:jobName" :
			return self.__job.name()
		elif name == "localDispatcher:directory" :
			return self.__job.directory()
		elif name == "localDispatcher:cpu" :
			stats = self.__job.statistics()
			return "{0:.2f} %".format( stats["pcpu"] ) if "pcpu" in stats.keys() else "---"
		elif name == "localDispatcher:memory" :
			stats = self.__job.statistics()
			return "{0:.2f} GB".format( stats["rss"] / 1024.0  / 1024.0 ) if "rss" in stats.keys() else "---"

		return None

	def job( self ) :

		return self.__job

	def jobPool( self ) :

		return self.__jobPool

	def isLeaf( self, canceller = None ) :

		return len( self )

	def _children( self, canceller ) :

		if self.isLeaf() :
			return []

		result = []
		for index, job in enumerate( self.__jobPool.jobs() ) :
			result.append(
				_LocalJobsPath(
					jobPool = self.__jobPool,
					job = job,
					path = [ str( index ) ],
				)
			)

		return result

class LocalJobs( GafferUI.Editor ) :

	def __init__( self, scriptNode, **kw ) :

		splitContainer = GafferUI.SplitContainer( borderWidth = 8 )
		GafferUI.Editor.__init__( self, splitContainer, scriptNode, **kw )

		jobPool = GafferDispatch.LocalDispatcher.defaultJobPool()

		with splitContainer :

			with GafferUI.ListContainer( spacing = 4 ) :

				self.__jobListingWidget = GafferUI.PathListingWidget(
					_LocalJobsPath( jobPool ),
					columns = (
						GafferUI.PathListingWidget.IconColumn( "Status", "localDispatcherStatus", "localDispatcher:status" ),
						GafferUI.PathListingWidget.StandardColumn( "Name", "localDispatcher:jobName", sizeMode = GafferUI.PathColumn.SizeMode.Stretch ),
						GafferUI.PathListingWidget.StandardColumn( "Id", "localDispatcher:id" ),
						GafferUI.PathListingWidget.StandardColumn( "CPU", "localDispatcher:cpu" ),
						GafferUI.PathListingWidget.StandardColumn( "Memory", "localDispatcher:memory" ),
					),
					selectionMode = GafferUI.PathListingWidget.SelectionMode.Rows,
				)
				self.__jobListingWidget._qtWidget().header().setSortIndicator( 1, QtCore.Qt.AscendingOrder )
				self.__jobListingWidget.selectionChangedSignal().connect( Gaffer.WeakMethod( self.__jobSelectionChanged ), scoped = False )

				with GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing=5 ) :
					GafferUI.Spacer( imath.V2i( 0 ), parenting = { "expand" : True } )
					self.__killButton = GafferUI.Button( "Kill Selected Jobs" )
					self.__killButton.clickedSignal().connect( Gaffer.WeakMethod( self.__killClicked ), scoped = False )
					self.__removeButton = GafferUI.Button( "Remove Selected Jobs" )
					self.__removeButton.clickedSignal().connect( Gaffer.WeakMethod( self.__removeClicked ), scoped = False )

			with GafferUI.TabbedContainer() :

				with GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Vertical, spacing=10, borderWidth=10, parenting = { "label"  : "Log" } ) as self.__messagesTab :
					self.__messageWidget = GafferUI.MessageWidget( toolbars = True, follow = True, role = GafferUI.MessageWidget.Role.Log )
					self.__messageWidget._qtWidget().setMinimumHeight( 150 )

				with GafferUI.ScrolledContainer( parenting = { "label"  : "Properties" } ) :

					with GafferUI.GridContainer( spacing=10, borderWidth=10 ) :

						GafferUI.Label( "Frame Range", parenting = { "index" : ( 0, 0 ) } )
						self.__propertiesFrameRange = GafferUI.Label( textSelectable = True, parenting = { "index" : ( 1, 0 ) } )

						GafferUI.Label( "Job Directory", parenting = { "index" : ( 0, 1 ) } )
						self.__propertiesJobDirectory = GafferUI.Label( textSelectable = True, parenting = { "index" : ( 1, 1 ) } )

						GafferUI.Label( "Environment Command", parenting = { "index" : ( 0, 2 ) } )
						self.__propertiesEnvironmentCommand = GafferUI.Label( textSelectable = True, parenting = { "index" : ( 1, 2 ) } )

						GafferUI.Label( "Start Time", parenting = { "index" : ( 0, 3 ) } )
						self.__propertiesStartTime = GafferUI.Label( textSelectable = True, parenting = { "index" : ( 1, 3 ) } )

		# Connecting to the JobPool and Job signals allows us to update our PathListingWidget
		# immediately when jobs are added and removed or their status changes.
		jobPool.jobAddedSignal().connect( Gaffer.WeakMethod( self.__jobAdded ), scoped = False )
		jobPool.jobRemovedSignal().connect( Gaffer.WeakMethod( self.__jobRemoved ), scoped = False )

		# But we also want to perform periodic updates to sample CPU/memory statistics, which
		# we do using this timer.
		self.__statisticsTimer = QtCore.QTimer()
		self.__statisticsTimer.timeout.connect( Gaffer.WeakMethod( self.__statisticsTimeout ) )
		self.visibilityChangedSignal().connect( Gaffer.WeakMethod( self.__visibilityChanged ), scoped = False )

		self.__updateButtons()

	def __repr__( self ) :

		return "GafferDispatchUI.LocalJobs( scriptNode )"

	def __visibilityChanged( self, widget ) :

		if widget.visible() :
			self.__statisticsTimer.start( 5000 )
		else :
			self.__statisticsTimer.stop()

	def __jobAdded( self, job ) :

		assert( threading.current_thread() is threading.main_thread() )
		job.statusChangedSignal().connect( Gaffer.WeakMethod( self.__jobStatusChanged ), scoped = False )
		self.__jobListingWidget.getPath()._emitPathChanged()

	def __jobRemoved( self, job ) :

		assert( threading.current_thread() is threading.main_thread() )
		self.__jobListingWidget.getPath()._emitPathChanged()

	def __jobStatusChanged( self, job ) :

		assert( threading.current_thread() is threading.main_thread() )
		self.__jobListingWidget.getPath()._emitPathChanged()
		self.__updateButtons()

	def __statisticsTimeout( self ) :

		self.__jobListingWidget.getPath()._emitPathChanged()

	def __killClicked( self, button ) :

		for job in self.__selectedJobs() :
			job.kill()

	def __removeClicked( self, button ) :

		jobPool = self.__jobListingWidget.getPath().jobPool()
		for job in self.__selectedJobs() :
			job.kill()
			jobPool.removeJob( job )

	def __selectedJobs( self ) :

		rootPath = self.__jobListingWidget.getPath()
		selection = self.__jobListingWidget.getSelection()
		return [
			path.job() for path in rootPath.children()
			if selection.match( str( path ) ) & selection.Result.ExactMatch
		]

	def __jobSelectionChanged( self, widget ) :

		jobs = self.__selectedJobs()

		if len( jobs ) == 1 :
			self.__messageWidget.setMessages( jobs[0].messages() )
			self.__messagesChangedConnection = jobs[0].messagesChangedSignal().connect( Gaffer.WeakMethod( self.__messagesChanged ), scoped = True )
		else :
			self.__messageWidget.clear()
			self.__messagesChangedConnection = None

		def soleFormat( values ) :

			value = sole( values )
			if value is not None :
				if isinstance( value, datetime.datetime ) :
					return "{:%a %b %d %H:%M:%S}".format( value )
				else :
					return str( value )
			else :
				return "---"

		self.__propertiesFrameRange.setText( soleFormat( [ j.frameRange() for j in jobs ] ) )
		self.__propertiesJobDirectory.setText( soleFormat( [ j.directory() for j in jobs ] ) )
		self.__propertiesEnvironmentCommand.setText( soleFormat( [ j.environmentCommand() for j in jobs ] ) )
		self.__propertiesStartTime.setText( soleFormat( [ j.startTime() for j in jobs ] ) )

		self.__updateButtons()

	def __messagesChanged( self, job ) :

		self.__messageWidget.setMessages( job.messages() )

	def __updateButtons( self ) :

		jobs = self.__selectedJobs()
		self.__removeButton.setEnabled( len( jobs ) )
		self.__killButton.setEnabled( any( j.status() == j.Status.Running for j in jobs ) )

GafferUI.Editor.registerType( "LocalJobs", LocalJobs )
