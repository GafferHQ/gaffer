import Gaffer
import GafferScene
import GafferUI

def __exportRibs( menu ):
	
	scriptWindow = menu.ancestor( GafferUI.ScriptWindow )
	script = scriptWindow.scriptNode()
	
	start = script['frameRange']['start'].getValue()
	end = script['frameRange']['end'].getValue()
	if len(script.selection()):
		sel = script.selection()[0]
		if sel.typeName() == 'GafferRenderMan::RenderManRender':
			if sel['mode'].getValue() == 'generate':
				for i in range(start, end+1):
					script.context().setFrame(i)
					sel.execute( [script.context()] )
			else:
				print 'abandoning run as output is set to render!'
		else:
			print 'needs to be a renderman render node!'
	else:
		print 'select a node!'
	
GafferUI.ScriptWindow.menuDefinition(application).append( "/ben/Export Ribs", { "command" : __exportRibs } )
