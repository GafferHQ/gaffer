##########################################################################
#
#  Copyright (c) 2016, John Haddon. All rights reserved.
#  Copyright (c) 2016, Image Engine Design Inc. All rights reserved.
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

import os
import glob
import inspect
import platform
import ctypes

import IECore

import Gaffer

def exportNodeReference( directory, modules = [], modulePath = "" ) :

	__makeDirs( directory )

	if modulePath :
		modulePath = os.path.expandvars( modulePath )
		for m in glob.glob( modulePath + "/*" ) :
			try :
				module = __import__( os.path.basename( m ) )
			except ImportError :
				continue

			if not m.endswith( "Test" ) and not m.endswith( "UI" ) :
				modules.append( module )

	index = open( "%s/index.md" % directory, "w" )
	index.write( "<!-- !NO_SCROLLSPY -->\n\n" )
	index.write( __heading( "Node Reference" ) )

	tocIndex = ""

	for module in sorted( modules, key = lambda x : getattr( x, "__name__" ) ) :

		moduleIndex = ""
		for name in dir( module ) :

			cls = getattr( module, name )
			if not inspect.isclass( cls ) or not issubclass( cls, Gaffer.Node ) :
				continue

			try :
				node = cls()
			except :
				continue

			if not node.__module__.startswith( module.__name__ + "." ) :
				# Skip nodes which look like they've been injected from
				# another module by one of the compatibility config files.
				continue

			__makeDirs( directory + "/" + module.__name__ )
			with open( "%s/%s/%s.md" % ( directory, module.__name__, name ), "w" ) as f :
				f.write( __nodeDocumentation( node ) )
				moduleIndex += "\n{}{}.md".format( " " * 4, name )

		if moduleIndex :

			with open( "%s/%s/index.md" % ( directory, module.__name__ ), "w" ) as f :
				f.write( "<!-- !NO_SCROLLSPY -->\n\n" )
				f.write( __heading( module.__name__ ) )
				f.write( __tocString().format( moduleIndex ) )

			tocIndex += "\n{}{}/index.md".format( " " * 4, module.__name__ )

	index.write( __tocString().format( tocIndex ) )

def exportLicenseReference( directory, about ) :

	with open( directory + "/index.md", "w" ) as index :

		index.write( __heading( "License" ) )
		index.write( "```none\n" + __fileContents( about.license() ) + "\n```\n\n" )

		index.write( __heading( "Dependencies", 1 ) )

		index.write( about.dependenciesPreamble() + "\n\n" )

		for dependency in about.dependencies() :

			index.write( __heading( dependency["name"], 2 ) )

			if "credit" in dependency :
				index.write( dependency["credit"] + "\n\n" )

			if "url" in dependency :
				index.write( "[%s](%s)\n\n" % ( dependency["url"], dependency["url"] ) )

			if "license" in dependency :
				if os.path.isfile( os.path.expandvars( dependency["license"] ) ) :
					index.write( "```none\n" + __fileContents( dependency["license"] ) + "\n```\n\n" )
				else :
					# Looks like Gaffer has been built with external dependencies rather
					# than using the package provided by the gafferDependencies project.
					# Documentation without the licenses isn't suitable for publication,
					# but is OK for internal use at facilities which build their own.
					pass

def exportCommandLineReference( directory, appPath = "$GAFFER_ROOT/apps", ignore = set() ) :

	classLoader = IECore.ClassLoader(
		IECore.SearchPath( os.path.expandvars( appPath ) )
	)

	__makeDirs( directory )

	index = open( "%s/index.md" % directory, "w" )
	index.write( "<!-- !NO_SCROLLSPY -->\n\n" )
	index.write( __heading( "Command Line Reference" ) )

	index.write( inspect.cleandoc(

		"""
		The `gaffer` command is an application loader used to run
		any of the applications shipped with gaffer, or any extension
		apps installed in directories specified by the `GAFFER_APP_PATHS`
		environment variable.

		A gaffer command takes this general form :

		```
		gaffer appName -arg value -arg value ...
		```

		If the `appName` is not specified it defaults to `gui`, and
		the familiar main interface is loaded. This shortcut also allows
		a file to load to be specified :

		```
		gaffer file.gfr
		```

		Help for any application can be printed with the following
		command :

		```
		gaffer -help appName
		```

		Further information on the specific command line arguments for each
		application is provided below.
		"""

	) )

	index.write( "\n\n" )

	tocIndex = ""

	for appName in classLoader.classNames() :

		if appName in ignore :
			continue

		tocIndex += "\n{}{}.md".format( " " * 4, appName )
		with open( "%s.md" % appName, "w" ) as f :

			f.write( __appDocumentation( classLoader.load( appName )() ) )

	index.write( __tocString().format( tocIndex ) )

def markdownToHTML( markdown ) :

	cmark = __cmark()
	if cmark is None :
		return markdown

	markdown = markdown.encode( "UTF-8" )
	return cmark.cmark_markdown_to_html( markdown, len( markdown ), cmark.CMARK_OPT_UNSAFE ).decode( "UTF-8" )

def __nodeDocumentation( node ) :

	result = __heading( node.typeName().rpartition( ":" )[2] )
	result += Gaffer.Metadata.value( node, "description" )

	def walkPlugs( parent ) :

		result =  ""
		for plug in parent.children( Gaffer.Plug ) :

			if plug.getName().startswith( "__" ) :
				continue

			description = Gaffer.Metadata.value( plug, "description" )
			if not description :
				continue

			result += "\n\n" + __heading( plug.relativeName( node ), 1 )
			result += description

			extensions = Gaffer.Metadata.value( plug, "fileSystemPath:extensions" ) or []
			if isinstance( extensions, str ) :
				extensions = extensions.split()

			if extensions :
				result += "\n\n**Supported file extensions** : "+ ", ".join( extensions )

			if type( plug ) in ( Gaffer.Plug, Gaffer.ValuePlug, Gaffer.CompoundDataPlug ) :
				result += walkPlugs( plug )

		return result

	result += walkPlugs( node )

	return result

def __appDocumentation( app ) :

	result = __heading( app.__class__.__name__ )

	result += app.description + "\n\n"

	for name, parameter in app.parameters().items() :

		result += __heading( "-" + name, 1 )
		result += parameter.description + "\n\n"

	return result

def __fileContents( file ) :

	with open( os.path.expandvars( file ), "r" ) as f :
		text = f.read()

	return text

def __heading( text, level = 0 ) :

	if level < 2 :
		return "%s\n%s\n\n" % ( text, "=-"[level] * len( text ) )
	else :
		return "%s %s\n\n" % ( "#" * (level + 1), text )

def __makeDirs( directory ) :

	try :
		os.makedirs( directory )
	except OSError :
		# Unfortunately makedirs raises an exception if
		# the directory already exists, but it might also
		# raise if it fails. We reraise only in the latter case.
		if not os.path.isdir( directory ) :
			raise

def __tocString() :

	tocString = inspect.cleandoc(

		"""
		```{{eval-rst}}
		.. toctree::
		    :titlesonly:
		    :maxdepth: 1
		{0}
		```
		"""

	)

	return tocString

__cmarkDLL = ""
def __cmark() :

	global __cmarkDLL
	if __cmarkDLL != "" :
		return __cmarkDLL

	sys = platform.system()

	if sys == "Darwin" :
		libName = "libcmark-gfm.dylib"
	elif sys == "Windows" :
		libName = "cmark-gfm.dll"
	else :
		libName = "libcmark-gfm.so"

	try :
		__cmarkDLL = ctypes.CDLL( libName )
	except :
		__cmarkDLL = None
		return __cmarkDLL

	__cmarkDLL.cmark_markdown_to_html.restype = ctypes.c_char_p
	__cmarkDLL.cmark_markdown_to_html.argtypes = [ctypes.c_char_p, ctypes.c_long, ctypes.c_long]

	__cmarkDLL.CMARK_OPT_UNSAFE = 1 << 17

	return __cmarkDLL
