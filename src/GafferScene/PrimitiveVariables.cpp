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

#include "GafferScene/PrimitiveVariables.h"

using namespace IECore;
using namespace Gaffer;
using namespace GafferScene;

IE_CORE_DEFINERUNTIMETYPED( PrimitiveVariables );

size_t PrimitiveVariables::g_firstPlugIndex = 0;

PrimitiveVariables::PrimitiveVariables( const std::string &name )
	:	SceneElementProcessor( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new CompoundDataPlug( "primitiveVariables" ) );
	
	// Fast pass-throughs for things we don't modify
	outPlug()->attributesPlug()->setInput( inPlug()->attributesPlug() );
	outPlug()->transformPlug()->setInput( inPlug()->transformPlug() );
	outPlug()->boundPlug()->setInput( inPlug()->boundPlug() );
}

PrimitiveVariables::~PrimitiveVariables()
{
}

Gaffer::CompoundDataPlug *PrimitiveVariables::primitiveVariablesPlug()
{
	return getChild<Gaffer::CompoundDataPlug>( g_firstPlugIndex );
}

const Gaffer::CompoundDataPlug *PrimitiveVariables::primitiveVariablesPlug() const
{
	return getChild<Gaffer::CompoundDataPlug>( g_firstPlugIndex );
}

void PrimitiveVariables::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	SceneElementProcessor::affects( input, outputs );

	if( primitiveVariablesPlug()->isAncestorOf( input ) )
	{
		outputs.push_back( outPlug()->objectPlug() );
	}
}

bool PrimitiveVariables::processesObject() const
{
	return primitiveVariablesPlug()->children().size();
}

void PrimitiveVariables::hashProcessedObject( const ScenePath &path, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	primitiveVariablesPlug()->hash( h );
}

IECore::ConstObjectPtr PrimitiveVariables::computeProcessedObject( const ScenePath &path, const Gaffer::Context *context, IECore::ConstObjectPtr inputObject ) const
{
	const Primitive *inputPrimitive = runTimeCast<const Primitive>( inputObject.get() );
	if( !inputPrimitive )
	{
		return inputObject;
	}

	const CompoundDataPlug *p = primitiveVariablesPlug();
	if( !p->children().size() )
	{
		return inputObject;
	}

	PrimitivePtr result = inputPrimitive->copy();

	std::string name;
	for( CompoundDataPlug::MemberPlugIterator it( p ); it != it.end(); ++it )
	{
		IECore::DataPtr d = p->memberDataAndName( it->get(), name );
		if( d )
		{
			result->variables[name] = PrimitiveVariable( PrimitiveVariable::Constant, d );
		}
	}

	return result;
}
