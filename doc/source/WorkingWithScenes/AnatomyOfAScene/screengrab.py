# BuildTarget: images/hierarchyView.png
# BuildTarget: images/sceneInspector.png
# BuildTarget: images/sceneInspectorAttributesSection.png
# BuildTarget: images/sceneInspectorBoundSection.png
# BuildTarget: images/sceneInspectorObjectSection.png
# BuildTarget: images/sceneInspectorTransformSection.png

import IECore
import time

import Gaffer
import GafferUI

import GafferScene
import GafferSceneUI
import GafferOSL

# Delay for x seconds
def __delay( delay ) :
	endtime = time.time() + delay
	while time.time() < endtime :
		GafferUI.EventLoop.waitForIdle( 1 )

# Create and connect nodes
script["SceneReader"] = GafferScene.SceneReader()
script["ShaderAssignment"] = GafferScene.ShaderAssignment()
script["ShaderAssignment"]["in"].setInput( script["SceneReader"]["out"] )
script["Constant"] = GafferOSL.OSLShader()
script["Constant"].loadShader( "Surface/Constant" )
script["ShaderAssignment"]["shader"].setInput( script["Constant"]["out"] )
script["StandardAttributes"] = GafferScene.StandardAttributes( "StandardAttributes" )
script["StandardAttributes"]["in"].setInput( script["ShaderAssignment"]["out"] )
script["Set"] = GafferScene.Set()
script["Set"]["in"].setInput( script["StandardAttributes"]["out"] )

# Set node plug values
script["SceneReader"]["fileName"].setValue( "${GAFFER_ROOT}/resources/gafferBot/caches/gafferBot.scc" )
script["StandardAttributes"]["attributes"]["visibility"]["enabled"].setValue( True )
script["Set"]["name"].setValue( "hands" )
script["Set"]["paths"].setValue( IECore.StringVectorData( [ '/GAFFERBOT' ] ) )
script.setFocus( script["Set"] )
__path = "/GAFFERBOT/C_torso_GRP/R_armUpper_GRP/R_armLower_GRP/R_clawBottom_GRP/R_clawBottom_CPT/R_clawBottom001_REN"

# The Scene Inspector
__paths = IECore.PathMatcher( [ __path ] )
GafferSceneUI.ScriptNodeAlgo.expandInVisibleSet( script, __paths )
GafferSceneUI.ScriptNodeAlgo.expandDescendantsInVisibleSet( script, __paths, script["SceneReader"]["out"] )
GafferSceneUI.ScriptNodeAlgo.setSelectedPaths( script, __paths )
scriptWindow = GafferUI.ScriptWindow.acquire( script )
GafferSceneUI.ScriptNodeAlgo.setVisibleSet( script, GafferScene.VisibleSet( expansions = IECore.PathMatcher( [ __path ] ) ) )
hierarchyView = scriptWindow.getLayout().editors( GafferSceneUI.HierarchyView )[0]
__delay( 1.0 )
GafferUI.WidgetAlgo.grab( widget = hierarchyView, imagePath = "images/hierarchyView.png" )

# The Selection tab of the Scene Inspector with a location selected
script.setFocus( script["SceneReader"] )
with GafferUI.Window( "Scene Inspector" ) as window :

	sceneInspector = GafferSceneUI.SceneInspector( script )

window._qtWidget().resize( 512, 320 )
window.setVisible( True )
GafferUI.WidgetAlgo.grab( widget = sceneInspector, imagePath = "images/sceneInspector.png" )

# Each section of the Selection tab of the Scene Inspector with a location selected
from GafferSceneUI.SceneInspector import __TransformSection, __BoundSection, __ObjectSection, __AttributesSection

for imageName, sectionClass in [
	( "TransformSection.png", __TransformSection ),
	( "BoundSection.png", __BoundSection ),
	( "ObjectSection.png", __ObjectSection ),
	( "AttributesSection.png", __AttributesSection )
] :

	section = sectionClass()
	section._Section__collapsible.setCollapsed( False )

	with GafferUI.Window( "Property" ) as window :

		sceneInspector = GafferSceneUI.SceneInspector( script, sections = [ section ] )
		sceneInspector.setNodeSet( Gaffer.StandardSet( [ script["Set"] ] ) )
		sceneInspector.setTargetPaths( [ __path ] )

	window.resizeToFitChild()
	window.setVisible( True )
	__delay( 0.5 )

	GafferUI.WidgetAlgo.grab( widget = sceneInspector, imagePath = "images/sceneInspector" + imageName )
