//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2012, John Haddon. All rights reserved.
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

#ifndef GAFFER_CONTEXTVARIABLES_INL
#define GAFFER_CONTEXTVARIABLES_INL

#include "Gaffer/Context.h"
#include "Gaffer/ContextVariables.h"

#include "IECore/SimpleTypedData.h"
#include "Gaffer/ContextProcessor.inl"

namespace Gaffer
{

template<typename BaseType>
const IECore::RunTimeTyped::TypeDescription<ContextVariables<BaseType> > ContextVariables<BaseType>::g_typeDescription;

template<typename BaseType>
size_t ContextVariables<BaseType>::g_firstPlugIndex;

template<typename BaseType>
ContextVariables<BaseType>::ContextVariables( const std::string &name )
	:	ContextProcessor<BaseType>( name )
{
	BaseType::storeIndexOfNextChild( g_firstPlugIndex );
	ContextProcessor<BaseType>::addChild(
		new CompoundDataPlug( "variables" )
	);
	ContextProcessor<BaseType>::addChild(
		new AtomicCompoundDataPlug( "extraVariables", Plug::In, new IECore::CompoundData )
	);
}

template<typename BaseType>
ContextVariables<BaseType>::~ContextVariables()
{
}

template<typename BaseType>
CompoundDataPlug *ContextVariables<BaseType>::variablesPlug()
{
	return ContextProcessor<BaseType>::template getChild<CompoundDataPlug>( g_firstPlugIndex );
}

template<typename BaseType>
const CompoundDataPlug *ContextVariables<BaseType>::variablesPlug() const
{
	return ContextProcessor<BaseType>::template getChild<CompoundDataPlug>( g_firstPlugIndex );
}

template<typename BaseType>
AtomicCompoundDataPlug *ContextVariables<BaseType>::extraVariablesPlug()
{
	return ContextProcessor<BaseType>::template getChild<AtomicCompoundDataPlug>( g_firstPlugIndex + 1 );
}

template<typename BaseType>
const AtomicCompoundDataPlug *ContextVariables<BaseType>::extraVariablesPlug() const
{
	return ContextProcessor<BaseType>::template getChild<AtomicCompoundDataPlug>( g_firstPlugIndex + 1 );
}

template<typename BaseType>
bool ContextVariables<BaseType>::affectsContext( const Plug *input ) const
{
	return variablesPlug()->isAncestorOf( input ) || input == extraVariablesPlug();
}

template<typename BaseType>
void ContextVariables<BaseType>::processContext( Context::EditableScope &context ) const
{
	std::string name;
	for( CompoundDataPlug::MemberPlugIterator it( variablesPlug() ); !it.done(); ++it )
	{
		IECore::DataPtr data = variablesPlug()->memberDataAndName( it->get(), name );
		if( data )
		{
			context.set( name, data.get() );
		}
	}
	IECore::ConstCompoundDataPtr extraVariablesData = extraVariablesPlug()->getValue();
	const IECore::CompoundDataMap &extraVariables = extraVariablesData->readable();
	for( IECore::CompoundDataMap::const_iterator it = extraVariables.begin(), eIt = extraVariables.end(); it != eIt; ++it )
	{
		context.set( it->first, it->second.get() );
	}
}

} // namespace Gaffer

#endif // GAFFER_CONTEXTVARIABLES_INL
