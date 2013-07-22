//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2012, John Haddon. All rights reserved.
//  Copyright (c) 2013, Image Engine Design Inc. All rights reserved.
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
	:	m_data( new CompoundData() ), m_changedSignal( 0 )
{
	set( g_frame, 1.0f );
}

Context::Context( const Context &other )
	:	m_data( other.m_data->copy() ), m_changedSignal( 0 )
{
}

Context::~Context()
{
	delete m_changedSignal;
}

void Context::names( std::vector<IECore::InternedString> &names ) const
{
	const CompoundDataMap &m = m_data->readable();
	for( CompoundDataMap::const_iterator it = m.begin(), eIt = m.end(); it != eIt; it++ )
	{
		names.push_back( it->first );
	}
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
	if( !m_changedSignal )
	{
		// we create this on demand, as otherwise it adds a significant
		// hit to the cost of constructing a Context. as we need
		// to frequently construct temporary Contexts during computation,
		// but only need to connect to the changed signal for the few
		// persistent contexts used by the gui, this is a very worthwhile
		// optimisation.
		m_changedSignal = new ChangedSignal();
	}
	return *m_changedSignal;
}

IECore::MurmurHash Context::hash() const
{
	return ((Object *)( m_data.get() ))->hash();
}

bool Context::operator == ( const Context &other ) const
{
	return m_data->isEqualTo( other.m_data.get() );
}

bool Context::operator != ( const Context &other ) const
{
	return m_data->isNotEqualTo( other.m_data.get() );
}

std::string Context::substitute( const std::string &s ) const
{
	std::string result;
	result.reserve( s.size() ); // might need more or less, but this is a decent ballpark
	substituteInternal( s, result, 0 );
	return result;
}

void Context::substituteInternal( const std::string &s, std::string &result, const int recursionDepth ) const
{
	if( recursionDepth > 8 )
	{
		throw IECore::Exception( "Context::substitute() : maximum recursion depth reached." );
	}

	for( size_t i=0, size=s.size(); i<size; )
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
			
			const IECore::Data *d = get<IECore::Data>( variableName, 0 );
			if( d )
			{
				switch( d->typeId() )
				{
					case IECore::StringDataTypeId :
						substituteInternal( static_cast<const IECore::StringData *>( d )->readable(), result, recursionDepth + 1 );
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
			else if( const char *v = getenv( variableName.c_str() ) )
			{
				// variable not in context - try environment
				result += v;
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
			int frame = (int)round( getFrame() );
			std::ostringstream padder;
			padder << std::setw( padding ) << std::setfill( '0' ) << frame;
			result += padder.str();
		}
		else if( s[i] == '~' && result.size()==0 )
		{
			if( const char *v = getenv( "HOME" ) )
			{
				result += v;
			}
			i++;
		}
		else
		{
			result.push_back( s[i] );
			i++;
		}
	}
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
