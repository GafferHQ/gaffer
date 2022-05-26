##########################################################################
#
#  Copyright (c) 2022, Cinesite VFX Ltd. All rights reserved.
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

import arnold

import IECore

import Gaffer
import GafferUI
import GafferArnold

class _ArnoldGPUCache( object ) :

	currentStatus = None

	def __cachePopulateCallback( self, userData, status, fractionDone, msg ) :

		self.currentStatus = status

		IECore.msg( IECore.Msg.Level.Debug, "populateGPUCache", str( msg ) )

	def _populateCache( self ) :

		canceller = Gaffer.Context.current().canceller()
		arnold.AiGPUCachePopulate(
			arnold.AI_GPU_CACHE_POPULATE_NON_BLOCKING,
			0,  # num_proc
			self.__cachePopulateCallback
		)
		try :
			while self.currentStatus != arnold.AI_RENDER_STATUS_FINISHED.value :
				IECore.Canceller.check( canceller )
		except Exception as e :
			arnold.AiGPUCachePopulateTerminate()

def populateGPUCache( menu ) :

	dialogue = GafferUI.BackgroundTaskDialogue( "Populating Arnold GPU Cache" )
	cache = _ArnoldGPUCache()

	dialogue.waitForBackgroundTask(
		cache._populateCache,
		parentWindow = menu.ancestor( GafferUI.Window )
	)
