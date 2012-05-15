move things into more modules :

	gaffercore
		- paths, utilities
		
	gaffercoreui
		- totally generic widgets, path widgets
		
	gaffergraph
	gaffergraphui

	gafferparameterised
	gafferparameterisedui
	
distinguish widgets and gadgets by module namespace?

have module name in typeName() ?

change serialisation to use parent().addChild(), and allow nested group nodes