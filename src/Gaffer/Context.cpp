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

#include <stack>

#include "tbb/enumerable_thread_specific.h"

#include "boost/lexical_cast.hpp"

#include "IECore/SimpleTypedData.h"

#include "Gaffer/Context.h"

using namespace Gaffer;
using namespace IECore;

//////////////////////////////////////////////////////////////////////////
// Context implementation
//////////////////////////////////////////////////////////////////////////

static InternedString g_frame( "frame" );

Context::Context()
	:	m_data( new CompoundData() )
{
	set( g_frame, 1.0f );
}

Context::Context( const Context &other )
	:	m_data( other.m_data->copy() )
{
}
	
float Context::getFrame() const
{
	return get<float>( g_frame );
}

void Context::setFrame( float frame )
{
	set( g_frame, frame );
}

Context::ChangedSignal &Context::changedSignal()
{
	return m_changedSignal;
}

IECore::MurmurHash Context::hash() const
{
	return ((Object *)( m_data.get() ))->hash();
}

bool Context::operator == ( const Context &other )
{
	return m_data->isEqualTo( other.m_data.get() );
}

bool Context::operator != ( const Context &other )
{
	return m_data->isNotEqualTo( other.m_data.get() );
}

std::string Context::substitute( const std::string &s ) const
{
	std::string result;
	size_t size = s.size();
	result.reserve( size ); // might need more or less, but this is a decent ballpark
	for( size_t i=0; i<size; )
	{
		if( s[i] == '$' )
		{
			std::string variableName;
			i++; // skip $
			bool bracketed = ( i < size ) && s[i]=='{';
			if( bracketed )
			{
				i++; // skip initial bracket
				while( i < size && s[i] != '}' )
				{
					variableName.push_back( s[i] );
					i++;
				}
				i++; // skip final bracket
			}
			else
			{
				while( i < size && isalnum( s[i] ) )
				{
					variableName.push_back( s[i] );
					i++;
				}
			}
			
			const IECore::Data *d = 0;
			try
			{
				d = get<IECore::Data>( variableName );
			}
			catch( ... )
			{
			}
			
			if( d )
			{
				switch( d->typeId() )
				{
					case IECore::StringDataTypeId :
						result += static_cast<const IECore::StringData *>( d )->readable();
						break;
					case IECore::FloatDataTypeId :
						result += boost::lexical_cast<std::string>(
							static_cast<const IECore::FloatData *>( d )->readable()
						);
						break;
					case IECore::IntDataTypeId :
						result += boost::lexical_cast<std::string>(
							static_cast<const IECore::IntData *>( d )->readable()
						);
						break;	
					default :
						break;
				}
			}
		}
		else if( s[i] == '#' )
		{
			int padding = 0;
			while( i < size && s[i]=='#' )
			{
				padding++;
				i++;
			}
			int frame = round( getFrame() );
			std::ostringstream padder;
			padder << std::setw( padding ) << std::setfill( '0' ) << frame;
			result += padder.str();
		}
		else
		{
			result.push_back( s[i] );
			i++;
		}
	}

	return result;
}

//////////////////////////////////////////////////////////////////////////
// Scope and current context implementation
//////////////////////////////////////////////////////////////////////////

typedef std::stack<const Context *> ContextStack;
typedef tbb::enumerable_thread_specific<ContextStack> ThreadSpecificContextStack;

static ThreadSpecificContextStack g_threadContexts;
static ContextPtr g_defaultContext = new Context;

Context::Scope::Scope( const Context *context )
{
	ContextStack &stack = g_threadContexts.local();
	stack.push( context );
}

Context::Scope::~Scope()
{
	ContextStack &stack = g_threadContexts.local();
	stack.pop();
}

const Context *Context::current()
{
	ContextStack &stack = g_threadContexts.local();
	if( !stack.size() )
	{
		return g_defaultContext;
	}
	return stack.top();
}