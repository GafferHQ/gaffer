//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2014, John Haddon. All rights reserved.
//  
//  Redistribution and use in source and binary forms, with or without
//  modification, are permitted provided that the following conditions are
//  met:
//  
//      * Redistributions of source code must retain the above
//        copyright notice, this list of conditions and the following
//        disclaimer.
//  
//      * Redistributions in binary form must reproduce the above
//        copyright notice, this list of conditions and the following
//        disclaimer in the documentation and/or other materials provided with
//        the distribution.
//  
//      * Neither the name of John Haddon nor the names of
//        any other contributors to this software may be used to endorse or
//        promote products derived from this software without specific prior
//        written permission.
//  
//  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS
//  IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
//  THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
//  PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR
//  CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
//  EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
//  PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
//  PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
//  LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
//  NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
//  SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
//  
//////////////////////////////////////////////////////////////////////////

#ifndef GAFFEROSL_OBJECTPROCESSING_H
#define GAFFEROSL_OBJECTPROCESSING_H

float inFloat( string name, float defaultValue )
{
	float result = defaultValue;
	getattribute( name, result );
	return result;
}

color inColor( string name, color defaultValue )
{
	color result = defaultValue;
	getattribute( name, result );
	return result;
}

point inPoint( string name, point defaultValue )
{
	point result = defaultValue;
	getattribute( name, result );
	return result;
}

vector inVector( string name, vector defaultValue )
{
	vector result = defaultValue;
	getattribute( name, result );
	return result;
}

normal inNormal( string name, normal defaultValue )
{
	normal result = defaultValue;
	getattribute( name, result );
	return result;
}

closure color outFloat( string name, float value )
{
	return debug( name, "type", "float", "value", color( value ) );
}

closure color outColor( string name, color value )
{
	return debug( name, "type", "color", "value", color( value ) );
}

closure color outPoint( string name, point value )
{
	return debug( name, "type", "point", "value", color( value ) );
}

closure color outVector( string name, vector value )
{
	return debug( name, "type", "vector", "value", color( value ) );
}

closure color outNormal( string name, normal value )
{
	return debug( name, "type", "normal", "value", color( value ) );
}

#endif // GAFFEROSL_OBJECTPROCESSING_H
