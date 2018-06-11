# BuildTarget: images/herd.png

import imath

import GafferScene

import GafferUI

scriptWindow = GafferUI.ScriptWindow.acquire( script )

script["Cow"] = GafferScene.SceneReader( "Cow" )
script["Cow"]["fileName"].setValue( "${GAFFER_ROOT}/resources/cow/cow.scc" )
script["Herd"] = GafferScene.Duplicate( "Herd" )
script["Herd"]["target"].setValue( '/cow' )
script["Herd"]["copies"].setValue( 7 )
script["Herd"]["transform"]["translate"].setValue( imath.V3f( 16, 0, 0 ) )
script["Herd"]["transform"]["rotate"].setValue( imath.V3f( 0, 45, 0 ) )
script["Herd"]["in"].setInput( script["Cow"]["out"] )
script.selection().add( script["Herd"] )
viewer = scriptWindow.getLayout().editors( GafferUI.Viewer )[0]
GafferUI.WidgetAlgo.grab( widget = viewer, imagePath = "images/herd.png" )
