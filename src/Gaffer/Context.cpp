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

// Headers needed to access environment - these differ
// between OS X and Linux.
#ifdef __APPLE__
#include <crt_externs.h>
static char **environ = *_NSGetEnviron();
#else
#include <unistd.h>
#endif

#include <stack>

#include "tbb/enumerable_thread_specific.h"

#include "boost/lexical_cast.hpp"

#include "IECore/SimpleTypedData.h"

#include "Gaffer/Context.h"

using namespace Gaffer;
using namespace IECore;

//////////////////////////////////////////////////////////////////////////
// Environment variable access for use in Context::substitute().
// We can't just take the current value for an environment variable
// each time we need it, because that defeats the caching of hashes
// in ValuePlug, which assumes that a hash depends only on graph state
// and the context. So instead, we take a copy of the environment at
// startup and use that for our lookups. This is also provides quicker
// lookups than getenv().
//////////////////////////////////////////////////////////////////////////

namespace
{

class Environment
{

	public :

		Environment()
		{
			for( char **e = environ; *e; e++ )
			{
				const char *separator = strchr( *e, '=' );
				if( !separator )
				{
					continue;
				}
				InternedString name( *e, separator - *e );
				InternedString value( separator + 1 );
				m_map[name] = value;
			}
		}

		const char *get( IECore::InternedString name ) const
		{
			Map::const_iterator it = m_map.find( name );
			if( it != m_map.end() )
			{
				return it->second.c_str();
			}
			return NULL;
		}

	private :

		typedef boost::container::flat_map<IECore::InternedString, IECore::InternedString> Map;
		Map m_map;

};

Environment g_environment;

} // namespace

//////////////////////////////////////////////////////////////////////////
// Context implementation
//////////////////////////////////////////////////////////////////////////

static InternedString g_frame( "frame" );

Context::Context()
	:	m_changedSignal( NULL ), m_hashValid( false )
{
	set( g_frame, 1.0f );
}

Context::Context( const Context &other, Ownership ownership )
	:	m_map( other.m_map ), m_changedSignal( NULL ), m_hash( other.m_hash ), m_hashValid( other.m_hashValid )
{
	// We used the (shallow) Map copy constructor in our initialiser above
	// because it offers a big performance win over iterating and inserting copies
	// ourselves. Now we need to go in and tweak our copies based on the ownership.

	for( Map::iterator it = m_map.begin(), eIt = m_map.end(); it != eIt; ++it )
	{
		it->second.ownership = ownership;
		switch( ownership )
		{
			case Copied :
				{
					DataPtr valueCopy = it->second.data->copy();
					it->second.data = valueCopy.get();
					it->second.data->addRef();
					break;
				}
			case Shared :
				it->second.data->addRef();
				break;
			case Borrowed :
				// no need to do anything
				break;
		}
	}
}

Context::~Context()
{
	for( Map::const_iterator it = m_map.begin(), eIt = m_map.end(); it != eIt; ++it )
	{
		if( it->second.ownership != Borrowed )
		{
			it->second.data->removeRef();
		}
	}

	delete m_changedSignal;
}

void Context::remove( const IECore::InternedString &name )
{
	Map::iterator it = m_map.find( name );
	if( it != m_map.end() )
	{
		m_map.erase( it );
		m_hashValid = false;
	}
}

void Context::changed( const IECore::InternedString &name )
{
	m_hashValid = false;
	if( m_changedSignal )
	{
		(*m_changedSignal)( this, name );
	}
}

void Context::names( std::vector<IECore::InternedString> &names ) const
{
	for( Map::const_iterator it = m_map.begin(), eIt = m_map.end(); it != eIt; it++ )
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
	if( m_hashValid )
	{
		return m_hash;
	}

	m_hash = IECore::MurmurHash();
	for( Map::const_iterator it = m_map.begin(), eIt = m_map.end(); it != eIt; it++ )
	{
		/// \todo Perhaps at some point the UI should use a different container for
		/// these "not computationally important" values, so we wouldn't have to skip
		/// them here.
		if( it->first.string().compare( 0, 3, "ui:" ) )
		{
			m_hash.append( it->first );
			it->second.data->hash( m_hash );
		}
	}
	m_hashValid = true;
	return m_hash;
}

bool Context::operator == ( const Context &other ) const
{
	if( m_map.size() != other.m_map.size() )
	{
		return false;
	}
	Map::const_iterator otherIt = other.m_map.begin();
	for( Map::const_iterator it = m_map.begin(), eIt = m_map.end(); it != eIt; ++it, ++otherIt )
	{
		if( it->first != otherIt->first || !( it->second.data->isEqualTo( otherIt->second.data ) ) )
		{
			return false;
		}
	}

	return true;
}

bool Context::operator != ( const Context &other ) const
{
	return !( *this == other );
}

std::string Context::substitute( const std::string &s, unsigned substitutions ) const
{
	std::string result;
	result.reserve( s.size() ); // might need more or less, but this is a decent ballpark
	substituteInternal( s.c_str(), result, 0, substitutions );
	return result;
}

unsigned Context::substitutions( const std::string &input )
{
	unsigned result = NoSubstitutions;
	for( const char *c = input.c_str(); *c; )
	{
		switch( *c )
		{
			case '$' :
				result |= VariableSubstitutions;
				c++;
				break;
			case '#' :
				result |= FrameSubstitutions;
				c++;
				break;
			case '~' :
				result |= TildeSubstitutions;
				c++;
				break;
			case '\\' :
				result |= EscapeSubstitutions;
				c++;
				if( *c )
				{
					c++;
				}
				break;
			default :
				c++;
		}
		if( result == AllSubstitutions )
		{
			return result;
		}
	}
	return result;
}

bool Context::hasSubstitutions( const std::string &input )
{
	for( const char *c = input.c_str(); *c; c++ )
	{
		switch( *c )
		{
			case '$' :
			case '#' :
			case '~' :
			case '\\' :
				return true;
			default :
				; // do nothing
		}
	}
	return false;
}

void Context::substituteInternal( const char *s, std::string &result, const int recursionDepth, unsigned substitutions ) const
{
	if( recursionDepth > 8 )
	{
		throw IECore::Exception( "Context::substitute() : maximum recursion depth reached." );
	}

	while( *s )
	{
		switch( *s )
		{
			case '\\' :
			{
				if( substitutions & EscapeSubstitutions )
				{
					s++;
					if( *s )
					{
						result.push_back( *s++ );
					}
				}
				else
				{
					// variable substitutions disabled
					result.push_back( *s++ );
				}
				break;
			}
			case '$' :
			{
				if( substitutions & VariableSubstitutions )
				{
					s++; // skip $
					bool bracketed = *s =='{';
					const char *variableNameStart = NULL;
					const char *variableNameEnd = NULL;
					if( bracketed )
					{
						s++; // skip initial bracket
						variableNameStart = s;
						while( *s && *s != '}' )
						{
							s++;
						}
						variableNameEnd = s;
						if( *s )
						{
							s++; // skip final bracket
						}
					}
					else
					{
						variableNameStart = s;
						while( isalnum( *s ) )
						{
							s++;
						}
						variableNameEnd = s;
					}

					InternedString variableName( variableNameStart, variableNameEnd - variableNameStart );
					const IECore::Data *d = get<IECore::Data>( variableName, NULL );
					if( d )
					{
						switch( d->typeId() )
						{
							case IECore::StringDataTypeId :
								substituteInternal( static_cast<const IECore::StringData *>( d )->readable().c_str(), result, recursionDepth + 1, substitutions );
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
					else if( const char *v = g_environment.get( variableName ) )
					{
						// variable not in context - try environment
						result += v;
					}
				}
				else
				{
					// variable substitutions disabled
					result.push_back( *s++ );
				}
				break;
			}
			case '#' :
			{
				if( substitutions & FrameSubstitutions )
				{
					int padding = 0;
					while( *s == '#' )
					{
						padding++;
						s++;
					}
					int frame = (int)round( getFrame() );
					std::ostringstream padder;
					padder << std::setw( padding ) << std::setfill( '0' ) << frame;
					result += padder.str();
				}
				else
				{
					// frame substitutions disabled
					result.push_back( *s++ );
				}
				break;
			}
			case '~' :
			{
				if( substitutions & TildeSubstitutions && result.size() == 0 )
				{
					if( const char *v = getenv( "HOME" ) )
					{
						result += v;
					}
					++s;
					break;
				}
				else
				{
					// tilde substitutions disabled
					result.push_back( *s++ );
				}
				break;
			}
			default :
				result.push_back( *s++ );
				break;
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
		return g_defaultContext.get();
	}
	return stack.top();
}
