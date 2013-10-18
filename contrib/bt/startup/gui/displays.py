import IECore

import GafferScene

GafferScene.Displays.registerDisplay( 
	"AOVs/beauty",
	IECore.Display( 
		"/tmp/beauty.####.exr",
		"exr",
		"rgba",
		{
			"quantize" : IECore.IntVectorData( [ 0, 0, 0, 0 ] ),
		}
	)
)

GafferScene.Displays.registerDisplay( 
	"AOVs/diffuse",
	IECore.Display( 
		"/tmp/diffuse.####.exr",
		"exr",
		"aov_diffuse",
		{
			"quantize" : IECore.IntVectorData( [ 0, 0, 0, 0 ] ),
		}
	)
)

GafferScene.Displays.registerDisplay( 
	"AOVs/specular",
	IECore.Display( 
		"/tmp/specular.####.exr",
		"exr",
		"aov_specular",
		{
			"quantize" : IECore.IntVectorData( [ 0, 0, 0, 0 ] ),
		}
	)
)

GafferScene.Displays.registerDisplay( 
	"AOVs/indirectDiffuse",
	IECore.Display( 
		"/tmp/indirectDiffuse.####.exr",
		"exr",
		"aov_indirectDiffuse",
		{
			"quantize" : IECore.IntVectorData( [ 0, 0, 0, 0 ] ),
		}
	)
)

GafferScene.Displays.registerDisplay( 
	"AOVs/indirectSpecular",
	IECore.Display( 
		"/tmp/indirectSpecular.####.exr",
		"exr",
		"aov_indirectSpecular",
		{
			"quantize" : IECore.IntVectorData( [ 0, 0, 0, 0 ] ),
		}
	)
)