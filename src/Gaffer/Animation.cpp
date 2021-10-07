//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2015, Image Engine Design Inc. All rights reserved.
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

#include "Gaffer/Animation.h"

#include "Gaffer/Action.h"
#include "Gaffer/Context.h"

#include "OpenEXR/ImathFun.h"

#include "boost/bind.hpp"

#include <algorithm>

#include <cassert>

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace Gaffer;

//////////////////////////////////////////////////////////////////////////
// Key implementation
//////////////////////////////////////////////////////////////////////////

Animation::Key::Key( float time, float value, Animation::Interpolation interpolation )
	:	m_parent( nullptr ), m_time( time ), m_value( value ), m_interpolation( interpolation ), m_active( false )
{
}

Animation::Key::~Key()
{
	// NOTE : parent reference should have been reset before the key is destructed

	assert( m_parent == nullptr );
}

Animation::KeyPtr Animation::Key::setTime( float time )
{
	if( time == m_time )
	{
		return KeyPtr();
	}

	KeyPtr clashingKey;

	if( m_parent )
	{
		// find any clashing active key.
		clashingKey = m_parent->getKey( time );

		// if key is active find first clashing inactive key
		KeyPtr clashingInactiveKey;
		if( m_active )
		{
			const CurvePlug::InactiveKeys::iterator it = m_parent->m_inactiveKeys.find( m_time );
			if( it != m_parent->m_inactiveKeys.end() )
			{
				clashingInactiveKey = &( *it );
			}
		}

		KeyPtr key = this;
		const float previousTime = m_time;
		const bool active = m_active;
		CurvePlug* const curve = m_parent;

#		define ASSERTCONTAINSKEY( KEY, CONTAINER, RESULT ) \
			assert( ( RESULT ) == ( std::find_if( ( CONTAINER ).begin(), ( CONTAINER ).end(), \
				[ key = &( *( KEY ) ) ]( const Key& k ) { return key == & k; } ) != ( CONTAINER ).end() ) );

		Action::enact(
			m_parent,
			// Do
			[ curve, time, previousTime, active, key, clashingKey, clashingInactiveKey ] {
				// check state is as expected
				key->throwIfStateNotAsExpected( curve, active, previousTime );
				if( clashingInactiveKey )
					clashingInactiveKey->throwIfStateNotAsExpected( curve, false, previousTime );
				if( clashingKey )
					clashingKey->throwIfStateNotAsExpected( curve, true, time );
				// NOTE : If key is inactive,
				//          remove key from inactive keys container
				//        else if there is a clashing inactive key
				//          remove the clashing inactive key from inactive keys container
				//          replace key with clashing inactive key in active keys container
				//        else
				//          remove key from active keys container
				//        set time of key
				//        If there is a clashing active key,
				//          replace clashing active key with key in active container
				//          insert clashing key into inactive keys container
				//        else insert key into active keys container
				// NOTE : It is critical to the following code that the key comparison NEVER throws.
				assert( key->m_hook.is_linked() );
				if( ! active )
				{
					ASSERTCONTAINSKEY( key, curve->m_inactiveKeys, true )
					curve->m_inactiveKeys.erase( curve->m_inactiveKeys.iterator_to( *key ) );
					ASSERTCONTAINSKEY( key, curve->m_inactiveKeys, false )
				}
				else if( clashingInactiveKey )
				{
					assert( clashingInactiveKey->m_hook.is_linked() );
					ASSERTCONTAINSKEY( clashingInactiveKey, curve->m_inactiveKeys, true )
					curve->m_inactiveKeys.erase( curve->m_inactiveKeys.iterator_to( *clashingInactiveKey ) );
					ASSERTCONTAINSKEY( clashingInactiveKey, curve->m_inactiveKeys, false )
					ASSERTCONTAINSKEY( key, curve->m_keys, true )
					curve->m_keys.replace_node( curve->m_keys.iterator_to( *key ), *clashingInactiveKey );
					ASSERTCONTAINSKEY( clashingInactiveKey, curve->m_keys, true )
					ASSERTCONTAINSKEY( key, curve->m_keys, false )
					clashingInactiveKey->m_active = true;
				}
				else
				{
					ASSERTCONTAINSKEY( key, curve->m_keys, true )
					curve->m_keys.erase( curve->m_keys.iterator_to( *key ) );
					ASSERTCONTAINSKEY( key, curve->m_keys, false )
				}
				assert( ! key->m_hook.is_linked() );
				key->m_time = time;
				key->m_active = true;
				if( clashingKey )
				{
					assert( clashingKey->m_hook.is_linked() );
					ASSERTCONTAINSKEY( key, curve->m_keys, false )
					ASSERTCONTAINSKEY( key, curve->m_inactiveKeys, false )
					ASSERTCONTAINSKEY( clashingKey, curve->m_keys, true )
					curve->m_keys.replace_node( curve->m_keys.iterator_to( *clashingKey ), *key );
					ASSERTCONTAINSKEY( key, curve->m_keys, true )
					ASSERTCONTAINSKEY( clashingKey, curve->m_keys, false )
					assert( ! clashingKey->m_hook.is_linked() );
					curve->m_inactiveKeys.insert_before( curve->m_inactiveKeys.lower_bound( key->m_time ), *clashingKey );
					ASSERTCONTAINSKEY( clashingKey, curve->m_inactiveKeys, true )
					clashingKey->m_active = false;
				}
				else
				{
					assert( curve->m_keys.count( key->m_time ) == static_cast< CurvePlug::Keys::size_type >( 0 ) );
					ASSERTCONTAINSKEY( key, curve->m_keys, false )
					curve->m_keys.insert( *key );
					ASSERTCONTAINSKEY( key, curve->m_keys, true )
				}

				assert( ! key || ( key->m_active == true ) );
				assert( ! clashingKey || ( clashingKey->m_active == false ) );
				assert( ! clashingInactiveKey || ( clashingInactiveKey->m_active == true ) );
				curve->propagateDirtiness( curve->outPlug() );
			},
			// Undo
			[ curve, time, previousTime, active, key, clashingKey, clashingInactiveKey ] {
				// check state is as expected
				key->throwIfStateNotAsExpected( curve, true, time );
				if( clashingKey )
					clashingKey->throwIfStateNotAsExpected( curve, false, time );
				if( clashingInactiveKey )
					clashingInactiveKey->throwIfStateNotAsExpected( curve, true, previousTime );
				// NOTE : If there was a clashing active key
				//          remove the clashing active key from inactive keys container
				//          replace key with clashing active key in active keys container
				//        else
				//          remove key from active keys container
				//        reset time of key
				//        If key was inactive reinsert key into inactive container
				//        else if there was a clashing inactive key
				//          replace clashing inactive key with key in active container
				//          reinsert clashing inactive key into inactive keys container
				//        else reinsert key into active keys container
				// NOTE : It is critical to the following code that the key comparison NEVER throws.
				assert( key->m_hook.is_linked() );
				if( clashingKey )
				{
					assert( clashingKey->m_hook.is_linked() );
					ASSERTCONTAINSKEY( clashingKey, curve->m_inactiveKeys, true )
					curve->m_inactiveKeys.erase( curve->m_inactiveKeys.iterator_to( *clashingKey ) );
					ASSERTCONTAINSKEY( clashingKey, curve->m_inactiveKeys, false )
					ASSERTCONTAINSKEY( key, curve->m_keys, true )
					curve->m_keys.replace_node( curve->m_keys.iterator_to( *key ), *clashingKey );
					ASSERTCONTAINSKEY( clashingKey, curve->m_keys, true )
					ASSERTCONTAINSKEY( key, curve->m_keys, false )
					clashingKey->m_active = true;
				}
				else
				{
					ASSERTCONTAINSKEY( key, curve->m_keys, true )
					curve->m_keys.erase( curve->m_keys.iterator_to( *key ) );
					ASSERTCONTAINSKEY( key, curve->m_keys, false )
				}
				assert( ! key->m_hook.is_linked() );
				key->m_time = previousTime;
				key->m_active = active;
				if( ! key->m_active )
				{
					ASSERTCONTAINSKEY( key, curve->m_keys, false )
					ASSERTCONTAINSKEY( key, curve->m_inactiveKeys, false )
					curve->m_inactiveKeys.insert_before( curve->m_inactiveKeys.lower_bound( key->m_time ), *key );
					ASSERTCONTAINSKEY( key, curve->m_inactiveKeys, true )
				}
				else if( clashingInactiveKey )
				{
					assert( clashingInactiveKey->m_hook.is_linked() );
					ASSERTCONTAINSKEY( key, curve->m_keys, false )
					ASSERTCONTAINSKEY( key, curve->m_inactiveKeys, false )
					ASSERTCONTAINSKEY( clashingInactiveKey, curve->m_keys, true )
					curve->m_keys.replace_node( curve->m_keys.iterator_to( *clashingInactiveKey ), *key );
					ASSERTCONTAINSKEY( key, curve->m_keys, true )
					ASSERTCONTAINSKEY( clashingInactiveKey, curve->m_keys, false )
					ASSERTCONTAINSKEY( clashingInactiveKey, curve->m_inactiveKeys, false )
					curve->m_inactiveKeys.insert_before( curve->m_inactiveKeys.lower_bound( key->m_time ), *clashingInactiveKey );
					ASSERTCONTAINSKEY( clashingInactiveKey, curve->m_inactiveKeys, true )
					clashingInactiveKey->m_active = false;
				}
				else
				{
					assert( curve->m_keys.count( key->m_time ) == static_cast< CurvePlug::Keys::size_type >( 0 ) );
					ASSERTCONTAINSKEY( key, curve->m_keys, false )
					curve->m_keys.insert( *key );
					ASSERTCONTAINSKEY( key, curve->m_keys, true )
				}

				assert( ! key || ( key->m_active == active ) );
				assert( ! clashingKey || ( clashingKey->m_active == true ) );
				assert( ! clashingInactiveKey || ( clashingInactiveKey->m_active == false ) );
				curve->propagateDirtiness( curve->outPlug() );
			}
		);

#		undef ASSERTCONTAINSKEY
	}
	else
	{
		m_time = time;
	}

	return clashingKey;
}

void Animation::Key::setValue( float value )
{
	if( value == m_value )
	{
		return;
	}

	if( m_parent )
	{
		KeyPtr k = this;
		const float previousValue = m_value;
		Action::enact(
			m_parent,
			// Do
			[ k, value ] {
				k->m_value = value;
				k->m_parent->propagateDirtiness( k->m_parent->outPlug() );
			},
			// Undo
			[ k, previousValue ] {
				k->m_value = previousValue;
				k->m_parent->propagateDirtiness( k->m_parent->outPlug() );
			}
		);
	}
	else
	{
		m_value = value;
	}
}

Animation::Interpolation Animation::Key::getInterpolation() const
{
	return m_interpolation;
}

void Animation::Key::setInterpolation( Animation::Interpolation interpolation )
{
	if( interpolation == m_interpolation )
	{
		return;
	}

	if( m_parent )
	{
		KeyPtr k = this;
		const Animation::Interpolation previousInterpolation = m_interpolation;
		Action::enact(
			m_parent,
			// Do
			[ k, interpolation ] {
				k->m_interpolation = interpolation;
				k->m_parent->propagateDirtiness( k->m_parent->outPlug() );
			},
			// Undo
			[ k, previousInterpolation ] {
				k->m_interpolation = previousInterpolation;
				k->m_parent->propagateDirtiness( k->m_parent->outPlug() );
			}
		);
	}
	else
	{
		m_interpolation = interpolation;
	}
}

bool Animation::Key::isActive() const
{
	return m_active;
}

bool Animation::Key::operator == ( const Key &rhs ) const
{
	return
		m_time == rhs.m_time &&
		m_value == rhs.m_value &&
		m_interpolation == rhs.m_interpolation;
}

bool Animation::Key::operator != ( const Key &rhs ) const
{
	return !(*this == rhs);
}

Animation::CurvePlug *Animation::Key::parent()
{
	return m_parent;
}

const Animation::CurvePlug *Animation::Key::parent() const
{
	return m_parent;
}

void Animation::Key::throwIfStateNotAsExpected( const Animation::CurvePlug* const curve, const bool active, const float time ) const
{
	// check that state is as expected
	//
	// NOTE : state may be changed outside the undo system and therefore not be as expected in
	//        which case throw an appropriate exception so user is informed of invalid api usage.

	if( m_parent != curve )
	{
		throw IECore::Exception( "Key parent changed outside undo system." );
	}

	if( m_active != active )
	{
		throw IECore::Exception( "Key active changed outside undo system." );
	}

	if( m_time != time )
	{
		throw IECore::Exception( "Key time changed outside undo system." );
	}
}

void Animation::Key::Dispose::operator()( Animation::Key* const key ) const
{
	assert( key != nullptr );

	key->m_parent = nullptr;
	key->m_active = false;
	key->removeRef();
}

//////////////////////////////////////////////////////////////////////////
// CurvePlug implementation
//////////////////////////////////////////////////////////////////////////

GAFFER_PLUG_DEFINE_TYPE( Animation::CurvePlug );

Animation::CurvePlug::CurvePlug( const std::string &name, const Direction direction, const unsigned flags )
: ValuePlug( name, direction, flags & ~Plug::AcceptsInputs )
, m_keys()
, m_inactiveKeys()
, m_keyAddedSignal()
, m_keyRemovedSignal()
{
	addChild( new FloatPlug( "out", Plug::Out ) );
}

Animation::CurvePlug::~CurvePlug()
{
	m_keys.clear_and_dispose( Key::Dispose() );
	m_inactiveKeys.clear_and_dispose( Key::Dispose() );
}

Animation::CurvePlug::CurvePlugKeySignal& Animation::CurvePlug::keyAddedSignal()
{
	return m_keyAddedSignal;
}

Animation::CurvePlug::CurvePlugKeySignal& Animation::CurvePlug::keyRemovedSignal()
{
	return m_keyRemovedSignal;
}

Animation::KeyPtr Animation::CurvePlug::addKey( const Animation::KeyPtr &key, const bool removeActiveClashing )
{
	const KeyPtr clashingKey = getKey( key->m_time );

	if( clashingKey )
	{
		if( key == clashingKey )
		{
			return KeyPtr();
		}
	}

	if( key->m_parent )
	{
		key->m_parent->removeKey( key.get() );
	}

	// save the time of the key at the point it is added in case it was previously
	// removed from the curve and changes have been made whilst the key was outside
	// the curve (these changes will not have been recorded in the undo/redo system)
	// when redo is called we can then check for any change and throw an exception
	// if time is not as we expect it to be. principle here is that the user should
	// not make changes outside the undo system so if they have then let them know.

	const float time = key->m_time;

#	define ASSERTCONTAINSKEY( KEY, CONTAINER, RESULT ) \
		assert( ( RESULT ) == ( std::find_if( ( CONTAINER ).begin(), ( CONTAINER ).end(), \
			[ key = &( *( KEY ) ) ]( const Key& k ) { return key == & k; } ) != ( CONTAINER ).end() ) );

	Action::enact(
		this,
		// Do
		[ this, key, clashingKey, time ] {
			// check state is as expected
			key->throwIfStateNotAsExpected( nullptr, false, time );
			if( clashingKey )
				clashingKey->throwIfStateNotAsExpected( this, true, time );
			// NOTE : If there is a clashing key,
			//          replace clashing key with key in active container
			//          insert clashing key into inactive keys container
			//        else insert key into active keys container
			// NOTE : It is critical to the following code that the key comparison NEVER throws.
			assert( ! key->m_hook.is_linked() );
			if( clashingKey )
			{
				assert( clashingKey->m_hook.is_linked() );
				ASSERTCONTAINSKEY( key, m_keys, false )
				ASSERTCONTAINSKEY( key, m_inactiveKeys, false )
				ASSERTCONTAINSKEY( clashingKey, m_keys, true )
				m_keys.replace_node( m_keys.iterator_to( *clashingKey ), *key );
				ASSERTCONTAINSKEY( key, m_keys, true )
				ASSERTCONTAINSKEY( clashingKey, m_keys, false )
				m_inactiveKeys.insert_before( m_inactiveKeys.lower_bound( time ), *clashingKey );
				ASSERTCONTAINSKEY( clashingKey, m_inactiveKeys, true )
				clashingKey->m_active = false;
			}
			else
			{
				assert( m_keys.count( key->m_time ) == static_cast< Keys::size_type >( 0 ) );
				ASSERTCONTAINSKEY( key, m_keys, false )
				m_keys.insert( *key );
				ASSERTCONTAINSKEY( key, m_keys, true )
			}
			key->m_parent = this; // NOTE : never throws or fails
			key->addRef();        // NOTE : take ownership
			key->m_active = true;
			m_keyAddedSignal( this, key.get() );
			propagateDirtiness( outPlug() );
		},
		// Undo
		[ this, key, clashingKey, time ] {
			// check state is as expected
			key->throwIfStateNotAsExpected( this, true, time );
			if( clashingKey )
				clashingKey->throwIfStateNotAsExpected( this, false, time );
			// NOTE : If there was a clashing key
			//          remove the clashing key from inactive keys container
			//          replace key with clashing key in active keys container
			//        else
			//          remove key from active keys container
			// NOTE : It is critical to the following code that the key comparison NEVER throws.
			assert( key->m_hook.is_linked() );
			if( clashingKey )
			{
				assert( clashingKey->m_hook.is_linked() );
				ASSERTCONTAINSKEY( clashingKey, m_inactiveKeys, true )
				m_inactiveKeys.erase( m_inactiveKeys.iterator_to( *clashingKey ) );
				ASSERTCONTAINSKEY( clashingKey, m_inactiveKeys, false )
				ASSERTCONTAINSKEY( key, m_keys, true )
				m_keys.replace_node( m_keys.iterator_to( *key ), *clashingKey );
				Key::Dispose()( key.get() );
				ASSERTCONTAINSKEY( clashingKey, m_keys, true )
				ASSERTCONTAINSKEY( key, m_keys, false )
				clashingKey->m_active = true;
			}
			else
			{
				assert( key->m_active == true );
				ASSERTCONTAINSKEY( key, m_keys, true )
				m_keys.erase_and_dispose( m_keys.iterator_to( *key ), Key::Dispose() );
				ASSERTCONTAINSKEY( key, m_keys, false )
			}
			m_keyRemovedSignal( this, key.get() );
			propagateDirtiness( outPlug() );
		}
	);

#	undef ASSERTCONTAINSKEY

	// remove the clashing key

	if( clashingKey && removeActiveClashing )
	{
		removeKey( clashingKey );
	}

	return clashingKey;
}

bool Animation::CurvePlug::hasKey( float time ) const
{
	return m_keys.find( time ) != m_keys.end();
}

Animation::Key *Animation::CurvePlug::getKey( float time )
{
	return const_cast< Key* >( static_cast< const CurvePlug* >( this )->getKey( time ) );
}

const Animation::Key *Animation::CurvePlug::getKey( float time ) const
{
	Keys::const_iterator it = m_keys.find( time );
	return ( it != m_keys.end() )
		? &( *it )
		: nullptr;
}

void Animation::CurvePlug::removeKey( const KeyPtr &key )
{
	if( key->m_parent != this )
	{
		throw IECore::Exception( "Key is not a child" );
	}

	// save the time of the key at the point it is removed in case it is subsequently
	// added back to the curve and changes are made whilst the key is outside
	// the curve (these changes will not be recorded in the undo/redo system)
	// when undo is called we can then check for any change and throw an exception
	// if time is not as we expect it to be. principle here is that the user should
	// not make changes outside the undo system so if they have then let them know.

	const float time = key->m_time;

	// if key is active find first clashing inactive key
	KeyPtr clashingKey;
	if( key->m_active )
	{
		const InactiveKeys::iterator it = m_inactiveKeys.find( key->m_time );
		if( it != m_inactiveKeys.end() )
		{
			clashingKey = &( *it );
		}
	}

	const bool active = key->m_active;

#	define ASSERTCONTAINSKEY( KEY, CONTAINER, RESULT ) \
		assert( ( RESULT ) == ( std::find_if( ( CONTAINER ).begin(), ( CONTAINER ).end(), \
			[ key = &( *( KEY ) ) ]( const Key& k ) { return key == & k; } ) != ( CONTAINER ).end() ) );

	Action::enact(
		this,
		// Do
		[ this, key, clashingKey, active, time ] {
			// check state is as expected
			key->throwIfStateNotAsExpected( this, active, time );
			if( clashingKey )
				clashingKey->throwIfStateNotAsExpected( this, false, time );
			// NOTE : If key is inactive,
			//          remove key from inactive keys container
			//        else if there is a clashing key
			//          remove the clashing key from inactive keys container
			//          replace key with clashing key in active keys container
			//        else
			//          remove key from active keys container
			// NOTE : It is critical to the following code that the key comparison NEVER throws.
			assert( key->m_hook.is_linked() );
			if( ! active )
			{
				ASSERTCONTAINSKEY( key, m_inactiveKeys, true )
				m_inactiveKeys.erase_and_dispose( m_inactiveKeys.iterator_to( *key ), Key::Dispose() );
				ASSERTCONTAINSKEY( key, m_inactiveKeys, false )
			}
			else if( clashingKey )
			{
				assert( clashingKey->m_hook.is_linked() );
				ASSERTCONTAINSKEY( clashingKey, m_inactiveKeys, true )
				m_inactiveKeys.erase( m_inactiveKeys.iterator_to( *clashingKey ) );
				ASSERTCONTAINSKEY( clashingKey, m_inactiveKeys, false )
				ASSERTCONTAINSKEY( key, m_keys, true )
				m_keys.replace_node( m_keys.iterator_to( *key ), *clashingKey );
				Key::Dispose()( key.get() );
				ASSERTCONTAINSKEY( key, m_keys, false )
				ASSERTCONTAINSKEY( clashingKey, m_keys, true )
				clashingKey->m_active = true;
			}
			else
			{
				ASSERTCONTAINSKEY( key, m_keys, true )
				m_keys.erase_and_dispose( m_keys.iterator_to( *key ), Key::Dispose() );
				ASSERTCONTAINSKEY( key, m_keys, false )
			}
			m_keyRemovedSignal( this, key.get() );
			propagateDirtiness( outPlug() );
		},
		// Undo
		[ this, key, clashingKey, active, time ] {
			// check state is as expected
			key->throwIfStateNotAsExpected( nullptr, false, time );
			if( clashingKey )
				clashingKey->throwIfStateNotAsExpected( this, true, time );
			// NOTE : If key was inactive reinsert key into inactive container
			//        else if there was a clashing key
			//          replace clashing key with key in active container
			//          reinsert clashing key into inactive keys container
			//        else reinsert key into active keys container
			// NOTE : It is critical to the following code that the key comparison NEVER throws.
			assert( ! key->m_hook.is_linked() );
			if( ! active )
			{
				ASSERTCONTAINSKEY( key, m_keys, false )
				ASSERTCONTAINSKEY( key, m_inactiveKeys, false )
				m_inactiveKeys.insert_before( m_inactiveKeys.lower_bound( time ), *key );
				ASSERTCONTAINSKEY( key, m_inactiveKeys, true )
			}
			else if( clashingKey )
			{
				assert( clashingKey->m_hook.is_linked() );
				ASSERTCONTAINSKEY( key, m_keys, false )
				ASSERTCONTAINSKEY( key, m_inactiveKeys, false )
				ASSERTCONTAINSKEY( clashingKey, m_keys, true )
				m_keys.replace_node( m_keys.iterator_to( *clashingKey ), *key );
				ASSERTCONTAINSKEY( key, m_keys, true )
				ASSERTCONTAINSKEY( clashingKey, m_keys, false )
				m_inactiveKeys.insert_before( m_inactiveKeys.lower_bound( time ), *clashingKey );
				ASSERTCONTAINSKEY( clashingKey, m_inactiveKeys, true )
				clashingKey->m_active = false;
			}
			else
			{
				assert( m_keys.count( key->m_time ) == static_cast< Keys::size_type >( 0 ) );
				ASSERTCONTAINSKEY( key, m_keys, false )
				m_keys.insert( *key );
				ASSERTCONTAINSKEY( key, m_keys, true )
			}
			key->m_parent = this; // NOTE : never throws or fails
			key->addRef();        // NOTE : take ownership
			key->m_active = active;
			m_keyAddedSignal( this, key.get() );
			propagateDirtiness( outPlug() );
		}
	);

#	undef ASSERTCONTAINSKEY
}

void Animation::CurvePlug::removeInactiveKeys()
{
	for( InactiveKeys::iterator it = m_inactiveKeys.begin(), itEnd = m_inactiveKeys.end(); it != itEnd; )
	{
		removeKey( &( *it++ ) );
	}
}

Animation::Key *Animation::CurvePlug::closestKey( float time )
{
	return const_cast<Animation::Key *>( const_cast<const CurvePlug *>( this )->closestKey( time ) );
}

const Animation::Key *Animation::CurvePlug::closestKey( float time ) const
{
	if( m_keys.empty() )
	{
		return nullptr;
	}

	Keys::const_iterator rightIt = m_keys.lower_bound( time );
	if( rightIt == m_keys.end() )
	{
		return &( *( m_keys.rbegin() ) );
	}
	else if( rightIt->m_time == time || rightIt == m_keys.begin() )
	{
		return &( *( rightIt ) );
	}
	else
	{
		Keys::const_iterator leftIt = std::prev( rightIt );
		return &( *( fabs( time - leftIt->m_time ) < fabs( time - rightIt->m_time ) ? leftIt : rightIt ) );
	}
}

Animation::Key *Animation::CurvePlug::closestKey( float time, float maxDistance )
{
	return const_cast<Animation::Key *>( const_cast<const CurvePlug *>( this )->closestKey( time, maxDistance ) );
}

const Animation::Key *Animation::CurvePlug::closestKey( float time, float maxDistance ) const
{
	const Animation::Key *candidate = closestKey( time );

	if( !candidate || fabs( candidate->getTime() - time) > maxDistance )
	{
		return nullptr;
	}

	return candidate;
}

Animation::Key *Animation::CurvePlug::previousKey( float time )
{
	return const_cast<Animation::Key *>( const_cast<const CurvePlug *>( this )->previousKey( time ) );
}

const Animation::Key *Animation::CurvePlug::previousKey( float time ) const
{
	Keys::const_iterator rightIt = m_keys.lower_bound( time );
	return ( rightIt != m_keys.begin() )
		? &( *( std::prev( rightIt ) ) )
		: nullptr;
}

Animation::Key *Animation::CurvePlug::nextKey( float time )
{
	return const_cast<Animation::Key *>( const_cast<const CurvePlug *>( this )->nextKey( time ) );
}

const Animation::Key *Animation::CurvePlug::nextKey( float time ) const
{
	Keys::const_iterator rightIt = m_keys.upper_bound( time );
	return ( rightIt != m_keys.end() )
		? &( *( rightIt ) )
		: nullptr;
}

Animation::CurvePlug::TimeKey::type Animation::CurvePlug::TimeKey::operator()( const Animation::Key& key ) const
{
	return key.getTime();
}

Animation::KeyIterator Animation::CurvePlug::begin()
{
	return m_keys.begin();
}

Animation::KeyIterator Animation::CurvePlug::end()
{
	return m_keys.end();
}

Animation::ConstKeyIterator Animation::CurvePlug::begin() const
{
	return m_keys.begin();
}

Animation::ConstKeyIterator Animation::CurvePlug::end() const
{
	return m_keys.end();
}

float Animation::CurvePlug::evaluate( float time ) const
{
	if( m_keys.empty() )
	{
		return 0;
	}

	Keys::const_iterator rightIt = m_keys.lower_bound( time );
	if( rightIt == m_keys.end() )
	{
		return (m_keys.rbegin())->getValue();
	}

	const Key &right = *( rightIt );
	if( right.getTime() == time || rightIt == m_keys.begin() )
	{
		return right.getValue();
	}

	const Key &left = *( std::prev( rightIt ) );
	if( right.getInterpolation() == Interpolation::Linear )
	{
		const float t = ( time - left.getTime() ) / ( right.getTime() - left.getTime() );
		return Imath::lerp( left.getValue(), right.getValue(), t );
	}
	else
	{
		// Step. We already dealt with the case where we're
		// exactly at the time of the right keyframe, so we
		// just return the value of the left keyframe.
		return left.getValue();
	}

	return 0;
}

FloatPlug *Animation::CurvePlug::outPlug()
{
	return getChild<FloatPlug>( 0 );
}

const FloatPlug *Animation::CurvePlug::outPlug() const
{
	return getChild<FloatPlug>( 0 );
}

//////////////////////////////////////////////////////////////////////////
// Animation implementation
//////////////////////////////////////////////////////////////////////////

GAFFER_NODE_DEFINE_TYPE( Animation );

size_t Animation::g_firstPlugIndex = 0;

Animation::Animation( const std::string &name )
	:	ComputeNode( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );

	addChild( new Plug( "curves" ) );
}

Animation::~Animation()
{
}

Plug *Animation::curvesPlug()
{
	return getChild<Plug>( g_firstPlugIndex );
}

const Plug *Animation::curvesPlug() const
{
	return getChild<Plug>( g_firstPlugIndex );
}

bool Animation::canAnimate( const ValuePlug *plug )
{
	if( !plug->getFlags( Plug::AcceptsInputs ) )
	{
		return false;
	}

	if( plug->getInput() && !isAnimated( plug ) )
	{
		return false;
	}

	const Node *node = plug->node();
	if( !node || !node->parent<Node>() )
	{
		// Nowhere to parent our Animation node.
		return false;
	}

	return
		runTimeCast<const FloatPlug>( plug ) ||
		runTimeCast<const IntPlug>( plug ) ||
		runTimeCast<const BoolPlug>( plug );
}

bool Animation::isAnimated( const ValuePlug *plug )
{
	return inputCurve( plug );
}

Animation::CurvePlug *Animation::acquire( ValuePlug *plug )
{
	// If the plug is already driven by a curve, return it.
	if( CurvePlug *curve = inputCurve( plug ) )
	{
		return curve;
	}

	// Otherwise we need to make one. Try to find an
	// existing Animation driving plugs on the same node.

	AnimationPtr animation;
	if( !plug->node() )
	{
		throw IECore::Exception( "Plug does not belong to a node" );
	}

	for( Plug::RecursiveIterator it( plug->node() ); !it.done(); ++it )
	{
		ValuePlug *valuePlug = runTimeCast<ValuePlug>( it->get() );
		if( !valuePlug )
		{
			continue;
		}

		if( CurvePlug *curve = inputCurve( valuePlug ) )
		{
			animation = runTimeCast<Animation>( curve->node() );
			if( animation )
			{
				break;
			}
		}
	}

	// If we couldn't find an existing Animation, then
	// make one.
	if( !animation )
	{
		Node *parent = plug->node()->parent<Node>();
		if( !parent )
		{
			throw IECore::Exception( "Node does not have a parent" );
		}
		animation = new Animation;
		parent->addChild( animation );
	}

	// Add a curve to the animation, and hook it up to
	// the target plug.

	CurvePlugPtr curve = new CurvePlug( "curve0", Plug::In, Plug::Default | Plug::Dynamic );
	animation->curvesPlug()->addChild( curve );

	plug->setInput( curve->outPlug() );

	return curve.get();
}

Animation::CurvePlug *Animation::inputCurve( ValuePlug *plug )
{
	ValuePlug *source = plug->source<ValuePlug>();
	if( source == plug ) // no input
	{
		return nullptr;
	}

	CurvePlug *curve = source->parent<CurvePlug>();
	if( !curve )
	{
		return nullptr;
	}

	if( source == curve->outPlug() )
	{
		return curve;
	}

	return nullptr;
}

const Animation::CurvePlug *Animation::inputCurve( const ValuePlug *plug )
{
	// preferring cast over maintaining two near-identical methods.
	return inputCurve( const_cast<ValuePlug *>( plug ) );
}

void Animation::affects( const Plug *input, AffectedPlugsContainer &outputs ) const
{
	ComputeNode::affects( input, outputs );
}

void Animation::hash( const ValuePlug *output, const Context *context, IECore::MurmurHash &h ) const
{
	ComputeNode::hash( output, context, h );

	if( const CurvePlug *parent = output->parent<CurvePlug>() )
	{
		h.append( parent->evaluate( context->getTime() ) );
	}
}

void Animation::compute( ValuePlug *output, const Context *context ) const
{
	if( const CurvePlug *parent = output->parent<CurvePlug>() )
	{
		static_cast<FloatPlug *>( output )->setValue( parent->evaluate( context->getTime() ) );
		return;
	}

	ComputeNode::compute( output, context );
}

ValuePlug::CachePolicy Animation::computeCachePolicy( const Gaffer::ValuePlug *output ) const
{
	if( output->parent<CurvePlug>() )
	{
		return ValuePlug::CachePolicy::Uncached;
	}

	return ComputeNode::computeCachePolicy( output );
}
