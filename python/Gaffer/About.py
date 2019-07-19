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
	def compatibilityVersion() :

		return About.milestoneVersion() * 1000 + About.majorVersion()

	@staticmethod
	def versionString() :

		return "%d.%d.%d.%d" % ( About.milestoneVersion(), About.majorVersion(), About.minorVersion(), About.patchVersion() )

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

		result = [

			{
				"name" : "boost",
				"url" : "http://www.boost.org/",
				"license" : "$GAFFER_ROOT/doc/licenses/Boost",
			},

			{
				"name" : "cortex",
				"url" : "https://github.com/ImageEngine/cortex/",
				"license" : "$GAFFER_ROOT/doc/licenses/Cortex",
			},

			{
				"name" : "freetype",
				"url" : "http://www.freetype.org/",
				"license" : "$GAFFER_ROOT/doc/licenses/FreeType",
				"credit" : "Portions of this software are copyright (c) 2009 The FreeType Project (www.freetype.org). All rights reserved."
			},

			{
				"name" : "glew",
				"url" : "http://glew.sourceforge.net/",
				"license" : "$GAFFER_ROOT/doc/licenses/GLEW",
			},

			{
				"name" : "ilmbase",
				"url" : "http://www.openexr.com/",
				"license" : "$GAFFER_ROOT/doc/licenses/IlmBase",
			},

			{
				"name" : "libjpeg-turbo",
				"url" : "https://libjpeg-turbo.org/",
				"license" : "$GAFFER_ROOT/doc/licenses/LibJPEG-Turbo",
				"credit" : "This software is based in part on the work of the Independent JPEG Group.",
			},

			{
				"name" : "libpng",
				"url" : "http://www.libpng.org/",
				"license" : "$GAFFER_ROOT/doc/licenses/LibPNG",
			},

			{
				"name" : "openexr",
				"url" : "http://www.openexr.com/",
				"license" : "$GAFFER_ROOT/doc/licenses/OpenEXR",
			},

			{
				"name" : "python",
				"url" : "http://python.org/",
				"license" : "$GAFFER_ROOT/doc/licenses/Python",
			},

			{
				"name" : "pyopengl",
				"url" : "http://pyopengl.sourceforge.net/",
			},

			{
				"name" : "libtiff",
				"url" : "http://www.libtiff.org/",
				"license" : "$GAFFER_ROOT/doc/licenses/LibTIFF",
			},

			{
				"name" : "tbb",
				"url" : "http://threadingbuildingblocks.org/",
				"license" : "$GAFFER_ROOT/doc/licenses/TBB",
			},

			{
				"name" : "OpenColorIO",
				"url" : "http://opencolorio.org/",
				"license" : "$GAFFER_ROOT/doc/licenses/OpenColorIO",
			},

			{
				"name" : "OpenImageIO",
				"url" : "http://www.openimageio.org/",
				"license" : "$GAFFER_ROOT/doc/licenses/OpenImageIO",
			},

			{
				"name" : "HDF5",
				"url" : "http://www.hdfgroup.org/",
				"license" : "$GAFFER_ROOT/doc/licenses/HDF5",
			},

			{
				"name" : "Alembic",
				"url" : "http://www.alembic.io/",
				"license" : "$GAFFER_ROOT/doc/licenses/Alembic",
			},

			{
				"name" : "OpenShadingLanguage",
				"url" : "https://github.com/imageworks/OpenShadingLanguage/",
				"license" : "$GAFFER_ROOT/doc/licenses/OpenShadingLanguage",
			},

			{
				"name" : "OpenVDB",
				"url" : "http://www.openvdb.org//",
				"license" : "$GAFFER_ROOT/doc/licenses/OpenVDB",
			},

			{
				"name" : "USD",
				"url" : "http://http://graphics.pixar.com/usd",
				"license" : "$GAFFER_ROOT/doc/licenses/USD",
			},

			{
				"name" : "Qt",
				"url" : "http://qt.nokia.com/",
				"license" : "$GAFFER_ROOT/doc/licenses/Qt",
			},

		]

		if os.path.exists( os.environ["GAFFER_ROOT"] + "/python/PyQt4" ) :

			result.append( {
				"name" : "PyQt",
				"url" : "http://www.riverbankcomputing.co.uk/",
				"license" : "$GAFFER_ROOT/doc/licenses/pyQt",
			} )

		if os.path.exists( os.environ["GAFFER_ROOT"] + "/python/PySide" ) :

			result.append( {
				"name" : "PySide",
				"url" : "http://www.pyside.org/",
				"license" : "$GAFFER_ROOT/doc/licenses/pySide",
			} )

		return result
