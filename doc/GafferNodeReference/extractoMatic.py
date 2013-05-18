import IECore
import Gaffer
import GafferUI

import inspect
import sys,os


__PLACEHOLDERSTRING__ = "!!!__EMPTY__!!!"

def addModuleDefinitionToDoc( doc, modulename ):
	#format for asciidoc. First level header
	string = "\n== %s anchor:module_%s[]\n" % (modulename,modulename)
	doc.write( string )

def addNodeDefinitionToDoc( doc, nodename, node ):
	#start with second level header for node name
	string = "\n\n=== %s anchor:node_%s[]\n" % (nodename,nodename)
	doc.write(string)
	
	#get node description from metadata
	desc = GafferUI.Metadata.nodeDescription(node)
	
	#record the node description from the metadata
	if desc == "":
		desc = __PLACEHOLDERSTRING__
	string = "%s\n\n" % (desc)
	string += ".Plugs\n"
	doc.write(string)

def addPlugDefinitionToDoc( doc, plugName, plugDescription, plugDepth ):
	#asciidoc uses '::',':::','::::' to define term:definiton indent level
	indentLevel = ':'
	for i in range(0,plugDepth):
		indentLevel += ':'
	
	if plugDescription == "":
		string = "%s%s %s\n" % (plugName, indentLevel, __PLACEHOLDERSTRING__)
	else:
		string = "%s%s %s\n" % (plugName, indentLevel, plugDescription)
	doc.write(string)
	
def checkForChildPlugsAndAddToDoc( doc, plug , inDepth ):
	depth = inDepth + 1
	
	childPlugs = plug.children()

	#if this plug is not a compound plug, or is a IO plug, or is made up of rgb/xyz data we don't need to go any deeper	
	if len(childPlugs) == 0 or isPlugPluggable( plug ) or plug.typeName() in (['Color3fPlug', 'Color4fPlug', 'V3fPlug']):
		addPlugDefinitionToDoc( doc, plug.getName(), GafferUI.Metadata.plugDescription(plug), depth )
	else:
		#we have children so recursively check for more children
		addPlugDefinitionToDoc( doc, plug.getName(), GafferUI.Metadata.plugDescription(plug), depth )
		for childPlug in childPlugs:
			checkForChildPlugsAndAddToDoc( doc, childPlug, depth )


def isPlugPluggable( plug ):
	if GafferUI.Nodule.create(plug) == None:
		return False
	else:
		return True




#open file ready to write asciidoc formatted data into
targetDoc = open('./dynamicContent.txt', 'w')


#build list of modules available for gaffer. nodes are split across modules
modules = []
for path in sys.path:
	if 'gaffer' in path and os.path.exists( path ):
		for module in os.listdir( path ):
			if module.startswith( 'Gaffer' ) and not module.endswith('Test'):
				modules.append( module )
modules.sort()

#now import all the modules
imported = map( __import__, modules )


#loop over each module, find it's contents, check if those are nodes, then pull all the info about plugs
for i in range(len(modules)):
	
	#prune the UI files off the list of modules to inspect (they're needed to us to get Metadata, but don't contain nodes)
	if modules[i].endswith('UI'):
		continue
	
	#print the module name into the doc
	addModuleDefinitionToDoc( targetDoc, modules[i] )

	#get all the members for this module	
	moduleContents = dir( imported[i] )
	
	#loop over the members
	for name in moduleContents:
		
		item = getattr( imported[i], name )
		#check each member of the module to see if it's a class and inherits from Gaffer.Node - meaning that is is a node type
		if not ( inspect.isclass( item ) and issubclass( item, Gaffer.Node ) ) :
			continue
		
		#catch the case where we have abstract nodes that are the source of real nodes (i.e Shader -> RenderManShader)
		try :
			node = item()
		except RuntimeError, e :
			assert( str( e ) == "This class cannot be instantiated from Python" )
			continue
		
		''' DEBUG temporarily only process one node for brevity
		if name != 'StandardOptions':
			continue
		'''
		
		
		#now we have all the information we need for this node, print it into the asciidoc file
		addNodeDefinitionToDoc( targetDoc, name, node)
		
		#now we need to loop over all plugs (the children of the node)
		for plug in node.children():
			if not plug.getName().startswith('__'): #skip special plugs
				
				#handle special cases where we know we want to skip plugs with specific names
				plugsBlacklist = ['user']
				if not plug.getName() in plugsBlacklist:
				
					#print to doc both the name of the plug (i.e fileName) and the metadata description ('The path to the file to be loaded')
					#addPlugDefinitionToDoc( targetDoc, [plug.getName(), GafferUI.Metadata.plugDescription(plug)] )
					checkForChildPlugsAndAddToDoc( targetDoc, plug, 0 )
					
					''' TODO - refine this 
					#start of some work to categorise plugs - IO plugs, control plugs etc
					if isPlugPluggable( plug ):
						print '%s is a pluggable plug' % (plug.getName())
					'''



#TODO
# plugs of type ScenePlug to be segregated from paramater type plugs
# present compound plugs with .name .value .enabled children in a better way. Large amount of this info is redundant. (related to option/attr overriders)
# handle case where options.thing.value.x doesn't draw properly as it's too deep for asciidoc term:definition lists


#tidy up
targetDoc.close()