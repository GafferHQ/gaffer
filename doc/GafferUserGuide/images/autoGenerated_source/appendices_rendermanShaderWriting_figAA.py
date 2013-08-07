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
scriptWindow = GafferUI.ScriptWindow.acquire( script ) #load a suitable layout - shouldn't need this once layout is stored in script
layouts = GafferUI.Layouts.acquire( application ) #load a suitable layout - shouldn't need this once layout is stored in script
layout = layouts.create( 'user:screenGrabJustNodeEditor', scriptWindow.scriptNode() ) #load a suitable layout - shouldn't need this once layout is stored in script
scriptWindow.setLayout( layout ) #load a suitable layout - shouldn't need this once layout is stored in script
script.selection().clear() #make sure the Shader node is active - shouldn't need this once selection is stored in script
script.selection().add(shaderNode) #make sure the Shader node is active - shouldn't need this once selection is stored in script