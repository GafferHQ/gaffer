import GafferUI
import GafferRenderMan
import os
scriptFile = script['fileName'].getValue()
scriptPath = os.path.dirname(scriptFile)
shaderNode = GafferRenderMan.RenderManShader('ShaderNode')
script.addChild( shaderNode )
os.environ['DL_SHADERS_PATH'] = os.environ['DL_SHADERS_PATH'] + ':' + scriptPath
shaderPath = 'annotationsExample'
shaderNode.loadShader( shaderPath )
scriptWindow = GafferUI.ScriptWindow.acquire( script )
scriptNode = script
layout = eval( "GafferUI.CompoundEditor( scriptNode, children = {'tabs': (GafferUI.NodeEditor( scriptNode ),), 'currentTab': 0} )" ) #simple single NodeEditor layout
scriptWindow.setLayout( layout )
scriptWindow._Widget__qtWidget.resize(500,700)
script.selection().clear() #make sure the Shader node is active
script.selection().add(shaderNode) #make sure the Shader node is active 