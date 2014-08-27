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

#include "IECore/Op.h"
#include "IECore/MurmurHash.h"

#include "Gaffer/OpHolder.h"
#include "Gaffer/CompoundParameterHandler.h"
#include "Gaffer/ValuePlug.h"

using namespace IECore;
using namespace Gaffer;

IE_CORE_DEFINERUNTIMETYPED( OpHolder )

OpHolder::OpHolder( const std::string &name )
	:	ParameterisedHolderComputeNode( name ), m_resultParameterHandler( 0 )
{
}

void OpHolder::setParameterised( IECore::RunTimeTypedPtr parameterised, bool keepExistingValues )
{
	OpPtr op = runTimeCast<Op>( parameterised );
	if( !op )
	{
		throw IECore::Exception( "Parameterised object is not an IECore::Op" );
	}
	ParameterisedHolderComputeNode::setParameterised( parameterised, keepExistingValues );

	m_resultParameterHandler = ParameterHandler::create( const_cast<Parameter *>( op->resultParameter() ) );
	if( !m_resultParameterHandler )
	{
		throw IECore::Exception( "Couldn't create handler for result parameter" );
	}

	ValuePlugPtr resultPlug = runTimeCast<ValuePlug>( m_resultParameterHandler->setupPlug( this, Plug::Out ) );
	if( !resultPlug )
	{
		throw IECore::Exception( "Result plug is not derived from ValuePlug" );
	}

	plugDirtiedSignal()( resultPlug.get() );
}

void OpHolder::setOp( const std::string &className, int classVersion, bool keepExistingValues )
{
	ParameterisedHolderComputeNode::setParameterised( className, classVersion, "IECORE_OP_PATHS", keepExistingValues );
}

IECore::Op *OpHolder::getOp( std::string *className, int *classVersion )
{
	return IECore::runTimeCast<IECore::Op>( getParameterised( className, classVersion ) );
}

const IECore::Op *OpHolder::getOp( std::string *className, int *classVersion ) const
{
	return IECore::runTimeCast<IECore::Op>( getParameterised( className, classVersion ) );
}

void OpHolder::affects( const Plug *input, AffectedPlugsContainer &outputs ) const
{
	ConstPlugPtr parametersPlug = getChild<Plug>( "parameters" );
	if( parametersPlug && parametersPlug->isAncestorOf( input ) )
	{
		const ValuePlug *resultPlug = getChild<ValuePlug>( "result" );
		if( resultPlug )
		{
			outputs.push_back( resultPlug );
		}
	}
}

void OpHolder::hash( const ValuePlug *output, const Context *context, IECore::MurmurHash &h ) const
{
	ParameterisedHolderComputeNode::hash( output, context, h );
	if( output->getName()=="result" )
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

void OpHolder::compute( ValuePlug *output, const Context *context ) const
{
	if( output->getName()=="result" )
	{
		const_cast<CompoundParameterHandler *>( parameterHandler() )->setParameterValue();
		const_cast<Op *>( getOp() )->operate();
		m_resultParameterHandler->setPlugValue();
		return;
	}

	ParameterisedHolderComputeNode::compute( output, context );
}
