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
import GafferDispatch
import GafferUI
import GafferDispatchUI

Gaffer.Metadata.registerValue( GafferDispatch.LocalDispatcher, "executeInBackground", "userDefault", True )
GafferDispatch.Dispatcher.setDefaultDispatcherType( "Local" )

def __scriptWindowPreClose( scriptWindow ) :

	numScripts = len( scriptWindow.scriptNode().parent() )
	if numScripts > 1 :
		return False

	# The last window is about to be closed, which will quit the
	# application. Check for LocalJobs that are still running,
	# and prompt the user.

	incompleteJobs = [
		job for job in
		GafferDispatch.LocalDispatcher.defaultJobPool().jobs()
		if job.status() in (
			GafferDispatch.LocalDispatcher.Job.Status.Waiting,
			GafferDispatch.LocalDispatcher.Job.Status.Running,
		)
	]

	if len( incompleteJobs ) == 0 :
		return False

	dialogue = GafferUI.ConfirmationDialogue(
		"Kill Incomplete Jobs?",
		"{} LocalDispatcher job{} still running and will be killed".format(
			len( incompleteJobs ),
			"s are" if len( incompleteJobs ) > 1 else " is"
		),
		confirmLabel = "Kill"
	)

	# If `Cancel` was pressed, prevent the window from being closed.
	return dialogue.waitForConfirmation( parentWindow = scriptWindow ) == False

def __scriptWindowCreated( scriptWindow ) :

	scriptWindow.preCloseSignal().connect( __scriptWindowPreClose )

GafferUI.ScriptWindow.instanceCreatedSignal().connect( __scriptWindowCreated )
