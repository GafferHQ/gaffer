//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2012, John Haddon. All rights reserved.
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

#include "GafferScene/Attributes.h"

using namespace IECore;
using namespace Gaffer;
using namespace GafferScene;

IE_CORE_DEFINERUNTIMETYPED( Attributes );

size_t Attributes::g_firstPlugIndex = 0;

Attributes::Attributes( const std::string &name )
	:	SceneElementProcessor( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new CompoundDataPlug( "attributes" ) );
	addChild( new BoolPlug( "global", Plug::In, false ) );
}

Attributes::~Attributes()
{
}

Gaffer::CompoundDataPlug *Attributes::attributesPlug()
{
	return getChild<Gaffer::CompoundDataPlug>( g_firstPlugIndex );
}

const Gaffer::CompoundDataPlug *Attributes::attributesPlug() const
{
	return getChild<Gaffer::CompoundDataPlug>( g_firstPlugIndex );
}

Gaffer::BoolPlug *Attributes::globalPlug()
{
	return getChild<Gaffer::BoolPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::BoolPlug *Attributes::globalPlug() const
{
	return getChild<Gaffer::BoolPlug>( g_firstPlugIndex + 1 );
}

void Attributes::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	SceneElementProcessor::affects( input, outputs );

	if( attributesPlug()->isAncestorOf( input ) || input == globalPlug() )
	{
		outputs.push_back( outPlug()->attributesPlug() );
		outputs.push_back( outPlug()->globalsPlug() );
	}
}

void Attributes::hashGlobals( const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	if( globalPlug()->getValue() )
	{
		// We will modify the globals. Bypass the SceneElementProcessor::hashGlobals()
		// because it's a pass-through and we need to compute a proper hash instead.
		FilteredSceneProcessor::hashGlobals( context, parent, h );
		inPlug()->globalsPlug()->hash( h );
		attributesPlug()->hash( h );
	}
	else
	{
		// We won't modify the globals - pass through the hash.
		h = inPlug()->globalsPlug()->hash();
	}
}

IECore::ConstCompoundObjectPtr Attributes::computeGlobals( const Gaffer::Context *context, const ScenePlug *parent ) const
{
	ConstCompoundObjectPtr inputGlobals = inPlug()->globalsPlug()->getValue();
	if( !globalPlug()->getValue() )
	{
		return inputGlobals;
	}

	const CompoundDataPlug *p = attributesPlug();
	IECore::CompoundObjectPtr result = inputGlobals->copy();

	std::string name;
	for( CompoundDataPlug::MemberPlugIterator it( p ); it != it.end(); ++it )
	{
		IECore::DataPtr d = p->memberDataAndName( it->get(), name );
		if( d )
		{
			result->members()["attribute:" + name] = d;
		}
	}

	return result;
}

bool Attributes::processesAttributes() const
{
	return attributesPlug()->children().size() && !globalPlug()->getValue();
}

void Attributes::hashProcessedAttributes( const ScenePath &path, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	attributesPlug()->hash( h );
}

IECore::ConstCompoundObjectPtr Attributes::computeProcessedAttributes( const ScenePath &path, const Gaffer::Context *context, IECore::ConstCompoundObjectPtr inputAttributes ) const
{
	const CompoundDataPlug *ap = attributesPlug();
	if( !ap->children().size() )
	{
		return inputAttributes;
	}

	CompoundObjectPtr result = inputAttributes->copy();
	ap->fillCompoundObject( result->members() );

	return result;
}
