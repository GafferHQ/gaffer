//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2015, Image Engine Design Inc. All rights reserved.
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

#ifndef GAFFEROSL_EXPRESSION_H
#define GAFFEROSL_EXPRESSION_H

int context( string name, int defaultValue )
{
	int result = defaultValue;
	getattribute( "gaffer:context", name, result );
	return result;
}

int context( string name )
{
	return context( name, 0 );
}

float context( string name, float defaultValue )
{
	float result = defaultValue;
	getattribute( "gaffer:context", name, result );
	return result;
}

float context( string name )
{
	return context( name, 0.0 );
}

color context( string name, color defaultValue )
{
	color result = defaultValue;
	getattribute( "gaffer:context", name, result );
	return result;
}

color context( string name )
{
	return context( name, color( 0.0 ) );
}

vector context( string name, vector defaultValue )
{
	vector result = defaultValue;
	getattribute( "gaffer:context", name, result );
	return result;
}

vector context( string name )
{
	return context( name, vector( 0.0 ) );
}

string context( string name, string defaultValue )
{
	string result = defaultValue;
	getattribute( "gaffer:context", name, result );
	return result;
}

string context( string name )
{
	return context( name, "" );
}

// Vector context variable queries with index

int contextElement( string name, int index, int defaultValue )
{
	int result = defaultValue;
	getattribute( "gaffer:context", name, index, result );
	return result;
}

int contextElement( string name, int index )
{
	return contextElement( name, index, 0 );
}

float contextElement( string name, int index, float defaultValue )
{
	float result = defaultValue;
	getattribute( "gaffer:context", name, index, result );
	return result;
}

float contextElement( string name, int index )
{
	return contextElement( name, index, 0.0 );
}

color contextElement( string name, int index, color defaultValue )
{
	color result = defaultValue;
	getattribute( "gaffer:context", name, index, result );
	return result;
}

color contextElement( string name, int index )
{
	return contextElement( name, index, color( 0.0 ) );
}

vector contextElement( string name, int index, vector defaultValue )
{
	vector result = defaultValue;
	getattribute( "gaffer:context", name, index, result );
	return result;
}

vector contextElement( string name, int index )
{
	return contextElement( name, index, vector( 0.0 ) );
}

string contextElement( string name, int index, string defaultValue )
{
	string result = defaultValue;
	getattribute( "gaffer:context", name, index, result );
	return result;
}

string contextElement( string name, int index )
{
	return contextElement( name, index, "" );
}

#endif // GAFFEROSL_EXPRESSION_H
