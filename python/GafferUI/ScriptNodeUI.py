##########################################################################
#
#  Copyright (c) 2012, John Haddon. All rights reserved.
#  Copyright (c) 2013, Image Engine Design Inc. All rights reserved.
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
import GafferUI

Gaffer.Metadata.registerNode(

	Gaffer.ScriptNode,

	"description",
	"""
	Defines a "script" - a Gaffer node network which can be
	saved to disk as a ".gfr" file and reloaded.
	""",

	plugs = {

		"fileName" : (

			"description",
			"""
			Where the script is stored.
			""",

		),

		"unsavedChanges" : (

			"description",
			"""
			Indicates whether or not the script has been
			modified since it was last saved.
			""",

		),

		"frameRange" : (

			"description",
			"""
			Defines the start and end frames for the script.
			These don't enforce anything, but are typically
			used by dispatchers to control default frame
			ranges, and by the UI to define the range of the
			time slider.
			""",

		),

		"frameRange.start" : (

			"description",
			"""
			The start frame. This doesn't enforce anything,
			but is typically used by dispatchers to control
			default frame ranges, and by the UI to define
			the range of the time slider.
			""",

		),

		"frameRange.end" : (

			"description",
			"""
			The end frame. This doesn't enforce anything,
			but is typically used by dispatchers to control
			default frame ranges, and by the UI to define
			the range of the time slider.
			""",

		),

		"variables" : (

			"description",
			"""
			Container for user-defined variables which can
			be used in expressions anywhere in the script.
			"""

		),

	},

)

GafferUI.PlugValueWidget.registerCreator(
	Gaffer.ScriptNode,
	"unsavedChanges",
	None
)

GafferUI.PlugValueWidget.registerCreator(
	Gaffer.ScriptNode,
	"frameRange",
	GafferUI.CompoundNumericPlugValueWidget
)

GafferUI.PlugValueWidget.registerCreator(
	Gaffer.ScriptNode,
	"variables",
	lambda plug : GafferUI.CompoundDataPlugValueWidget( plug, collapsed=None ),
)

Gaffer.Metadata.registerPlugValue(
	Gaffer.ScriptNode,
	"variables",
	"nodeUI:section",
	"Variables",
)
