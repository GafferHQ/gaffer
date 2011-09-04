//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2011, John Haddon. All rights reserved.
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

#include "Gaffer/OpHolder.h"
#include "Gaffer/CompoundParameterHandler.h"
#include "Gaffer/ValuePlug.h"

using namespace IECore;
using namespace Gaffer;

IE_CORE_DEFINERUNTIMETYPED( OpHolder )

OpHolder::OpHolder( const std::string &name )
	:	ParameterisedHolderNode( name ), m_resultParameterHandler( 0 )
{
}
			
void OpHolder::setParameterised( IECore::RunTimeTypedPtr parameterised )
{
	OpPtr op = runTimeCast<Op>( parameterised );
	if( !op )
	{
		throw IECore::Exception( "Parameterised object is not an IECore::Op" );
	}
	ParameterisedHolderNode::setParameterised( parameterised );
		
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
	resultPlug->setDirty();
}

void OpHolder::setOp( const std::string &className, int classVersion )
{
	ParameterisedHolderNode::setParameterised( className, classVersion, "IECORE_OP_PATHS" );
}

IECore::OpPtr OpHolder::getOp( std::string *className, int *classVersion )
{
	return IECore::runTimeCast<IECore::Op>( getParameterised( className, classVersion ) );
}

IECore::ConstOpPtr OpHolder::getOp( std::string *className, int *classVersion ) const
{
	return IECore::runTimeCast<IECore::Op>( getParameterised( className, classVersion ) );
}

void OpHolder::dirty( ConstPlugPtr dirty ) const
{
	ConstPlugPtr parametersPlug = getChild<Plug>( "parameters" );
	if( parametersPlug && parametersPlug->isAncestorOf( dirty ) )
	{
		/// \todo Should the dirty() method really be const? Should it perhaps fill an array
		/// of plugs instead? Then it could be used for dependency queries too, and remain const.
		ConstValuePlugPtr resultPlug = getChild<ValuePlug>( "result" );
		if( resultPlug )
		{
			constPointerCast<ValuePlug>( resultPlug )->setDirty();
		}
	}
}

void OpHolder::compute( PlugPtr output ) const
{
	if( output->getName()=="result" )
	{	
		constPointerCast<CompoundParameterHandler>( parameterHandler() )->setParameterValue();
		constPointerCast<Op>( getOp() )->operate();
		m_resultParameterHandler->setPlugValue();
	}
}
