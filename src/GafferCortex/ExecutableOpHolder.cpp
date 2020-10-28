//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2013-2014, Image Engine Design Inc. All rights reserved.
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

#include "GafferCortex/ExecutableOpHolder.h"

#include "GafferCortex/CompoundParameterHandler.h"

#include "Gaffer/Context.h"
#include "Gaffer/ValuePlug.h"

#include "IECore/MurmurHash.h"
#include "IECore/Op.h"
#include "IECore/SimpleTypedParameter.h"

using namespace IECore;
using namespace GafferCortex;

GAFFER_NODE_DEFINE_TYPE( ExecutableOpHolder )

ExecutableOpHolder::ExecutableOpHolder( const std::string &name )
	:	ParameterisedHolderTaskNode( name )
{
}

void ExecutableOpHolder::setParameterised( IECore::RunTimeTypedPtr parameterised, bool keepExistingValues )
{
	OpPtr op = runTimeCast<Op>( parameterised );
	if( !op )
	{
		throw IECore::Exception( "Parameterised object is not an IECore::Op" );
	}
	ParameterisedHolderTaskNode::setParameterised( parameterised, keepExistingValues );
}

void ExecutableOpHolder::setOp( const std::string &className, int classVersion, bool keepExistingValues )
{
	ParameterisedHolderTaskNode::setParameterised( className, classVersion, "IECORE_OP_PATHS", keepExistingValues );
}

IECore::Op *ExecutableOpHolder::getOp( std::string *className, int *classVersion )
{
	return IECore::runTimeCast<IECore::Op>( getParameterised( className, classVersion ) );
}

const IECore::Op *ExecutableOpHolder::getOp( std::string *className, int *classVersion ) const
{
	return IECore::runTimeCast<IECore::Op>( getParameterised( className, classVersion ) );
}

IECore::MurmurHash ExecutableOpHolder::hash( const Gaffer::Context *context ) const
{
	std::string className;
	int classVersion;
	if ( !getOp( &className, &classVersion ) )
	{
		return IECore::MurmurHash();
	}

	IECore::MurmurHash h = ParameterisedHolderTaskNode::hash( context );
	h.append( className );
	h.append( classVersion );

	Gaffer::Context::Scope scope( context );
	if( const ParameterHandler *handler = parameterHandler() )
	{
		h.append( handler->hash() );
	}

	return h;
}

void ExecutableOpHolder::execute() const
{
	// \todo Implement a way to get the CompoundObject for a given context without modifying the Op's parameter
	// and passing it explicitly in the operate call, so clients can safely call execute() from multiple threads.
	const_cast<CompoundParameterHandler *>( parameterHandler() )->setParameterValue();
	Op *op = const_cast<Op *>( getOp() );
	op->operate();
}
