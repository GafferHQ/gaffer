##########################################################################
#
#  Copyright (c) 2018, Image Engine Design Inc. All rights reserved.
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

from Qt import QtCore

import collections
import pathlib
import re
import stat
import weakref

class Backups( object ) :

	def __init__( self, applicationRoot ) :

		# \todo I wonder if it would make sense for this sort
		# of "bolt on" component to be a GraphComponent that was
		# parented under the ApplicationRoot somewhere, instead
		# of manually tracking the "parent" like this?
		self.__applicationRoot = weakref.ref( applicationRoot )

		self.__settings = Gaffer.Plug()
		self.__settings["enabled"] = Gaffer.BoolPlug( defaultValue = True )
		self.__settings["frequency"] = Gaffer.IntPlug( defaultValue = 5, minValue = 0 )
		self.__settings["fileName"] = Gaffer.StringPlug( defaultValue = "${script:directory}/.gafferBackups/${script:name}-backup${backup:number}.gfr" )
		self.__settings["files"] = Gaffer.IntPlug( defaultValue = 10, minValue = 1 )
		self.__settings["checkForBackups"] = Gaffer.BoolPlug( defaultValue = True )

		applicationRoot["preferences"]["backups"] = self.__settings

		applicationRoot["preferences"].plugSetSignal().connect( self.__plugSet, scoped = False )

		self.__timer = QtCore.QTimer()
		self.__timer.timeout.connect( Gaffer.WeakMethod( self.__timeout ) )

		# Initialise the timer
		self.__plugSet( self.__settings["enabled"] )

	# Creates a backup for the specified script, returning the
	# name of the backup file. This is really only public so we
	# can call it from the unit tests.
	def backup( self, script ) :

		path = None
		existingPaths = []
		for p in self.__potentialPaths( script ) :
			if not p.exists() :
				path = p
				break
			else :
				existingPaths.append( p )

		if path is None :
			# All files exist already, sort by modification
			# time and choose the oldest.
			existingPaths.sort( key = lambda p : p.stat().st_mtime )
			path = existingPaths[0]

		path.parent.mkdir( parents = True, exist_ok = True )

		# When overwriting a previous backup we need to
		# temporarily make it writable. If this fails for
		# any reason we leave it to `serialiseToFile()` to
		# throw.
		with IECore.IgnoredExceptions( OSError ) :
			path.chmod( stat.S_IWUSR )

		script.serialiseToFile( path )

		# Protect file by making it read only.
		path.chmod( stat.S_IREAD | stat.S_IRGRP | stat.S_IROTH )

		return path

	# Returns the filenames of all the backups that have
	# been made for the specified script, ordered from
	# oldest to most recent. Script may either be a ScriptNode
	# or a filename.
	def backups( self, script ) :

		paths = [ p for p in self.__potentialPaths( script ) if p.exists() ]
		paths.sort( key = lambda p : p.stat().st_mtime )
		return paths

	# Returns the most recent backup for `script`, if it is
	# both newer and has different contents to the original.
	# Otherwise returns None. Script may either be a ScriptNode
	# or a filename.
	def recoveryFile( self, script ) :

		scriptPath = self.__scriptPath( script )
		if not scriptPath:
			return None
		backups = self.backups( scriptPath )
		if not backups :
			return None

		backupPath = backups[-1]
		if not scriptPath.exists() :
			return backupPath

		if backupPath.stat().st_mtime < scriptPath.stat().st_mtime :
			return None

		ignorePatterns = [
			# Commented lines, for instance a header.
			r'#.*$',
			# Version metadata.
			r'Gaffer\.Metadata\.registerValue\( parent, "serialiser:.*Version", .* \)$',
			r'Gaffer\.Metadata\.registerNodeValue\( parent, "serialiser:.*Version", .* \)$',
			# Pesky catalogue port number, which is different each time we run.
			r'parent\["variables"\]\["imageCataloguePort"\]\["value"\]\.setValue\( [0-9]* \)$',
		]
		ignorePatterns = [ re.compile( x ) for x in ignorePatterns ]

		with open( backupPath, encoding = "utf-8" ) as backupFile, open( scriptPath, encoding = "utf-8" ) as scriptFile :

			backupLines = backupFile.readlines()
			scriptLines = scriptFile.readlines()

			if len( backupLines ) != len( scriptLines ) :
				return backupPath

			for backupLine, scriptLine in zip( backupLines, scriptLines ) :

				if any( x.match( backupLine ) and x.match( scriptLine ) for x in ignorePatterns ) :
					continue

				if backupLine != scriptLine :
					return backupPath

		return None

	def settings( self ) :

		return self.__settings

	def checkForBackups( self ) :

		return self.__settings["checkForBackups"].getValue()

	@classmethod
	def acquire( cls, application, createIfNecessary=True ) :

		if isinstance( application, Gaffer.Application ) :
			applicationRoot = application.root()
		else :
			assert( isinstance( application, Gaffer.ApplicationRoot ) )
			applicationRoot = application

		try :
			return applicationRoot.__backups
		except AttributeError :
			if not createIfNecessary :
				return None
			applicationRoot.__backups = Backups( applicationRoot )
			return applicationRoot.__backups

	def __plugSet( self, plug ) :

		if plug == self.__settings["fileName"] :
			if plug.getValue() == "" :
				self.__timer.stop()
				return

		if plug in ( self.__settings["enabled"], self.__settings["frequency"] ) :
			frequency = self.__settings["frequency"].getValue()
			if not self.__settings["enabled"].getValue() :
				frequency = 0

			if not frequency :
				self.__timer.stop()
			else :
				self.__timer.start(
					# Frequency is in minutes, Qt wants milliseconds
					frequency * 60 * 1000
				)

	def __timeout( self ) :

		for script in self.__applicationRoot()["scripts"] :

			if Gaffer.MetadataAlgo.readOnly( script ) :
				# Skip read-only scripts as a heuristic for
				# not making backups-of-backups. Even if this
				# isn't actually a backup, the user can't edit
				# it anyway, so can't make any changes that
				# would require backing up.
				continue

			if script["fileName"].getValue() :
				try :
					backupFileName = self.backup( script )
					IECore.msg(
						IECore.Msg.Level.Info,
						"GafferUI.Backups",
						"Saved backup file \"{}\"".format( backupFileName )
					)
				except Exception as e :
					IECore.msg(
						IECore.Msg.Level.Error,
						"GafferUI.Backups",
						str( e )
					)

	def __scriptPath( self, script ) :

		if isinstance( script, pathlib.Path ) :
			return script

		if isinstance( script, Gaffer.ScriptNode ) :
			fileName = script["fileName"].getValue()
		else :
			assert( isinstance( script, str ) )
			fileName = script

		return pathlib.Path( fileName ) if fileName else None

	def __potentialPaths( self, script ) :

		scriptPath = self.__scriptPath( script )

		if not scriptPath :
			return []

		context = Gaffer.Context()
		context["script:name"] = scriptPath.stem
		context["script:directory"] = scriptPath.parent.as_posix()

		pattern = self.__settings["fileName"].getValue()
		paths = []
		for i in range( self.__settings["files"].getValue() ) :
			context["backup:number"] = i
			context.setFrame( i )
			paths.append( pathlib.Path( context.substitute( pattern ) ) )

		# Make results unique while maintaining order
		return collections.OrderedDict( [ ( x, x ) for x in paths ] ).keys()

##########################################################################
# UI
##########################################################################

def __backupsEnabled( plug ) :

	return plug["enabled"].getValue()

def __backupNumberEnabled( plug ) :

	if not __backupsEnabled( plug ) :
		return False

	f = plug["fileName"].getValue()
	return "${backup:number}" in f

Gaffer.Metadata.registerNode(

	Gaffer.Preferences,

	plugs = {

		"backups" : [

			"description",
			"""
			Controls a mechanism used to create automatic
			backup copies of scripts.
			""",

			"layout:section", "Backups",
			"plugValueWidget:type", "GafferUI.LayoutPlugValueWidget",

			"layout:activator:backupsEnabled", __backupsEnabled,
			"layout:activator:backupNumberEnabled", __backupNumberEnabled,

		],

		"backups.enabled" : [

			"description",
			"""
			Turns the backup system on and off.
			""",

		],

		"backups.frequency" : [

			"description",
			"""
			How often backups are made, measured in minutes.
			""",

			"layout:activator", "backupsEnabled",

		],

		"backups.fileName" : [

			"description",
			"""
			The name of the backup file to be created. This may
			use any of the following variables :

			- `${script:directory}` : the directory that contains
			  the script to be backed up.
			- `${script:name}` : the current filename of the script
			  to be backed up. Note that this variable _must_ be
			  used, otherwise backups for different scripts will
			  be saved over the top of each other.
			- `${backup:number}` : the number of this backup, used
			  to keep more than one backup per file.
			- `#` : the same as `${backup:number}`.
			""",

			"layout:activator", "backupsEnabled",

		],

		"backups.files" : [

			"description",
			"""
			The number of backups to keep for each script. Only
			used if the backup filename includes `${backup:number}`.
			When the backup limit is reached, the oldest backup
			will be overwritten.
			""",

			"layout:activator", "backupNumberEnabled",

		],

		"backups.checkForBackups" : [

			"description",
			"""
			When a file is opened, checks for a more recent backup.
			If one is found, a dialogue is displayed,
			asking if the backup should be opened instead.
			If this option is turned off,
			you can still access backups via the File/Open Backup menu item.
			""",

		],

	}

)
