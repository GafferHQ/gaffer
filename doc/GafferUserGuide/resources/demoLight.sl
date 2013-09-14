light demoLight (
    float intensity = 1;
    color lightcolor = 1;
    vector from = point "shader" (0,0,0);
    /*point to = point "shader" (0,0,1);
    float coneangle = radians(30);
    float conedeltaangle = radians(5);
    float beamdistrib = 2;*/
    float samples = 1;
    float blur = 0;
    float bias = -1;
)
{
	/*
    uniform vector A = (to - from) / length(to - from);
    float cos_coneangle = cos( coneangle );
    float cos_delta  = cos( coneangle - conedeltaangle );

    illuminate( from, A, coneangle )
    {
        float cosangle = L.A / length(L);

        color atten = pow(cosangle, beamdistrib) / (L.L);
        atten *= smoothstep(cos_coneangle, cos_delta, cosangle);
        atten *=
            transmission( Ps, from,
              "samples", samples,
              "samplecone", 0,
              "bias", bias );

        Cl = atten * intensity * lightcolor;
    }*/
    
	illuminate( from )
		Cl = (intensity * lightcolor) / (L.L) *  transmission( Ps, from, "samples", samples, "samplecone", 0, "bias", bias );
}