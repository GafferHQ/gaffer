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

#include "Gaffer/TimeWarp.h"
#include "Gaffer/Context.h"
#include "Gaffer/ContextProcessor.inl"

namespace Gaffer
{

template<typename BaseType>
const IECore::RunTimeTyped::TypeDescription<TimeWarp<BaseType> > TimeWarp<BaseType>::g_typeDescription;

template<typename BaseType>
TimeWarp<BaseType>::TimeWarp( const std::string &name )
	:	ContextProcessor<BaseType>( name )
{
	ContextProcessor<BaseType>::addChild( new FloatPlug( "speed", Plug::In, 1.0f ) );
	ContextProcessor<BaseType>::addChild( new FloatPlug( "offset" ) );
}

template<typename BaseType>
TimeWarp<BaseType>::~TimeWarp()
{
}

template<typename BaseType>
FloatPlug *TimeWarp<BaseType>::speedPlug()
{
	return ContextProcessor<BaseType>::template getChild<FloatPlug>( "speed" );
}

template<typename BaseType>
const FloatPlug *TimeWarp<BaseType>::speedPlug() const
{
	return ContextProcessor<BaseType>::template getChild<FloatPlug>( "speed" );
}

template<typename BaseType>
FloatPlug *TimeWarp<BaseType>::offsetPlug()
{
	return ContextProcessor<BaseType>::template getChild<FloatPlug>( "offset" );
}

template<typename BaseType>
const FloatPlug *TimeWarp<BaseType>::offsetPlug() const
{
	return ContextProcessor<BaseType>::template getChild<FloatPlug>( "offset" );
}

template<typename BaseType>
void TimeWarp<BaseType>::affects( const Plug *input, DependencyNode::AffectedPlugsContainer &outputs ) const
{
	ContextProcessor<BaseType>::affects( input, outputs );
	
	if( input == speedPlug() || input == offsetPlug() )
	{
		ContextProcessor<BaseType>::appendAffectedPlugs( outputs );
	}
}

template<typename BaseType>
void TimeWarp<BaseType>::processContext( Context *context ) const
{
	context->setFrame( context->getFrame() * speedPlug()->getValue() + offsetPlug()->getValue() );
}

} // namespace Gaffer
