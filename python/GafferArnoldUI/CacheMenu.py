##########################################################################
#
#  Copyright (c) 2017, Image Engine Design Inc. All rights reserved.
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

import functools

import arnold

import GafferUI
import GafferScene

def appendDefinitions( menuDefinition, prefix="" ) :

	for label, flags in (
		( "All", arnold.AI_CACHE_ALL ),
		( "Divider", None ),
		( "Texture", arnold.AI_CACHE_TEXTURE ),
		( "Skydome Lights", arnold.AI_CACHE_BACKGROUND ),
		( "Quad Lights", arnold.AI_CACHE_QUAD ),
	) :
		menuDefinition.append(
			prefix + "/Flush Cache/" + label,
			{
				"divider" : flags is None,
				"command" : functools.partial( __flushCaches, flags = flags ),
			}
		)

def __flushCaches( menu, flags ) :

	scriptNode = menu.ancestor( GafferUI.ScriptWindow ).scriptNode()
	flushed = False
	for node in GafferScene.InteractiveRender.RecursiveRange( scriptNode ) :
		if node["state"].getValue() == node.State.Stopped :
			continue
		if node.command( "ai:cacheFlush", { "flags" : flags } ) is not None :
			flushed = True

	if not flushed :
		# No renders running. Flush global caches ready for next one.
		arnold.AiUniverseCacheFlush( None, flags )
