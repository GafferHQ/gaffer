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

#include "IECore/Op.h"
#include "IECore/MurmurHash.h"
#include "IECore/SimpleTypedParameter.h"

#include "Gaffer/Context.h"
#include "Gaffer/ExecutableOpHolder.h"
#include "Gaffer/CompoundParameterHandler.h"
#include "Gaffer/ValuePlug.h"

using namespace IECore;
using namespace Gaffer;

IE_CORE_DEFINERUNTIMETYPED( ExecutableOpHolder )

ExecutableOpHolder::ExecutableOpHolder( const std::string &name )
	:	ParameterisedHolderExecutableNode( name )
{
}

void ExecutableOpHolder::setParameterised( IECore::RunTimeTypedPtr parameterised, bool keepExistingValues )
{
	OpPtr op = runTimeCast<Op>( parameterised );
	if( !op )
	{
		throw IECore::Exception( "Parameterised object is not an IECore::Op" );
	}
	ParameterisedHolderExecutableNode::setParameterised( parameterised, keepExistingValues );
}

void ExecutableOpHolder::setOp( const std::string &className, int classVersion, bool keepExistingValues )
{
	ParameterisedHolderExecutableNode::setParameterised( className, classVersion, "IECORE_OP_PATHS", keepExistingValues );
}

IECore::Op *ExecutableOpHolder::getOp( std::string *className, int *classVersion )
{
	return IECore::runTimeCast<IECore::Op>( getParameterised( className, classVersion ) );
}

const IECore::Op *ExecutableOpHolder::getOp( std::string *className, int *classVersion ) const
{
	return IECore::runTimeCast<IECore::Op>( getParameterised( className, classVersion ) );
}

IECore::MurmurHash ExecutableOpHolder::hash( const Context *context ) const
{
	std::string className;
	int classVersion;
	if ( !getOp( &className, &classVersion ) )
	{
		return IECore::MurmurHash();
	}

	IECore::MurmurHash h = ExecutableNode::hash( context );
	h.append( className );
	h.append( classVersion );

	Context::Scope scope( context );
	const ValuePlug *parametersPlug = getChild<ValuePlug>( "parameters" );
	if( parametersPlug )
	{
		parametersPlug->hash( h );
	}

	return h;
}

void ExecutableOpHolder::execute() const
{
	// \todo Implement a way to get the CompoundObject for a given context without modifying the Op's parameter
	// and passing it explicitly in the operate call, so clients can safely call execute() from multiple threads.
	const_cast<CompoundParameterHandler *>( parameterHandler() )->setParameterValue();
	Op *op = const_cast<Op *>( getOp() );
	/// \todo: Remove this once scoping the context takes care of it for us
	substitute( op->parameters(), Context::current() );
	op->operate();
}

void ExecutableOpHolder::substitute( Parameter *parameter, const Context *context ) const
{
	if ( const CompoundParameter *compound = runTimeCast<const CompoundParameter>( parameter ) )
	{
		const CompoundParameter::ParameterVector &children = compound->orderedParameters();
		for ( CompoundParameter::ParameterVector::const_iterator it = children.begin(); it != children.end(); ++it )
		{
			substitute( const_cast<Parameter*>( it->get() ), context );
		}
	}

	if ( StringParameter *stringParm = runTimeCast<StringParameter>( parameter ) )
	{
		stringParm->setTypedValue( context->substitute( stringParm->getTypedValue() ) );
	}
}
