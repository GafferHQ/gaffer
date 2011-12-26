##########################################################################
#  
#  Copyright (c) 2011, John Haddon. All rights reserved.
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

import IECore

import GafferUI

class AboutWindow( GafferUI.Window ) :

	def __init__( self, about ) :
	
		GafferUI.Window.__init__( self, title = "About " + about.name() )
		
		with GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Vertical, spacing=10, borderWidth=30 ) as column :

			# logo and basic info
	
			with GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing=10 ) :
			
				GafferUI.Image( about.logo() )
			
				text = ( about.name() + " " + about.versionString() + "\n" +
					about.copyright() + "\n" +
					about.url()
				)
				
				GafferUI.MultiLineTextWidget( text, editable = False )
						
			# license
			
			with GafferUI.Collapsible( label="License", collapsed=True ) :
			
				GafferUI.MultiLineTextWidget(
					text = "".join( open( os.path.expandvars( about.license() ) ).readlines() ),
					editable = False,
				)
			
			# dependencies
			
			dependencies = about.dependencies()
			if dependencies :
			
				with GafferUI.Collapsible( label="Dependencies", collapsed=True ) :
	
					dependenciesText = about.dependenciesPreamble() + "\n\n"
					for d in dependencies :
					
						dependenciesText += d["name"] + "\n"
						if "credit" in d :
							dependenciesText += d["credit"] + "\n"
						if "license" in d :
							dependenciesText += d["license"] + "\n"
						if "url" in d :
							dependenciesText += d["url"] + "\n"
						
						dependenciesText += "\n"
						
					GafferUI.MultiLineTextWidget( dependenciesText, editable = False )	

		self.setChild( column )