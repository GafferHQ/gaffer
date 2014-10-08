//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2014, Image Engine Design Inc. All rights reserved.
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

#include "GafferScene/Set.h"
#include "GafferScene/PathMatcherData.h"

using namespace IECore;
using namespace GafferScene;

IE_CORE_DEFINERUNTIMETYPED( Set );

size_t Set::g_firstPlugIndex = 0;

Set::Set( const std::string &name )
	:	GlobalsProcessor( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new Gaffer::StringPlug( "name", Gaffer::Plug::In, "set" ) );
	addChild( new Gaffer::StringVectorDataPlug( "paths", Gaffer::Plug::In, new StringVectorData ) );
	addChild( new Gaffer::ObjectPlug( "__pathMatcher", Gaffer::Plug::Out, new PathMatcherData ) );
}

Set::~Set()
{
}

Gaffer::StringPlug *Set::namePlug()
{
	return getChild<Gaffer::StringPlug>( g_firstPlugIndex );
}

const Gaffer::StringPlug *Set::namePlug() const
{
	return getChild<Gaffer::StringPlug>( g_firstPlugIndex );
}

Gaffer::StringVectorDataPlug *Set::pathsPlug()
{
	return getChild<Gaffer::StringVectorDataPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::StringVectorDataPlug *Set::pathsPlug() const
{
	return getChild<Gaffer::StringVectorDataPlug>( g_firstPlugIndex + 1 );
}

Gaffer::ObjectPlug *Set::pathMatcherPlug()
{
	return getChild<Gaffer::ObjectPlug>( g_firstPlugIndex + 2 );
}

const Gaffer::ObjectPlug *Set::pathMatcherPlug() const
{
	return getChild<Gaffer::ObjectPlug>( g_firstPlugIndex + 2 );
}

void Set::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	GlobalsProcessor::affects( input, outputs );

	if( pathsPlug() == input )
	{
		outputs.push_back( pathMatcherPlug() );
	}
	else if(
		namePlug() == input ||
		pathMatcherPlug() == input
	)
	{
		outputs.push_back( outPlug()->globalsPlug() );
	}
}

void Set::hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	GlobalsProcessor::hash( output, context, h );

	if( output == pathMatcherPlug() )
	{
		pathsPlug()->hash( h );
	}
}

void Set::compute( Gaffer::ValuePlug *output, const Gaffer::Context *context ) const
{
	if( output == pathMatcherPlug() )
	{
		ConstStringVectorDataPtr paths = pathsPlug()->getValue();
		PathMatcherDataPtr pathMatcherData = new PathMatcherData;
		pathMatcherData->writable().init( paths->readable().begin(), paths->readable().end() );
		static_cast<Gaffer::ObjectPlug *>( output )->setValue( pathMatcherData );
		return;
	}

	GlobalsProcessor::compute( output, context );
}

void Set::hashProcessedGlobals( const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	namePlug()->hash( h );
	pathMatcherPlug()->hash( h );
}

IECore::ConstCompoundObjectPtr Set::computeProcessedGlobals( const Gaffer::Context *context, IECore::ConstCompoundObjectPtr inputGlobals ) const
{
	std::string name = namePlug()->getValue();
	if( !name.size() )
	{
		return inputGlobals;
	}

	IECore::CompoundObjectPtr result = new IECore::CompoundObject;
	// Since we're not going to modify any existing members other than the sets,
	// and our result becomes const on returning it, we can directly reference
	// the input members in our result without copying. We have to be careful not
	// to modify the input sets though.
	result->members() = inputGlobals->members();

	CompoundDataPtr sets = new CompoundData;
	if( const CompoundData *inputSets = inputGlobals->member<CompoundData>( "gaffer:sets" ) )
	{
		sets->writable() = inputSets->readable();
	}
	result->members()["gaffer:sets"] = sets;

	ConstObjectPtr set = pathMatcherPlug()->getValue();
	// const cast is acceptable because we're just using it to place a const object into a
	// container that will be treated as const everywhere immediately after return from this method.
	sets->writable()[name] = const_cast<Data *>( static_cast<const Data *>( set.get() ) );

	return result;
}
