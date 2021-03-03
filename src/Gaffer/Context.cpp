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

#include "Gaffer/Context.h"

#include "IECore/SimpleTypedData.h"
#include "IECore/VectorTypedData.h"

#include "boost/lexical_cast.hpp"

// Headers needed to access environment - these differ
// between OS X and Linux.
#ifdef __APPLE__
#include <crt_externs.h>
static char **environ = *_NSGetEnviron();
#else
#include <unistd.h>
#endif

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

		const std::string *get( IECore::InternedString name ) const
		{
			Map::const_iterator it = m_map.find( name );
			if( it != m_map.end() )
			{
				return &it->second.string();
			}
			return nullptr;
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
static InternedString g_framesPerSecond( "framesPerSecond" );

Context::Context()
	:	m_changedSignal( nullptr ), m_hashValid( false ), m_canceller( nullptr )
{
	set( g_frame, 1.0f );
	set( g_framesPerSecond, 24.0f );
}

Context::Context( const Context &other, Ownership ownership )
	:	m_map( other.m_map ),
		m_changedSignal( nullptr ),
		m_hash( other.m_hash ),
		m_hashValid( other.m_hashValid ),
		m_canceller( other.m_canceller )
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

Context::Context( const Context &other, const IECore::Canceller &canceller )
	:	Context( other, Copied )
{
	if( m_canceller )
	{
		throw IECore::Exception( "Can't replace an existing Canceller" );
	}
	m_canceller = &canceller;
}

Context::Context( const Context &other, bool omitCanceller )
	:	Context( other, Copied )
{
	if( omitCanceller )
	{
		m_canceller = nullptr;
	}
}

Context::~Context()
{
	#ifndef NDEBUG
	validateHashes();
	#endif // NDEBUG

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
		if( m_changedSignal )
		{
			(*m_changedSignal)( this, name );
		}
	}
}

void Context::removeMatching( const StringAlgo::MatchPattern &pattern )
{
	if( pattern == "" )
	{
		return;
	}

	for( Map::iterator it = m_map.begin(); it != m_map.end(); )
	{
		if( StringAlgo::matchMultiple( it->first, pattern ) )
		{
			it = m_map.erase( it );
			m_hashValid = false;
			if( m_changedSignal )
			{
				(*m_changedSignal)( this, it->first );
			}
		}
		else
		{
			it++;
		}
	}
}

void Context::changed( const IECore::InternedString &name )
{
	Map::iterator it = m_map.find( name );
	if( it != m_map.end() )
	{
		m_hashValid = false;
		it->second.updateHash( name );
	}

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

float Context::getFramesPerSecond() const
{
	return get<float>( g_framesPerSecond );
}

void Context::setFramesPerSecond( float framesPerSecond )
{
	set<float>( g_framesPerSecond, framesPerSecond );
}

float Context::getTime() const
{
	return getFrame() / getFramesPerSecond();
}

void Context::setTime( float timeInSeconds )
{
	setFrame( timeInSeconds * getFramesPerSecond() );
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

	uint64_t sumH1 = 0, sumH2 = 0;
	for( Map::const_iterator it = m_map.begin(), eIt = m_map.end(); it != eIt; ++it )
	{
		sumH1 += it->second.hash.h1();
		sumH2 += it->second.hash.h2();
	}

	m_hash = MurmurHash( sumH1, sumH2 );
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
	return IECore::StringAlgo::substitute( s, SubstitutionProvider( this ), substitutions );
}

//////////////////////////////////////////////////////////////////////////
// Scope and current context implementation
//////////////////////////////////////////////////////////////////////////

Context::Scope::Scope( const Context *context )
	:	ThreadState::Scope( /* push = */ static_cast<bool>( context ) )
{
	if( m_threadState )
	{
		// The `push` argument to our base class should mean that we only
		// end up in here if we have a context to scope. If not, we are
		// a no-op.
		assert( context );
		m_threadState->m_context = context;
	}
}

Context::Scope::~Scope()
{
}

Context::EditableScope::EditableScope( const Context *context )
	:	m_context( new Context( *context, Borrowed ) )
{
	m_threadState->m_context = m_context.get();
}

Context::EditableScope::EditableScope( const ThreadState &threadState )
	:	ThreadState::Scope( threadState ), m_context( new Context( *threadState.m_context, Borrowed ) )
{
	m_threadState->m_context = m_context.get();
}

Context::EditableScope::~EditableScope()
{
}

void Context::EditableScope::setFrame( float frame )
{
	m_context->setFrame( frame );
}

void Context::EditableScope::setFramesPerSecond( float framesPerSecond )
{
	m_context->setFramesPerSecond( framesPerSecond );
}

void Context::EditableScope::setTime( float timeInSeconds )
{
	m_context->setTime( timeInSeconds );
}

void Context::EditableScope::remove( const IECore::InternedString &name )
{
	m_context->remove( name );
}

void Context::EditableScope::removeMatching( const StringAlgo::MatchPattern &pattern )
{
	m_context->removeMatching( pattern );
}

const Context *Context::current()
{
	return ThreadState::current().m_context;
}

//////////////////////////////////////////////////////////////////////////
// SubstitutionProvider implementation
//////////////////////////////////////////////////////////////////////////

Context::SubstitutionProvider::SubstitutionProvider( const Context *context )
	:	m_context( context )
{
}

int Context::SubstitutionProvider::frame() const
{
	return (int)round( m_context->getFrame() );
}

const std::string &Context::SubstitutionProvider::variable( const boost::string_view &name, bool &recurse ) const
{
	InternedString internedName( name );
	const IECore::Data *d = m_context->get<IECore::Data>( internedName, nullptr );
	if( d )
	{
		switch( d->typeId() )
		{
			case IECore::StringDataTypeId :
				recurse = true;
				return static_cast<const IECore::StringData *>( d )->readable();
			case IECore::FloatDataTypeId :
				m_formattedString = boost::lexical_cast<std::string>(
					static_cast<const IECore::FloatData *>( d )->readable()
				);
				return m_formattedString;
			case IECore::IntDataTypeId :
				m_formattedString = boost::lexical_cast<std::string>(
					static_cast<const IECore::IntData *>( d )->readable()
				);
				return m_formattedString;
			case IECore::InternedStringVectorDataTypeId : {
				// This is unashamedly tailored to the needs of GafferScene's `${scene:path}`
				// variable. We could make this cleaner by adding a mechanism for registering custom
				// formatters, but that would be overkill for this one use case.
				const auto &v = static_cast<const IECore::InternedStringVectorData *>( d )->readable();
				m_formattedString.clear();
				if( v.empty() )
				{
					m_formattedString += "/";
				}
				else
				{
					for( const auto &x : v )
					{
						m_formattedString += "/" + x.string();
					}
				}
				return m_formattedString;
			}
			default :
				break;
		}
	}
	else if( const std::string *v = g_environment.get( internedName ) )
	{
		// variable not in context - try environment
		return *v;
	}

	m_formattedString.clear();
	return m_formattedString;
}

void Context::validateHashes()
{
	for( Map::iterator it = m_map.begin(), eIt = m_map.end(); it != eIt; ++it )
	{
		IECore::MurmurHash prevHash = it->second.hash;
		it->second.updateHash( it->first );

		if( prevHash != it->second.hash )
		{
			throw IECore::Exception( "Corrupt hash for context entry: " + it->first.string() );
		}
	}

	if( m_hashValid )
	{
		IECore::MurmurHash prevTotal = m_hash;
		if( prevTotal != hash() )
		{
			throw IECore::Exception( "Corrupt total hash for context" );
		}
	}
}
