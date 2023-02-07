##########################################################################
#
#  Copyright (c) 2011-2013, John Haddon. All rights reserved.
#  Copyright (c) 2012, Image Engine Design Inc. All rights reserved.
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
import imath

import IECore

import Gaffer
import GafferUI

class AboutWindow( GafferUI.Window ) :

	def __init__( self, about, **kw ) :

		GafferUI.Window.__init__( self, title = "About " + about.name(), sizeMode=GafferUI.Window.SizeMode.Manual, borderWidth = 6, **kw )

		with self :

			with GafferUI.TabbedContainer() :

				with GafferUI.ListContainer(
					GafferUI.ListContainer.Orientation.Vertical,
					spacing=10,
					borderWidth=10,
					parenting = { "label"  : "Gaffer" },
				) :

					GafferUI.Spacer(
						imath.V2i( 1 ),
						parenting = { "expand" : True }
					)

					GafferUI.Image(
						"GafferLogo.png",
						parenting = { "horizontalAlignment" : GafferUI.HorizontalAlignment.Center }
					)

					text = "<h3><a href='%s'>%s</a></h3> <small>Version %s</small>" % (
						about.url(),
						about.url(),
						about.versionString(),
					)

					self.__label(
						text,
						horizontalAlignment = GafferUI.HorizontalAlignment.Center,
						parenting = { "horizontalAlignment" : GafferUI.Label.HorizontalAlignment.Center },
					)

					GafferUI.Spacer(
						imath.V2i( 1 ),
						parenting = { "expand" : True }
					)

					self.__label(
						"<small>%s</small>" % about.copyright().replace( "(c)", "&copy;" ),
						parenting = { "horizontalAlignment" : GafferUI.Label.HorizontalAlignment.Center },
					)

				with GafferUI.ListContainer(
					GafferUI.ListContainer.Orientation.Vertical,
					spacing=10,
					borderWidth=10,
					parenting = { "label"  : "License" },
				) :

					license = "".join( open( os.path.expandvars( about.license() ), encoding = "utf-8" ).readlines() )
					with GafferUI.ScrolledContainer(
						horizontalMode=GafferUI.ScrollMode.Never,
						verticalMode=GafferUI.ScrollMode.Automatic,
						borderWidth = 5
					) :
						self.__label( "<pre>" + license + "</pre>" )

				dependencies = about.dependencies()
				if dependencies :

					with GafferUI.ListContainer(
						GafferUI.ListContainer.Orientation.Vertical,
						spacing=10,
						borderWidth=10,
						parenting = { "label" : "Dependencies" },
					) :

						with GafferUI.ScrolledContainer(
							horizontalMode=GafferUI.ScrollMode.Never,
							verticalMode=GafferUI.ScrollMode.Always,
							borderWidth = 5
						) :

							with GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Vertical, spacing=5, borderWidth=10 ) :

								text = "<p>%s</p>" % self.__wrapText( about.dependenciesPreamble() )

								for d in dependencies :

									text += "<h3>%s</h3>" % d["name"]

									if "credit" in d :
										text += "<p>%s</p>" % self.__wrapText( d["credit"] )

									if "license" in d :
										text += "<a href='file://%s'>License</a>" % os.path.expandvars( d["license"] )

									if "url" in d :
										if "license" in d :
											text += " | "
										text += "<a href='%s'>%s</a>" % ( d["url"], d["url"] )

								self.__label( text )

	def __wrapText( self, text ) :

		return IECore.StringUtil.wrap( text, 80 ).replace( '\n', "<br>" )

	def __label( self, text, **kw ) :

		## \todo Perhaps this stylesheet stuff should be done as standard for all labels?
		header = "<html><head><style type=text/css>"
		header += "a:link { color:#bbbbbb; text-decoration:none }"
		header += "</style></head><body>"

		footer = "</body></html>"

		text = header + text + footer

		label = GafferUI.Label( text, **kw )
		label.linkActivatedSignal().connect( Gaffer.WeakMethod( self.__linkActivated ), scoped = False )
		return label

	def __linkActivated( self, label, url ) :

		GafferUI.showURL( url )
