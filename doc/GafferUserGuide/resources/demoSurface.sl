surface demoSurface(
	uniform color diffuseCol = color(0.18,0.18,0.18);
	uniform color specularCol = color(0.18,0.18,0.18);
	uniform float specularRoughness = 0.1;
	uniform color ambientCol = color(0.0,0.0,0.0);
)
{
	normal _N = normalize(N);
	vector _V = - normalize(I);
	
	Ci = specular(_N,_V,specularRoughness) * specularCol + diffuse(_N) * diffuseCol + ambientCol;
	Oi = 1;
}