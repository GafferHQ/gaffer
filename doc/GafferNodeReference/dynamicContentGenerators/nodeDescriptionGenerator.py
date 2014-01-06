'''
This is run by 'gaffer python' via the INSTALL.py script.
Generates asciidoc formatted description of the available Gaffer nodes and their plugs.
'''

import IECore
import Gaffer
import GafferUI

import inspect
import sys,os


__PLACEHOLDERSTRING = "!!!__EMPTY__!!!"

def addModuleDefinitionToDoc( doc, modulename ):
	#format for asciidoc. First level header
	string = "\n== %s anchor:module_%s[]\n" % (modulename,modulename)
	doc.write( string )

def addNodeDefinitionToDoc( doc, nodename, node ):
	#start with second level header for node name
	string = "\n\n=== %s anchor:node_%s[]\n" % (nodename,nodename)
	doc.write(string)
	
	#get node description from metadata
	desc = Gaffer.Metadata.nodeDescription(node)
	
	#record the node description from the metadata
	if desc == "":
		desc = __PLACEHOLDERSTRING
	string = "%s\n\n" % (desc)

	if len(node.children()) > 1: #if the node has plugs other than 'user' plug:
		#we're going to enter this title with it's own class so we can style it specifically
		string += '+++<div class="nonimage_title">+++Plugs:+++</div>+++\n\n'
		
	doc.write(string)

def addPlugDefinitionToDoc( doc, plugName, plugDescription, plugType, plugDepth ):
	#asciidoc uses '::',':::','::::' to define term:definiton indent level
	indentLevel = (':' * plugDepth) + ':'
	#however it only offers those three levels. so for more we have to use ';;'
	if plugDepth > 3:
		indentLevel = ';;'
	
	if plugDescription == "":
		plugDescription = __PLACEHOLDERSTRING
	
	#include the plug type, then the wordy description. wrap description in an explicit <p> to split it onto a new line
	plugDescription = "`%s`+++<p>+++%s+++</p>+++" % ( plugType, plugDescription)
	
	string = "%s%s %s\n" % (plugName, indentLevel, plugDescription)
	
	doc.write(string)

def checkForChildPlugsAndAddToDoc( doc, plug , inDepth ):
	depth = inDepth + 1
	
	childPlugs = plug.children()
	
	#if this plug is not a compound plug, or is a IO plug, or is made up of rgb/xyz data we don't need to go any deeper
	endPlugs = ['Gaffer::Color3fPlug', 'Gaffer::Color4fPlug', 'Gaffer::V3fPlug']#, 'Gaffer::CompoundDataPlug::MemberPlug']
	if len(childPlugs) == 0 or isPlugPluggable( plug ) or plug.typeName() in endPlugs:
		addPlugDefinitionToDoc( doc, plug.getName(), Gaffer.Metadata.plugDescription(plug), plug.typeName(), depth )
		
	elif plug.typeName() == 'Gaffer::CompoundDataPlug::MemberPlug':
		#special case for these compound plugs that have the enable/disable check.
		#we will promote the type of their child 'value' plug to this level.
		valueType = ''
		for cplug in childPlugs:
			if cplug.getName() == 'value':
				valueType = cplug.typeName()
		
		addPlugDefinitionToDoc( doc, plug.getName()+'.value', Gaffer.Metadata.plugDescription(plug), valueType, depth )
		
	else:
		#we have children so recursively check for more children
		addPlugDefinitionToDoc( doc, plug.getName(), Gaffer.Metadata.plugDescription(plug), plug.typeName(), depth )
		for childPlug in childPlugs:
			checkForChildPlugsAndAddToDoc( doc, childPlug, depth )

def isPlugPluggable( plug ):
	if GafferUI.Nodule.create(plug) == None:
		return False
	else:
		return True




#open file ready to write asciidoc formatted data into
with open('./nodeDescription_dynamicContent.txt', 'w') as targetDoc:

	#build list of modules available for gaffer. nodes are split across modules
	modules = []
	for path in sys.path:
		if 'gaffer' in path and os.path.exists( path ) and path != os.getcwd():
			for module in os.listdir( path ):
				if module.startswith( 'Gaffer' ) and not module.endswith('Test'):
					modules.append( module )
	modules.sort()
	
	
	#now import all the modules
	# make some effort to handle optional modules...
	# if we don't have dependencies (arnold, 3delight etc) we should still be able to continue
	imported = []
	skip = []
	for module in modules:
		try:
			imported.append( __import__(module) )
		except ImportError:
			skip.append(module) # make a note that this module should be skipped
			print "Error importing module [ %s ]. Check availabilty of dependencies." % (module)
	
	# take any modules that failed to import properly out of the master list
	for module in skip:
		if module in modules:
			modules.remove(module)
	
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
			#check each member of the module to make sure it's a class and inherits from Gaffer.Node (meaning that it -is- a node type)
			if not ( inspect.isclass( item ) and issubclass( item, Gaffer.Node ) ) :
				continue
			
			#catch the case where we have abstract nodes that are the source of real nodes (i.e Shader -> RenderManShader)
			try :
				node = item()
			except RuntimeError, e :
				assert( str( e ) == "This class cannot be instantiated from Python" )
				continue
			
			#also skip nodes that have been inherited from. these are lowlevel nodes that users wont be expected to interact with
			#user would interact with the subclasses.
			if item.__subclasses__():
				continue
			
			#now we have all the information we need for this node (including an instance of the node),
			#so print it into the asciidoc file
			addNodeDefinitionToDoc( targetDoc, name, node)
			
			#now we need to loop over all plugs (the children of the node)
			##sort the tuple of plugs alphabetically by result of getName
			plugs = node.children()
			plugs = sorted( plugs, key=lambda x:x.getName() )
			for plug in plugs:
				if not plug.getName().startswith('__'): #skip special plugs
					
					#handle special cases where we know we want to skip plugs with specific names
					plugsBlacklist = ['user']
					if not plug.getName() in plugsBlacklist:
						
						#print to doc both the name of the plug (e.g. fileName)
						#and the metadata description ('The path to the file to be loaded')
						#this function also recursively checks for child plugs for printing too
						checkForChildPlugsAndAddToDoc( targetDoc, plug, 0 )
