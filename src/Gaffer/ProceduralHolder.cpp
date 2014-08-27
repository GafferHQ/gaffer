//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2011-2012, John Haddon. All rights reserved.
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

#include "IECore/ParameterisedProcedural.h"
#include "IECore/NullObject.h"

#include "Gaffer/ProceduralHolder.h"
#include "Gaffer/CompoundParameterHandler.h"
#include "Gaffer/TypedObjectPlug.h"

using namespace IECore;
using namespace Gaffer;

IE_CORE_DEFINERUNTIMETYPED( ProceduralHolder )

ProceduralHolder::ProceduralHolder( const std::string &name )
	:	ParameterisedHolderComputeNode( name )
{

	addChild(

		new ObjectPlug(
			"output",
			Plug::Out,
			NullObject::defaultNullObject()
		)

	);

}

void ProceduralHolder::setParameterised( IECore::RunTimeTypedPtr parameterised, bool keepExistingValues )
{
	ParameterisedProceduralPtr op = runTimeCast<ParameterisedProcedural>( parameterised );
	if( !op )
	{
		throw IECore::Exception( "Parameterised object is not an IECore::ParameterisedProcedural" );
	}

	ParameterisedHolderComputeNode::setParameterised( parameterised, keepExistingValues );

	plugDirtiedSignal()( getChild<ObjectPlug>( "output" ) );
}

void ProceduralHolder::setProcedural( const std::string &className, int classVersion )
{
	ParameterisedHolderComputeNode::setParameterised( className, classVersion, "IECORE_PROCEDURAL_PATHS" );
}

IECore::ParameterisedProcedural *ProceduralHolder::getProcedural( std::string *className, int *classVersion )
{
	return IECore::runTimeCast<IECore::ParameterisedProcedural>( getParameterised( className, classVersion ) );
}

const IECore::ParameterisedProcedural *ProceduralHolder::getProcedural( std::string *className, int *classVersion ) const
{
	return IECore::runTimeCast<IECore::ParameterisedProcedural>( getParameterised( className, classVersion ) );
}

void ProceduralHolder::affects( const Plug *input, AffectedPlugsContainer &outputs ) const
{
	ParameterisedHolderComputeNode::affects( input, outputs );

	const Plug *parametersPlug = getChild<Plug>( "parameters" );
	if( parametersPlug && parametersPlug->isAncestorOf( input ) )
	{
		outputs.push_back( getChild<ObjectPlug>( "output" ) );
	}
}

void ProceduralHolder::hash( const ValuePlug *output, const Context *context, IECore::MurmurHash &h ) const
{
	ParameterisedHolderComputeNode::hash( output, context, h );
	if( output->getName()=="output" )
	{
		std::string className;
		int classVersion;
		getParameterised( &className, &classVersion );
		h.append( className );
		h.append( classVersion );

		const ValuePlug *parametersPlug = getChild<ValuePlug>( "parameters" );
		if( parametersPlug )
		{
			parametersPlug->hash( h );
		}
	}
}

void ProceduralHolder::compute( ValuePlug *output, const Context *context ) const
{
	if( output==getChild<ObjectPlug>( "output" ) )
	{
		const_cast<CompoundParameterHandler *>( parameterHandler() )->setParameterValue();
		static_cast<ObjectPlug *>( output )->setValue( getProcedural() );
		return;
	}

	ParameterisedHolderComputeNode::compute( output, context );
}
