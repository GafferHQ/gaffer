//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2013, Image Engine Design Inc. All rights reserved.
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

#include "Gaffer/Context.h"

#include "GafferScene/Light.h"

using namespace Gaffer;
using namespace GafferScene;

IE_CORE_DEFINERUNTIMETYPED( Light );

size_t Light::g_firstPlugIndex = 0;

Light::Light( const std::string &name )
	:	ObjectSource( name, "light" )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new CompoundPlug( "parameters" ) );
}

Light::~Light()
{
}

Gaffer::CompoundPlug *Light::parametersPlug()
{
	return getChild<CompoundPlug>( g_firstPlugIndex );
}

const Gaffer::CompoundPlug *Light::parametersPlug() const
{
	return getChild<CompoundPlug>( g_firstPlugIndex );
}

void Light::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	ObjectSource::affects( input, outputs );
	
	if( input == namePlug() )
	{
		outputs.push_back( outPlug()->globalsPlug() );
	}
	else if( parametersPlug()->isAncestorOf( input ) )
	{
		outputs.push_back( sourcePlug() );
	}
}

void Light::hashGlobals( const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	ObjectSource::hashGlobals( context, parent, h );
	namePlug()->hash( h );
}

IECore::ConstCompoundObjectPtr Light::computeGlobals( const Gaffer::Context *context, const ScenePlug *parent ) const
{
	IECore::CompoundObjectPtr result = new IECore::CompoundObject;
	
	/// \todo Maybe this forwardDeclarations thing needs promoting to being a specific child
	/// of ScenePlug? Maybe it would also be nice to have a data structure dedicated to storing
	/// values along the hierarchy of a bunch of paths - PathMatcher is almost doing this internally
	/// and the internal data structure could perhaps be extracted and generalised for the purpose.
	IECore::CompoundDataPtr forwardDeclarations = new IECore::CompoundData;
	IECore::CompoundDataPtr forwardDeclaration = new IECore::CompoundData;
	forwardDeclaration->writable()["type"] = new IECore::IntData( IECore::LightTypeId );
	forwardDeclarations->writable()[ "/" + namePlug()->getValue() ] = forwardDeclaration;
	
	result->members()["gaffer:forwardDeclarations"] = forwardDeclarations;
	
	return result;
}

void Light::hashSource( const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	hashLight( context, h );
}

IECore::ConstObjectPtr Light::computeSource( const Context *context ) const
{
	return computeLight( context );
}
