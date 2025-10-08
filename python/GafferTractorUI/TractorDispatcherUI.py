##########################################################################
#
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

import Gaffer
import GafferDispatch
import GafferTractor

Gaffer.Metadata.registerNode(

	GafferTractor.TractorDispatcher,

	"description",
	"""
	Dispatches tasks by spooling them to a renderfarm
	managed by Pixar's Tractor software.

	This dispatcher deliberately provides a very simple
	one-to-one mapping between Gaffer's nodes and plugs
	and Tractor's Tasks and attributes. This can be
	customised on a site-by-site basis with user defaults
	and expressions for the plugs, or for more complete
	control, with TractorDispatcher.preSpoolSignal().
	""",

	plugs = {

		"service" : {

			"description" :
			"""
			A Tractor "service key expression" used to select
			blades on which tasks will be executed. The default
			value matches all blades. Typically this default is
			sufficient for the job itself, but more restrictive
			values may be needed for the dispatcher.tractor.service
			plugs on each dispatched node.
			""",

		},

		"envKey" : {

			"description" :
			"""
			An arbitrary key passed to the remote Tractor blade,
			to be used by environment handlers which configure
			the way the blade launches commands.
			""",

		},

	}

)

Gaffer.Metadata.registerNode(

	GafferDispatch.TaskNode,

	plugs = {

		"dispatcher.tractor" : {

			"description" :
			"""
			Settings that control how tasks are
			dispatched to Tractor.
			""",

			"layout:section" : "Tractor",
			"plugValueWidget:type" : "GafferUI.LayoutPlugValueWidget",

		},

		"dispatcher.tractor.service" : {

			"description" :
			"""
			A Tractor "service key expression" used to select
			blades on which tasks will be executed.
			""",

		},

		"dispatcher.tractor.tags" : {

			"description" :
			"""
			A space separated list of tags that can be
			used with Tractor's limits to constrain
			the number of concurrent tasks. Typically this is
			used to ensure that tasks using commercial
			software do not exceed the available license
			count.
			""",

		},

	}

)
