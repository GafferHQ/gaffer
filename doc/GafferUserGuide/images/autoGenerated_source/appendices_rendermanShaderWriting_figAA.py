import GafferRenderMan
import os

scriptFile = script['fileName'].getValue()
scriptPath = os.path.dirname(scriptFile)
shaderNode = GafferRenderMan.RenderManShader("shaderNode")
script.addChild( shaderNode )
shaderNode["name"].setValue('annotationsDemo')
shaderNode["type"].setValue('ri:surface')
shaderPath = os.path.join( scriptPath, 'annotationsExample' )
shaderNode.loadShader( shaderPath )

scriptWindow = GafferUI.ScriptWindow.acquire( script ) #load a suitable layout - shouldn't need this once layout is stored in script
layout = GafferUI.Layouts.create( 'user:screenGrabTest', scriptWindow.scriptNode() ) #load a suitable layout - shouldn't need this once layout is stored in script
scriptWindow.setLayout( layout ) #load a suitable layout - shouldn't need this once layout is stored in script
script.selection().clear() #make sure the Shader node is active - shouldn't need this once selection is stored in script
script.selection().add(script['annotationsDemo']) #make sure the Shader node is active - shouldn't need this once selection is stored in script