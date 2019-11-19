# Replaces all usage of the `Set.paths` plug with a PathFilter
# connected to `Set.filter`. This can be used to assess the performance
# impact of deprecating the `paths` plug and always requiring a filter
# to be used.

import GafferScene

for s in GafferScene.Set.RecursiveRange( root ) :

	if not s["paths"].isSetToDefault() :

		pathFilter = GafferScene.PathFilter()
		if s["paths"].getInput() :
			pathFilter["paths"].setInput( s["paths"].getInput() )
			s["paths"].setInput( None )
		else :
			pathFilter["paths"].setValue( s["paths"].getValue() )
			s["paths"].setToDefault()

		s.parent().addChild( pathFilter )

		if s["filter"].getInput() :
			unionFilter = GafferScene.UnionFilter()
			unionFilter["in"][0].setInput( s["filter"].getInput() )
			unionFilter["in"][1].setInput( pathFilter["out"] )
			s["filter"].setInput( unionFilter["out"] )
			s.parent().addChild( unionFilter )
		else :
			s["filter"].setInput( pathFilter["out"] )

		print "Replaced {}.paths with PathFilter".format( s.relativeName( root ) )
