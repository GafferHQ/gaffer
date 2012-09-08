move things into more modules :

	gaffercore
		- paths, utilities
		
	gaffercoreui
		- totally generic widgets, path widgets
		
	gaffergraph
	gaffergraphui

	gaffercortex
	gaffercortexui
	
distinguish widgets and gadgets by module namespace?

rename borderwidth parameters to something more accurate
	- consider the ContainerGadget::padding naming too

have module name in typeName() ?

change serialisation to use parent().addChild(), and allow nested group nodes

rename CompoundObjectPlug to AtomicCompoundObjectPlug?
	- and ObjectVectorPlug to AtomicObjectVectorPlug?
		- or remove this one?
			- i'm not sure we really need it