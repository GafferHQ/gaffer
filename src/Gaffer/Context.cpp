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
#include "IECore/PathMatcherData.h"

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
// TypeFunctionTable implementation
//////////////////////////////////////////////////////////////////////////

DataPtr Context::TypeFunctionTable::makeData( IECore::TypeId typeId, const void *raw )
{
	TypeFunctionTable &tf = theFunctionTable();
	TypeMap::const_iterator it = tf.m_typeMap.find( typeId );
	if( it == tf.m_typeMap.end() )
	{
		throw IECore::Exception( "Context does not support typeId: " + std::to_string( typeId ) );
	}
	return it->second.makeDataFunction( raw );
}

void Context::TypeFunctionTable::internalSetData( IECore::TypeId typeId, Context &c, const InternedString &name, const ConstDataPtr &value, AllocMap &allocMap, bool copy, const IECore::MurmurHash *knownHash )
{
	TypeFunctionTable &tf = theFunctionTable();
	TypeMap::const_iterator it = tf.m_typeMap.find( typeId );
	if( it == tf.m_typeMap.end() )
	{
		throw IECore::Exception( "Context does not support typeId: " + std::to_string( typeId ) );
	}
	it->second.internalSetDataFunction( c, name, value, allocMap, copy, knownHash );
}

bool Context::TypeFunctionTable::typedEquals( IECore::TypeId typeId, const void *rawA, const void *rawB )
{
	TypeFunctionTable &tf = theFunctionTable();
	TypeMap::const_iterator it = tf.m_typeMap.find( typeId );
	if( it == tf.m_typeMap.end() )
	{
		throw IECore::Exception( "Context does not support typeId: " + std::to_string( typeId ) );
	}
	return it->second.typedEqualsFunction( rawA, rawB );
}

IECore::MurmurHash Context::TypeFunctionTable::entryHash( IECore::TypeId typeId, Storage &s, const IECore::InternedString &name )
{
	TypeFunctionTable &tf = theFunctionTable();
	TypeMap::const_iterator it = tf.m_typeMap.find( typeId );
	if( it == tf.m_typeMap.end() )
	{
		throw IECore::Exception( "Context does not support typeId: " + std::to_string( typeId ) );
	}
	return it->second.entryHashFunction( s, name );
}

Context::TypeFunctionTable &Context::TypeFunctionTable::theFunctionTable()
{
	static TypeFunctionTable *tf = new TypeFunctionTable();
	return *tf;
}

// Core types and things which are actually used
Context::ContextTypeDescription<FloatData> floatTypeDescription;
Context::ContextTypeDescription<IntData> intTypeDescription;
Context::ContextTypeDescription<BoolData> boolTypeDescription;
Context::ContextTypeDescription<StringData> stringTypeDescription;
Context::ContextTypeDescription<InternedStringData> internedStringTypeDescription;
Context::ContextTypeDescription<V2iData> v2iTypeDescription;
Context::ContextTypeDescription<V3iData> v3iTypeDescription;
Context::ContextTypeDescription<V2fData> v2fTypeDescription;
Context::ContextTypeDescription<V3fData> v3fTypeDescription;
Context::ContextTypeDescription<Color3fData> color3fTypeDescription;
Context::ContextTypeDescription<Color4fData> color4fTypeDescription;
Context::ContextTypeDescription<Box2iData> box2iTypeDescription;

Context::ContextTypeDescription<UInt64Data> uint64TypeDescription;
Context::ContextTypeDescription<InternedStringVectorData> internedStringVectorTypeDescription;
Context::ContextTypeDescription<PathMatcherData> pathMatcherTypeDescription;

// Types which seem like obvious generalizations, or are used in the Context tests
Context::ContextTypeDescription<Box2fData> box2fTypeDescription;
Context::ContextTypeDescription<Box3iData> box3iTypeDescription;
Context::ContextTypeDescription<Box3fData> box3fTypeDescription;
Context::ContextTypeDescription<FloatVectorData> floatVectorTypeDescription;
Context::ContextTypeDescription<IntVectorData> intVectorTypeDescription;
Context::ContextTypeDescription<StringVectorData> stringVectorTypeDescription;
Context::ContextTypeDescription<V2iVectorData> v2iVectorTypeDescription;
Context::ContextTypeDescription<V3iVectorData> v3iVectorTypeDescription;
Context::ContextTypeDescription<V2fVectorData> v2fVectorTypeDescription;
Context::ContextTypeDescription<V3fVectorData> v3fVectorTypeDescription;
Context::ContextTypeDescription<Color3fVectorData> color3fVectorTypeDescription;
Context::ContextTypeDescription<Color4fVectorData> color4fVectorTypeDescription;


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

Context::Context( const Context &other )
	:	Context( other, Copied )
{
}

Context::Context( const Context &other, Ownership ownership )
	:	m_changedSignal( nullptr ),
		m_hash( other.m_hash ),
		m_hashValid( other.m_hashValid ),
		m_canceller( other.m_canceller )
{
	if( ownership == Borrowed )
	{
		// Reserving one extra spot before we copy in the existing entries means that we will
		// avoid doing this allocation twice in the common case where we set exactly one context
		// variable.  Perhaps we should reserve two extra spots - though that is some extra memory
		// to carry around in cases where we don't add any variables?
		m_map.reserve( other.m_map.size() + 1 );
		m_map = other.m_map;
	}
	else
	{
		for( auto &i : other.m_map )
		{
			// Copying a context without using Borrowed should be completely safe, even if
			// the source context is destroyed, so we need to preserve the memory for the
			// source context entries.  If they are in other.m_allocMap, we can just take
			// smart pointer, since the alloc map entries are private and never change.
			// Otherwise, we need to call getAsData to allocate a fresh Data that we will
			// store
			AllocMap::const_iterator allocIt = other.m_allocMap.find( i.first );
			if( allocIt != other.m_allocMap.end() )
			{
				// Try setting with the Data stored in the other Context
				TypeFunctionTable::internalSetData( allocIt->second->typeId(), *this, i.first, allocIt->second, m_allocMap, false, &i.second.hash );

				// Check if the other Context was actually the using a pointer
				// to the value we just added
				if( (m_map.end() - 1 )->second.value == i.second.value )
				{
					// Yep, it matches, we're good
					continue;
				}

				// The Data stored in other.m_allocMap wasn't actually used by other.m_map
				// ( it was probably overwritten with a fast EditScope::set that doesn't touch
				// m_allocMap ).  We need to allocate a new Data after all.
			}

			// getAsData allocates a fresh Data, so we don't need to copy
			TypeFunctionTable::internalSetData( i.second.typeId, *this, i.first, other.getAsData( i.first ), m_allocMap, false, &i.second.hash );
		}
	}
}

Context::Context( const Context &other, const IECore::Canceller &canceller )
	:	Context( other )
{
	if( m_canceller )
	{
		throw IECore::Exception( "Can't replace an existing Canceller" );
	}
	m_canceller = &canceller;
}

Context::Context( const Context &other, bool omitCanceller )
	:	Context( other )
{
	if( omitCanceller )
	{
		m_canceller = nullptr;
	}
}

Context::~Context()
{
	delete m_changedSignal;
}

void Context::set( const IECore::InternedString &name, const IECore::Data *value )
{
	// The context interface should be safe, so we copy the value so that the client can't
	// invalidate this context by changing it.  ( If you don't want to pay for this copy,
	// use EditableScope )
	ConstDataPtr valueSmart( value );
	TypeFunctionTable::internalSetData( value->typeId(), *this, name, valueSmart, m_allocMap, true );
}

IECore::DataPtr Context::getAsData( const IECore::InternedString &name ) const
{
	Map::const_iterator it = m_map.find( name );
	if( it == m_map.end() )
	{
		throw IECore::Exception( boost::str( boost::format( "Context has no entry named \"%s\"" ) % name.value() ) );
	}

	#ifndef NDEBUG
	validateVariableHash( it->second, name);
	#endif // NDEBUG

	return TypeFunctionTable::makeData( it->second.typeId, it->second.value );
}

IECore::DataPtr Context::getAsData( const IECore::InternedString &name, IECore::Data *defaultValue ) const
{
	Map::const_iterator it = m_map.find( name );
	if( it == m_map.end() )
	{
		return defaultValue;
	}

	#ifndef NDEBUG
	validateVariableHash( it->second, name);
	#endif // NDEBUG

	return TypeFunctionTable::makeData( it->second.typeId, it->second.value );
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
	std::pair<Map::iterator, bool> insert = m_map.try_emplace( g_frame );
	const Storage &storage = insert.first->second;
	if( !insert.second && storage.typeId == FloatData::staticTypeId() && *((float*)storage.value) == frame )
	{
		// Already set to the value we want, we can skip
		return;
	}

	m_frame = frame;
	internalSet( insert.first, &m_frame );
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
		if(
			it->first != otherIt->first ||
			it->second.typeId != otherIt->second.typeId ||
			!TypeFunctionTable::typedEquals( it->second.typeId, it->second.value, otherIt->second.value )
		)
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

void Context::EditableScope::setAllocated( const IECore::InternedString &name, const IECore::Data *value )
{
	m_context->set( name, value );
}

void Context::EditableScope::setFrame( float frame )
{
	m_context->setFrame( frame );
}

//DEPRECATED
void Context::EditableScope::setFramesPerSecond( float framesPerSecond )
{
	m_context->setFramesPerSecond( framesPerSecond );
}

void Context::EditableScope::setTime( float timeInSeconds )
{
	m_context->setTime( timeInSeconds );
}

void Context::EditableScope::setFramesPerSecond( const float *framesPerSecond )
{
	set( g_framesPerSecond, framesPerSecond );
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
	IECore::TypeId typeId;
	const void* d = m_context->getPointerAndTypeId( internedName, typeId );
	if( d )
	{
		switch( typeId )
		{
			case IECore::StringDataTypeId :
				recurse = true;
				return *static_cast<const std::string*>( d );
			case IECore::FloatDataTypeId :
				m_formattedString = boost::lexical_cast<std::string>(
					*static_cast<const float *>( d )
				);
				return m_formattedString;
			case IECore::IntDataTypeId :
				m_formattedString = boost::lexical_cast<std::string>(
					*static_cast<const int *>( d )
				);
				return m_formattedString;
			case IECore::InternedStringVectorDataTypeId : {
				// This is unashamedly tailored to the needs of GafferScene's `${scene:path}`
				// variable. We could make this cleaner by adding a mechanism for registering custom
				// formatters, but that would be overkill for this one use case.
				const auto &v = *static_cast<const std::vector<InternedString>* >( d );
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

void Context::validateVariableHash( const Storage &s, const IECore::InternedString &name ) const
{
	if( s.hash != TypeFunctionTable::entryHash( s.typeId, const_cast<Storage&>( s ), name ) )
	{
		throw IECore::Exception( "Corrupt hash for context entry: " + name.string() );
	}
}
