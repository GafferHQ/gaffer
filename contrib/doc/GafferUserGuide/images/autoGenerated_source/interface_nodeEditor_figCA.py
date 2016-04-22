import IECore
import Gaffer
import GafferUI
import GafferScene
import GafferSceneUI
import os

scriptNode = script
scriptWindow = GafferUI.ScriptWindow.acquire( script )

#just launch a colour chooser dialogue and then set it to be grabbed
cc = GafferUI.ColorChooserDialogue(color=IECore.Color3f(0.2,0.6,0.8))
cc.setVisible(True)
cc._Widget__qtWidget.resize(250,250)
cc.colorChooser().setColor( IECore.Color3f(0.6,0.6,0.8) )
application.setGrabWidget(cc)
