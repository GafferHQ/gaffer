import Gaffer
import GafferScene
import GafferUI

def __exportScreenGrabSession( menu ):
	
	scriptWindow = menu.ancestor( GafferUI.ScriptWindow )
	script = scriptWindow.scriptNode()

	# get current script file name. we will put the cmds file relative to it
	gfrFile = script['fileName'].getValue()

	if gfrFile == '':
		print 'WARNING: Save gfr file in to correct location first'
	else:
		# save up to capture any recent changes
		script.save()
		
		cmdsFile = gfrFile.rstrip('.gfr') + '.py'

		# open the cmds file for writing
		with open(cmdsFile, 'w') as fh:
			#put the header in
			fh.write('import IECore\n')
			fh.write('import GafferUI\n')
			fh.write('import GafferScene\n')
			fh.write('import GafferSceneUI\n')
			fh.write('import os\n')
			
			
			# get the layout from the current gaffer session and stash it in a string
			scriptWindow = GafferUI.ScriptWindow.acquire( script )
			layoutStashStr = repr( scriptWindow.getLayout() )

			# write commands to load and set the layout
			
			fh.write( 'scriptNode = script\n' ) #script is called scriptNode in layout string
			fh.write( 'scriptWindow = GafferUI.ScriptWindow.acquire( script )\n' )
			fh.write( 'layout = eval( "%s" )\n' % (layoutStashStr))
			fh.write( 'scriptWindow.setLayout( layout )\n' )
			
			
			# get the current window size and stash it 
			size = scriptWindow.size()
			
			# write command to set the window size
			fh.write( 'scriptWindow._Widget__qtWidget.resize(%i,%i)\n' % (size[0], size[1]) )
			
			
			# get the current node selection and stash it
			nodeNames = []
			for node in script.selection() :
				nodeNames.append( "'%s'" % (node.relativeName( script )) )
			
			# write commands to set the node selection
			nodesList = ','.join(nodeNames)
			fh.write( 'for nodeName in [%s]:\n' % (nodesList))
			fh.write( '\tscript.selection().add( script.descendant( nodeName ) )\n' )
			
			
			# get the current scene expansion state
			if "ui:scene:expandedPaths" in script.context().keys(): # only valid if current context is a scene (might be an image). so check
				expandedPaths = script.context()["ui:scene:expandedPaths"].value.paths()
			
				# write commands to set the scene expansion state
				fh.write( 'script.context()["ui:scene:expandedPaths"] = GafferScene.PathMatcherData( GafferScene.PathMatcher( %s ) )\n' % ( repr(expandedPaths) ))
			
			
			# get the current scene selection state
			if "ui:scene:selectedPaths" in script.context().keys():
				selectedPaths = script.context()["ui:scene:selectedPaths"]
			
				# write commands to set the scene selection
				fh.write( 'script.context()["ui:scene:selectedPaths"] = %s\n' % ( repr(selectedPaths) ))
			
			
			fh.write( '##############################################################\n' )
			fh.write( '## IMAGE SPECIFIC COMMANDS BELOW #############################\n' )



GafferUI.ScriptWindow.menuDefinition(application).append( "/ben/Export Screen Grab Session", { "command" : __exportScreenGrabSession } )



