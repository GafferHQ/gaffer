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

		using Map = boost::container::flat_map<IECore::InternedString, IECore::InternedString>;
		Map m_map;

};

Environment g_environment;

} // namespace

//////////////////////////////////////////////////////////////////////////
// Context::Value implementation
//////////////////////////////////////////////////////////////////////////

Context::Value::Value( const IECore::InternedString &name, const IECore::Data *value )
	:	Value( typeFunctions( value->typeId() ).constructor( name, value ) )
{
}

Context::Value::Value( IECore::TypeId typeId, const void *value, const IECore::MurmurHash &hash )
	:	m_typeId( typeId ), m_value( value ), m_hash( hash )
{
}

bool Context::Value::operator == ( const Value &rhs ) const
{
	if( m_typeId != rhs.m_typeId )
	{
		return false;
	}
	if( m_value == rhs.m_value )
	{
		return true;
	}
	return typeFunctions( m_typeId ).isEqual( *this, rhs );
}

bool Context::Value::operator != ( const Value &rhs ) const
{
	return !(*this == rhs);
}

bool Context::Value::references( const IECore::Data *data ) const
{
	if( m_typeId != data->typeId() )
	{
		return false;
	}
	return typeFunctions( m_typeId ).valueFromData( data ) == m_value;
}

IECore::DataPtr Context::Value::makeData() const
{
	return typeFunctions( m_typeId ).makeData( *this, nullptr );
}

Context::Value Context::Value::copy( IECore::ConstDataPtr &owner ) const
{
	const void *v;
	owner = typeFunctions( m_typeId ).makeData( *this, &v );
	return Value( m_typeId, v, m_hash );
}

void Context::Value::validate( const IECore::InternedString &name ) const
{
	typeFunctions( m_typeId ).validate( name, *this );
}

Context::Value::TypeMap &Context::Value::typeMap()
{
	static TypeMap m_map;
	return m_map;
}

const Context::Value::TypeFunctions &Context::Value::typeFunctions( IECore::TypeId typeId )
{
	const TypeMap &m = typeMap();
	auto it = m.find( typeId );
	if( it == m.end() )
	{
		throw IECore::Exception(
			"Context does not support type " + std::string( RunTimeTyped::typeNameFromTypeId( typeId ) )
		);
	}
	return it->second;
}

//////////////////////////////////////////////////////////////////////////
// Type registrations
//////////////////////////////////////////////////////////////////////////

namespace
{

Context::TypeDescription<FloatData> g_floatTypeDescription;
Context::TypeDescription<IntData> g_intTypeDescription;
Context::TypeDescription<BoolData> g_boolTypeDescription;
Context::TypeDescription<StringData> g_stringTypeDescription;
Context::TypeDescription<InternedStringData> g_internedStringTypeDescription;
Context::TypeDescription<V2iData> g_v2iTypeDescription;
Context::TypeDescription<V3iData> g_v3iTypeDescription;
Context::TypeDescription<V2fData> g_v2fTypeDescription;
Context::TypeDescription<V3fData> g_v3fTypeDescription;
Context::TypeDescription<Color3fData> g_color3fTypeDescription;
Context::TypeDescription<Color4fData> g_color4fTypeDescription;
Context::TypeDescription<Box2iData> g_box2iTypeDescription;
Context::TypeDescription<UInt64Data> g_uint64TypeDescription;
Context::TypeDescription<InternedStringVectorData> g_internedStringVectorTypeDescription;
Context::TypeDescription<PathMatcherData> g_pathMatcherTypeDescription;
Context::TypeDescription<Box2fData> g_box2fTypeDescription;
Context::TypeDescription<Box3iData> g_box3iTypeDescription;
Context::TypeDescription<Box3fData> g_box3fTypeDescription;
Context::TypeDescription<FloatVectorData> g_floatVectorTypeDescription;
Context::TypeDescription<IntVectorData> g_intVectorTypeDescription;
Context::TypeDescription<StringVectorData> g_stringVectorTypeDescription;
Context::TypeDescription<V2iVectorData> g_v2iVectorTypeDescription;
Context::TypeDescription<V3iVectorData> g_v3iVectorTypeDescription;
Context::TypeDescription<V2fVectorData> g_v2fVectorTypeDescription;
Context::TypeDescription<V3fVectorData> g_v3fVectorTypeDescription;
Context::TypeDescription<Color3fVectorData> g_color3fVectorTypeDescription;
Context::TypeDescription<Color4fVectorData> g_color4fVectorTypeDescription;

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

Context::Context( const Context &other )
	:	Context( other, CopyMode::Owning )
{
}

Context::Context( const Context &other, CopyMode mode )
	:	m_changedSignal( nullptr ),
		m_hash( other.m_hash ),
		m_hashValid( other.m_hashValid ),
		m_canceller( other.m_canceller )
{
	// Reserving one extra spot before we copy in the existing variables means that we will
	// avoid a second allocation in the common case where we set exactly one context
	// variable. Perhaps we should reserve two extra spots - though that is some extra memory
	// to carry around in cases where we don't add any variables?
	m_map.reserve( other.m_map.size() + 1 );

	if( mode == CopyMode::NonOwning )
	{
		m_map = other.m_map;
	}
	else
	{
		// We need ownership of the stored values so that we remain valid even
		// if the source context is destroyed.
		m_allocMap.reserve( other.m_map.size() + 1 );
		for( auto &i : other.m_map )
		{
			auto allocIt = other.m_allocMap.find( i.first );
			if(
				allocIt != other.m_allocMap.end() &&
				i.second.references( allocIt->second.get() )
			)
			{
				// The value is already owned by `other`, and is immutable, so we
				// can just share ownership with it.
				internalSetWithOwner( i.first, i.second, ConstDataPtr( allocIt->second ) );
			}
			else
			{
				// Data not owned by `other`. Take a copy that we own, and call `internalSet()`.
				ConstDataPtr owner;
				const Value v = i.second.copy( owner );
				internalSetWithOwner( i.first, v, std::move( owner ) );
			}
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
	// We copy the value so that the client can't invalidate this context by changing it.
	ConstDataPtr copy = value->copy();
	const Value v( name, copy.get() );
	internalSetWithOwner( name, v, std::move( copy ) );
}

IECore::DataPtr Context::getAsData( const IECore::InternedString &name ) const
{
	return internalGet( name ).makeData();
}

IECore::DataPtr Context::getAsData( const IECore::InternedString &name, const IECore::DataPtr &defaultValue ) const
{
	if( const Value *value = internalGetIfExists( name ) )
	{
		return value->makeData();
	}
	return defaultValue;
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
	set<float>( g_frame, frame );
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
		sumH1 += it->second.hash().h1();
		sumH2 += it->second.hash().h2();
	}

	m_hash = MurmurHash( sumH1, sumH2 );
	m_hashValid = true;
	return m_hash;
}

bool Context::operator == ( const Context &other ) const
{
	return m_map == other.m_map;
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
	:	m_context( new Context( *context, CopyMode::NonOwning ) )
{
	m_threadState->m_context = m_context.get();
}

Context::EditableScope::EditableScope( const ThreadState &threadState )
	:	ThreadState::Scope( threadState ), m_context( new Context( *threadState.m_context, CopyMode::NonOwning ) )
{
	m_threadState->m_context = m_context.get();
}

Context::EditableScope::~EditableScope()
{
}

void Context::EditableScope::setCanceller( const IECore::Canceller *canceller )
{
	m_context->m_canceller = canceller;
}

void Context::EditableScope::setAllocated( const IECore::InternedString &name, const IECore::Data *value )
{
	m_context->set( name, value );
}

void Context::EditableScope::setFrame( float frame )
{
	m_frameStorage = frame;
	set( g_frame, &m_frameStorage );
}

void Context::EditableScope::setTime( float timeInSeconds )
{
	setFrame( timeInSeconds * m_context->getFramesPerSecond() );
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
	if( const Value *value = m_context->internalGetIfExists( internedName ) )
	{
		switch( value->typeId() )
		{
			case IECore::StringDataTypeId :
				recurse = true;
				return *static_cast<const std::string*>( value->rawValue() );
			case IECore::InternedStringDataTypeId :
				recurse = true;
				return *static_cast<const IECore::InternedString *>( value->rawValue() );
			case IECore::FloatDataTypeId :
				m_formattedString = boost::lexical_cast<std::string>(
					*static_cast<const float *>( value->rawValue() )
				);
				return m_formattedString;
			case IECore::IntDataTypeId :
				m_formattedString = boost::lexical_cast<std::string>(
					*static_cast<const int *>( value->rawValue() )
				);
				return m_formattedString;
			case IECore::InternedStringVectorDataTypeId : {
				// This is unashamedly tailored to the needs of GafferScene's `${scene:path}`
				// variable. We could make this cleaner by adding a mechanism for registering custom
				// formatters, but that would be overkill for this one use case.
				const auto &v = *static_cast<const std::vector<InternedString>* >( value->rawValue() );
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
