##########################################################################
#
#  Copyright (c) 2025, Image Engine Design Inc. All rights reserved.
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

import GafferSceneUI
import IECore

def __expandUSDPointInstancersMenu( menuDefinition, plugValueWidget ) :

	sceneView = plugValueWidget.getPlug().node()
	try:
		renderAdaptor = sceneView["__preprocessor"]["RenderAdaptors"]["USDPointInstancerAdaptor"]["_PointInstancerAdaptor"]
	except:
		# If there is no adaptor, then this menu doesn't make sense - if the user has deregistered this adaptor,
		# it probably means they aren't using USD, or they have their own approach to point instancers, so we
		# can just skip this menu option.
		return

	renderer = renderAdaptor["renderer"].getValue()
	currentDict = renderAdaptor["defaultEnabledPerRenderer"].getValue()
	current = currentDict.get( renderer, IECore.BoolData( True ) ).value

	def callBackFunc( unused ):
		modified = currentDict.copy()
		modified[renderer] = IECore.BoolData( not current )
		renderAdaptor["defaultEnabledPerRenderer"].setValue( modified )

	menuDefinition.append( "/AttributesDivider", { "divider" : True } )
	menuDefinition.append(
		"/Expand USD Instancers",
		{
			"command" : callBackFunc,
			"checkBox" : current
		}
	)

GafferSceneUI.SceneViewUI._ExpansionPlugValueWidget.menuSignal().connect( __expandUSDPointInstancersMenu )
