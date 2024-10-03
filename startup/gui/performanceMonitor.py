##########################################################################
#
#  Copyright (c) 2021, Cinesite VFX Ltd. All rights reserved.
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
#      * Neither the name of Cinesite VFX Ltd. nor the names of
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

import functools

import IECore

import Gaffer
import GafferUI

menu = GafferUI.ScriptWindow.menuDefinition( application )

def __performanceMonitor( menu, createIfMissing = False ) :

	# We store a monitor per script, so that we don't pollute
	# other scripts with metrics collected as a side effect
	# of monitoring this one.
	script = menu.ancestor( GafferUI.ScriptWindow ).scriptNode()
	monitor = getattr( script, "__performanceMonitor", None )
	if monitor is not None :
		return monitor

	if createIfMissing :
		monitor = Gaffer.PerformanceMonitor()
		monitor.__running = False
		script.__performanceMonitor = monitor
		return monitor
	else :
		return None

def __startPerformanceMonitor( menu ) :

	monitor = __performanceMonitor( menu, createIfMissing = True )
	assert( not monitor.__running )

	monitor.__enter__()
	monitor.__running = True

def __stopPerformanceMonitor( menu ) :

	monitor = __performanceMonitor( menu )
	assert( monitor is not None and monitor.__running )
	monitor.__exit__( None, None, None )
	monitor.__running = False

	script = menu.ancestor( GafferUI.ScriptWindow ).scriptNode()
	Gaffer.MonitorAlgo.annotate( script, monitor, persistent = False )

def __clearPerformanceMonitor( menu ) :

	script = menu.ancestor( GafferUI.ScriptWindow ).scriptNode()
	del script.__performanceMonitor
	Gaffer.MonitorAlgo.removePerformanceAnnotations( script )

def __currentContextMonitor( menu ) :

	# We store a monitor per script, so that we don't pollute
	# other scripts with metrics collected as a side effect
	# of monitoring this one.
	script = menu.ancestor( GafferUI.ScriptWindow ).scriptNode()
	return getattr( script, "__contextMonitor", None )

def __startContextMonitor( menu, root = None ) :

	monitor = __currentContextMonitor( menu )
	if monitor is not None :
		assert( root is None )
	else :
		script = menu.ancestor( GafferUI.ScriptWindow ).scriptNode()
		assert( root is not None )
		assert( script == root or script.isAncestorOf( root ) )
		monitor = Gaffer.ContextMonitor( root )
		monitor.__running = False
		script.__contextMonitor = monitor

	monitor.__enter__()
	monitor.__running = True

def __stopContextMonitor( menu ) :

	monitor = __currentContextMonitor( menu )
	assert( monitor is not None and monitor.__running )
	monitor.__exit__( None, None, None )
	monitor.__running = False

	script = menu.ancestor( GafferUI.ScriptWindow ).scriptNode()
	Gaffer.MonitorAlgo.annotate( script, monitor, persistent = False )

def __clearContextMonitor( menu ) :

	script = menu.ancestor( GafferUI.ScriptWindow ).scriptNode()
	del script.__contextMonitor
	Gaffer.MonitorAlgo.removeContextAnnotations( script )

def __clearCaches( menu ) :

	Gaffer.ValuePlug.clearCache()
	Gaffer.ValuePlug.clearHashCache()

def __profilingSubMenu( menu ) :

	result = IECore.MenuDefinition()

	# PerformanceMonitor

	performanceMonitor = __performanceMonitor( menu )

	result.append(
		"/Performance Monitor/" + ( "Start" if performanceMonitor is None else "Resume" ),
		{
			"command" : __startPerformanceMonitor,
			"active" : performanceMonitor is None or not performanceMonitor.__running
		}
	)

	result.append(
		"/Performance Monitor/Stop and Annotate",
		{
			"command" : __stopPerformanceMonitor,
			"active" : performanceMonitor is not None and performanceMonitor.__running
		}
	)
	result.append(
		"/Performance Monitor/Divider",
		{
			"divider" : True,
		}
	)
	result.append(
		"/Performance Monitor/Clear",
		{
			"command" : __clearPerformanceMonitor,
			"active" : performanceMonitor is not None and not performanceMonitor.__running
		}
	)

	# ContextMonitor

	contextMonitor = __currentContextMonitor( menu )
	script = menu.ancestor( GafferUI.ScriptWindow ).scriptNode()
	selection = script.selection()

	if contextMonitor is not None :
		result.append(
			"/Context Monitor/Resume",
			{
				"command" : __startContextMonitor,
				"active" : not contextMonitor.__running,
			}
		)
	else :
		result.append(
			"/Context Monitor/Start",
			{
				"command" : functools.partial( __startContextMonitor, root = script )
			}
		)
		result.append(
			"/Context Monitor/Start for Selected Node",
			{
				"command" : functools.partial( __startContextMonitor, root = selection[-1] if len( selection ) else None ),
				"active" : selection.size() == 1
			}
		)

	result.append(
		"/Context Monitor/Stop and Annotate",
		{
			"command" : __stopContextMonitor,
			"active" : contextMonitor is not None and contextMonitor.__running
		}
	)
	result.append(
		"/Context Monitor/Divider",
		{
			"divider" : True,
		}
	)
	result.append(
		"/Context Monitor/Clear",
		{
			"command" : __clearContextMonitor,
			"active" : contextMonitor is not None and not contextMonitor.__running
		}
	)

	result.append(
		"/CacheDivider", { "divider" : True },
	)

	result.append(
		"/Clear Caches",
		{
			"command" : __clearCaches,
		}
	)

	return result

menu.append( "/Tools/Profiling", { "subMenu" : __profilingSubMenu } )

def __graphEditorCreated( graphEditor ) :

	## \todo It's a bit naughty accessing an internal gadget like this.
	# What we really want is for Editors to have plugs (like Views do), and for
	# the visible annotations to be specified on a promoted plug. Then
	# we could just set a `userDefault` for that plug.
	annotationsGadget = graphEditor.graphGadget()["__annotations"]

	annotations = Gaffer.MetadataAlgo.annotationTemplates() + [ "user", annotationsGadget.untemplatedAnnotations ]
	visiblePattern = annotationsGadget.getVisibleAnnotations()
	visibleAnnotations = { a for a in annotations if IECore.StringAlgo.matchMultiple( a, visiblePattern ) }
	visibleAnnotations -= {
		"performanceMonitor:hashDuration",
		"performanceMonitor:computeDuration",
		"performanceMonitor:perHashDuration",
		"performanceMonitor:perComputeDuration",
		"performanceMonitor:hashesPerCompute",
	}

	annotationsGadget.setVisibleAnnotations( " ".join( visibleAnnotations ) )

GafferUI.GraphEditor.instanceCreatedSignal().connect( __graphEditorCreated )
