# BuildTarget: images/demoMacbethChart.png

import os
import subprocess32 as subprocess
import tempfile
import time

import IECore
import Gaffer
import GafferUI
import GafferScene
import GafferSceneUI
import GafferAppleseed
import GafferDispatch
import imath

scriptWindow = GafferUI.ScriptWindow.acquire( script )
viewer = scriptWindow.getLayout().editors( GafferUI.Viewer )[0]
graphEditor = scriptWindow.getLayout().editors( GafferUI.GraphEditor )[0]
hierarchyView = scriptWindow.getLayout().editors( GafferSceneUI.HierarchyView )[0]

# Delay for x seconds
def __delay( delay ) :
	endtime = time.time() + delay
	while time.time() < endtime :
		GafferUI.EventLoop.waitForIdle( 1 )

# Create a random directory in `/tmp` for the dispatcher's `jobsDirectory`, so we don't clutter the user's `~gaffer` directory
__temporaryDirectory = tempfile.mkdtemp( prefix = "gafferDocs" )

# Tutorial: the MacbethTexture node in the node menu
# TODO: Automate images/tutorialNodeMenuCustomEntry.png when these tools become available:
# - API for opening the node menu and selecting a node path

# Tutorial: the MacbethTexture node in the Graph Editor
#node = Gaffer.Reference( "MacbethTexture" )
#script.addChild( node )
#node.load( os.path.expandvars( "$GAFFER_ROOT/resources/references/macbethTexture.grf" ) )
#GafferUI.EventLoop.waitForIdle()
#GafferUI.WidgetAlgo.grab( widget = graphEditor, imagePath = "images/tutorialMacbethTextureNode.png" )
# TODO: Automate images/tutorialMacbethTextureNode.png when these tools become available:
# - API for zooming in on the Graph Editor

# Demo : Macbeth chart
__imageName = "demoMacbethChart"
# Use the demo itself, but add an AppleseedRender node to render from
script["fileName"].setValue( os.path.abspath( "demos/demoMacbethChart.gfr" ) )
script.load()
script["Outputs"]["outputs"].removeChild( script["Outputs"]["outputs"]["output1"] )
script["Outputs"]["outputs"].addChild( Gaffer.ValuePlug( "output2", flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic, ) )
script["Outputs"]["outputs"]["output2"].addChild( Gaffer.StringPlug( "name", defaultValue = 'Batch/Beauty', flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic, ) )
script["Outputs"]["outputs"]["output2"].addChild( Gaffer.BoolPlug( "active", defaultValue = True, flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic, ) )
script["Outputs"]["outputs"]["output2"].addChild( Gaffer.StringPlug( "fileName", defaultValue = os.path.abspath( "images/{}.png".format( __imageName ) ), flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic, ) )
script["Outputs"]["outputs"]["output2"].addChild( Gaffer.StringPlug( "type", defaultValue = 'png', flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic, ) )
script["Outputs"]["outputs"]["output2"].addChild( Gaffer.StringPlug( "data", defaultValue = 'rgba', flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic, ) )
script["Outputs"]["outputs"]["output2"].addChild( Gaffer.CompoundDataPlug( "parameters", flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic, ) )
script["Outputs"]["outputs"]["output2"]["parameters"].addChild( Gaffer.CompoundDataPlug.MemberPlug( "quantize", flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic, ) )
script["Outputs"]["outputs"]["output2"]["parameters"]["quantize"].addChild( Gaffer.StringPlug( "name", defaultValue = 'quantize', flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic, ) )
script["Outputs"]["outputs"]["output2"]["parameters"]["quantize"].addChild( Gaffer.IntVectorDataPlug( "value", defaultValue = IECore.IntVectorData( [ 0, 0, 0, 0 ] ), flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic, ) )
script['AppleseedOptions']['options']['denoiserMode']["value"].setValue( "on" )
script['AppleseedOptions']['options']['denoiserMode']["enabled"].setValue( True )
script["StandardOptions"]["options"]["renderResolution"]["value"].setValue( imath.V2i( 480, 360 ) )
script.addChild( GafferAppleseed.AppleseedRender( "AppleseedRender" ) )
script["AppleseedRender"]["in"].setInput( script["Outputs"]["out"] )
__dispatcher = GafferDispatch.LocalDispatcher()
__dispatcher["jobsDirectory"].setValue( __temporaryDirectory )
__dispatcher.dispatch( [ script["AppleseedRender"] ] )
