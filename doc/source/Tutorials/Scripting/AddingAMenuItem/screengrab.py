# BuildTarget: images/viewerCows.png

import imath
import time

import GafferScene
import GafferUI

scriptWindow = GafferUI.ScriptWindow.acquire( script )
viewer = scriptWindow.getLayout().editors( GafferUI.Viewer )[0]

def __delay( delay ) :
	endtime = time.time() + delay
	while time.time() < endtime :
		GafferUI.EventLoop.waitForIdle( 1 )

# Circle of cows in Viewer
sceneReaderNode = GafferScene.SceneReader( "Cow" )
script.addChild( sceneReaderNode )
sceneReaderNode["fileName"].setValue( "${GAFFER_ROOT}/resources/cow/cow.scc" )
duplicateNode = GafferScene.Duplicate( "Herd" )
script.addChild( duplicateNode )
duplicateNode["target"].setValue( '/cow' )
duplicateNode["copies"].setValue( 7 )
duplicateNode["transform"]["translate"].setValue( imath.V3f( 16, 0, 0 ) )
duplicateNode["transform"]["rotate"].setValue( imath.V3f( 0, 45, 0 ) )
duplicateNode["in"].setInput( sceneReaderNode["out"] )
script.selection().add( duplicateNode )
__delay( 0.1 )
viewer.view().viewportGadget().getPrimaryChild().waitForCompletion()
GafferUI.WidgetAlgo.grab( widget = viewer, imagePath = "images/viewerCows.png" )
