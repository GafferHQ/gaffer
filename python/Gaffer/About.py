##########################################################################
#
#  Copyright (c) 2011-2013, John Haddon. All rights reserved.
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
import json

class About :

	@staticmethod
	def name() :

		return "Gaffer"

	@staticmethod
	def milestoneVersion() :

		return !GAFFER_MILESTONE_VERSION!

	@staticmethod
	def majorVersion() :

		return !GAFFER_MAJOR_VERSION!

	@staticmethod
	def minorVersion() :

		return !GAFFER_MINOR_VERSION!

	@staticmethod
	def patchVersion() :

		return !GAFFER_PATCH_VERSION!

	@staticmethod
	def versionSuffix() :

		return "!GAFFER_VERSION_SUFFIX!"

	@staticmethod
	def compatibilityVersion() :

		return About.milestoneVersion() * 1000 + About.majorVersion()

	@staticmethod
	def versionString() :

		return "{}.{}.{}.{}{}".format(
			About.milestoneVersion(), About.majorVersion(), About.minorVersion(),
			About.patchVersion(), About.versionSuffix()
		)

	@staticmethod
	def copyright() :

		return "Copyright (c) 2011-2019 John Haddon, Copyright (c) 2011-2019 Image Engine Design Inc."

	@staticmethod
	def license() :

		return "$GAFFER_ROOT/LICENSE"

	@staticmethod
	def url() :

		return "http://www.gafferhq.org"

	@staticmethod
	def dependenciesPreamble() :

		return ( About.name() + " includes code from several open source projects. "
			"Specific licensing information, credits, source downloads and "
			"URLs are provided for each project below."
		)

	@staticmethod
	def dependencies() :

		licenseDir = os.path.expandvars( "$GAFFER_ROOT/doc/licenses" )
		if not os.path.exists( licenseDir ) :
			# Internal build, not based on GafferHQ/dependencies.
			return []

		with open( os.path.join( licenseDir, "manifest.json" ), encoding = "utf-8" ) as f :
			result = json.load( f )

		for project in result :
			if "license" in project :
				project["license"] = os.path.normpath( os.path.join( licenseDir, project["license"] ) )

		return result
