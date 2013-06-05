scriptWindow = GafferUI.ScriptWindow.acquire( script ) #load a suitable layout - shouldn't need this once layout is stored in script
layout = GafferUI.Layouts.create( 'user:screenGrabTest', scriptWindow.scriptNode() ) #load a suitable layout - shouldn't need this once layout is stored in script
scriptWindow.setLayout( layout ) #load a suitable layout - shouldn't need this once layout is stored in script
script.selection().clear() #make sure the Display node is active - shouldn't need this once selection is stored in script
script.selection().add(script['Display']) #make sure the Display node is active - shouldn't need this once selection is stored in script
script['RenderManRender'].execute( [script.context()] ) #