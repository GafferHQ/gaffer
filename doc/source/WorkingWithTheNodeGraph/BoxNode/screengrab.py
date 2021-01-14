# BuildTarget: images/interfaceUIEditor.png
# BuildTarget: images/exampleBoxBasics.png

import os

import Gaffer
import GafferScene

import GafferUI

scriptWindow = GafferUI.ScriptWindow.acquire( script )
graphEditor = scriptWindow.getLayout().editors( GafferUI.GraphEditor )[0]

# Illustration of the basics of a Box
# script["fileName"].setValue( os.path.abspath( "scripts/illustrationBoxBasics.gfr" ) )
# TODO: Automate `images/illustrationBoxBasics.svg` when these tools become available:
# - Borders around images
# - Simple color-to-alpha-channel conversion
# - 2D curves with end caps

# Illustration of the generic uses of a Box
# script["fileName"].setValue( os.path.abspath( "scripts/illustrationBoxUses1.gfr" ) )
# script["fileName"].setValue( os.path.abspath( "scripts/illustrationBoxUses2.gfr" ) )
# script["fileName"].setValue( os.path.abspath( "scripts/illustrationBoxUses3.gfr" ) )
# TODO: Automate `images/illustrationBoxUses.png` when these tools become available:
# - 2D curves with end caps

# Illustration of Box nesting
# script["fileName"].setValue( os.path.abspath( "scripts/illustrationBoxNesting.gfr" ) )
# TODO: Automate `images/illustrationBoxNesting.svg` when these tools become available:
# - Borders around images
# - Simple color-to-alpha-channel conversion
# - 2D curves with end caps

# Illustration of importing a saved Box reference, using the example mySurfaceShaders Box
# script["fileName"].setValue( os.path.abspath( "scripts/illustrationBoxReferences.gfr" ) )
# TODO: Automate `images/illustrationBoxReferences.svg` when these tools become available:
# - Borders around images
# - 2D curves with end caps
# - Screengrabs containing the window frame

# Illustration of promoted plugs
# script["fileName"].setValue( os.path.abspath( "scripts/illustrationBoxBasics.gfr" ) )
# TODO: Automate `images/illustrationPromotedPlug.svg` when these tools become available:
# - 2D curves with end caps
# - Embed a saved window layout to script

# Task animation of boxing up a bunch of nodes
# script["fileName"].setValue( os.path.abspath( "scripts/taskBoxUpNodesBefore.gfr" ) )
# TODO: Automate `images/taskBoxUpNodes.gif` when these tools become available:
# - KB/M recording and simulated playback
# - On-screen keystroke monitor

# Task result of boxing up nodes
# script["fileName"].setValue( os.path.abspath( "scripts/taskBoxUpNodesAfter.gfr" ) )
# script.load()
# graphEditor.frame( script.children( Gaffer.Node ) )
# GafferUI.WidgetAlgo.grab( widget = graphEditor, imagePath = "images/taskBoxUpNodesResult.png" )

# Task animation of the quickest way to connect a Box
# script["fileName"].setValue( os.path.abspath( "scripts/taskConnectBox.gfr" ) )
# TODO: Automate `images/taskConnectBox.gif` when these tools become available:
# - KB/M recording and simulated playback
# - On-screen keystroke monitor

# Task animation of an alternate way of connecting a Box
# script["fileName"].setValue( os.path.abspath( "scripts/taskConnectBox.gfr" ) )
# TODO: Automate `images/taskConnectBoxAlt.gif` when these tools become available:
# - KB/M recording and simulated playback
# - On-screen keystroke monitor

# Interface capture of the passThrough plug on a BoxOut node
# script.addChild( Gaffer.BoxOut() )
# script["BoxOut"]["in"] = GafferScene.ScenePlug()
# script["BoxOut"]["passThrough"] = GafferScene.ScenePlug()
# TODO: Automate `images/interfacePassthroughPlug.png` when these tools become available:
# - Easily trigger plug tooltips to appear

# Task animation of connecting the passThrough plug
# script["fileName"].setValue( os.path.abspath( "scripts/taskConnectPassthroughPlug.gfr" ) )
# TODO: Automate `images/taskConnectPassthroughPlug.gif` when these tools become available:
# - KB/M recording and simulated playback
# - On-screen keystroke monitor

# Task animation of connecting the passThrough plug
# script["fileName"].setValue( os.path.abspath( "scripts/taskConnectPromotePlug.gfr" ) )
# TODO: Automate `images/taskPromotePlug.gif` when these tools become available:
# - KB/M recording and simulated playback
# - On-screen keystroke monitor

# Task animation of demoting a plug1
# script["fileName"].setValue( os.path.abspath( "scripts/taskDemotePlug.gfr" ) )
# TODO: Automate `images/taskDemotePlug.gif` when these tools become available:
# - KB/M recording and simulated playback
# - On-screen keystroke monitor

# Task animation of adjusting plug position
# script["fileName"].setValue( os.path.abspath( "scripts/taskAdjustPlugPosition.gfr" ) )
# TODO: Automate `images/taskAdjustPlugPosition.gif` when these tools become available:
# - KB/M recording and simulated playback
# - On-screen keystroke monitor

# Interface capture of the UI Editor, using the example mySurfaceShaders Box
script["fileName"].setValue( os.path.abspath( "scripts/illustrationBoxReferences.gfr" ) )
script.load()
UIEditorWindow = GafferUI.UIEditor.acquire( script["mySurfaceShaders"], floating=True )
GafferUI.WidgetAlgo.grab( widget = UIEditorWindow, imagePath = "images/interfaceUIEditor.png" )
del UIEditorWindow

# Box Node Basics example
script["fileName"].setValue( os.path.abspath( "../../../examples/boxBasics.gfr" ) )
script.load()
script.removeChild( script[ "Backdrop" ] )
graphEditor.frame( script.children( Gaffer.Node ) )
GafferUI.WidgetAlgo.grab( widget = graphEditor, imagePath = "images/exampleBoxBasics.png" )
