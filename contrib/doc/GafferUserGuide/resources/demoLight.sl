light demoLight (
	float intensity = 1;
	color lightcolor = 1;
	vector from = vector "shader" (0,0,0);
	float samples = 1;
	float blur = 0;
	float bias = -1;
)
{
	point pfrom = point "shader" (xcomp(from),ycomp(from),zcomp(from));
	illuminate( pfrom )
		Cl = (intensity * lightcolor) / (L.L) *  transmission( Ps, pfrom, "samples", samples, "samplecone", 0, "bias", bias );
}
