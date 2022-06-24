###########################################################################
#
#  Copyright (c) 2022, Image Engine Design Inc. All rights reserved.
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
import GafferImage
import GafferUI
import imath

Gaffer.Metadata.registerNode(

	GafferImage.DeleteViews,

	"description",
	"""
	Deletes views from an image.
	""",

	plugs = {

		"mode" : [

			"description",
			"""
			Defines how the views listed in the views
			plug are treated. Delete mode deletes the listed
			views. Keep mode keeps the listed views,
			deleting all others.
			""",

			"preset:Delete", GafferImage.DeleteViews.Mode.Delete,
			"preset:Keep", GafferImage.DeleteViews.Mode.Keep,

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",

		],

		"views" : [

			"description",
			"""
			The names of the views to be deleted (or kept
			if the mode is set to Keep). Names should be separated
			by spaces and may contain any of Gaffer's standard
			wildcards.

			Note that if you delete all views from an image, you will
			be unable to evaluate attributes of the image,  because it
			will have no data left.
			""",

		],

	}

)
