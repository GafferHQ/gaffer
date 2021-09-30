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

#include <cassert>

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace Gaffer;

//////////////////////////////////////////////////////////////////////////
// Key implementation
//////////////////////////////////////////////////////////////////////////

Animation::Key::Key( float time, float value, Animation::Interpolation interpolation )
	:	m_parent( nullptr ), m_time( time ), m_value( value ), m_interpolation( interpolation )
{
}

Animation::Key::~Key()
{
	// NOTE : parent reference should have been reset before the key is destructed

	assert( m_parent == 0 );
}

void Animation::Key::setTime( float time )
{
	if( time == m_time )
	{
		return;
	}

	if( m_parent )
	{
		if( KeyPtr existingKey = m_parent->getKey( time ) )
		{
			m_parent->removeKey( existingKey );
		}

		KeyPtr key = this;
		const float previousTime = m_time;
		CurvePlug *curve = m_parent;
		Action::enact(
			m_parent,
			// Do
			[ curve, time, key ] {
				assert( key->m_parent == curve );
				assert( key->m_hook.is_linked() );
				curve->m_keys.erase( curve->m_keys.iterator_to( *key ) ); // NOTE : never throws or fails
				assert( ! key->m_hook.is_linked() );
				key->m_time = time;
				assert( curve->m_keys.count( key->m_time ) == static_cast< CurvePlug::Keys::size_type >( 0 ) );
				curve->m_keys.insert( *key ); // NOTE : never throws or fails as long as no key with same time in keys
				curve->propagateDirtiness( curve->outPlug() );
			},
			// Undo
			[ curve, previousTime, key ] {
				assert( key->m_parent == curve );
				assert( key->m_hook.is_linked() );
				curve->m_keys.erase( curve->m_keys.iterator_to( *key ) ); // NOTE : never throws or fails
				assert( ! key->m_hook.is_linked() );
				key->m_time = previousTime;
				assert( curve->m_keys.count( key->m_time ) == static_cast< CurvePlug::Keys::size_type >( 0 ) );
				curve->m_keys.insert( *key ); // NOTE : never throws or fails as long as no key with same time in keys
				curve->propagateDirtiness( curve->outPlug() );
			}
		);
	}
	else
	{
		m_time = time;
	}
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

void Animation::Key::Dispose::operator()( Animation::Key* const key ) const
{
	assert( key != 0 );

	key->m_parent = nullptr;
	key->removeRef();
}

//////////////////////////////////////////////////////////////////////////
// CurvePlug implementation
//////////////////////////////////////////////////////////////////////////

GAFFER_PLUG_DEFINE_TYPE( Animation::CurvePlug );

Animation::CurvePlug::CurvePlug( const std::string &name, Direction direction, unsigned flags )
	:	ValuePlug( name, direction, flags & ~Plug::AcceptsInputs )
{
	addChild( new FloatPlug( "out", Plug::Out ) );
}

Animation::CurvePlug::~CurvePlug()
{
	m_keys.clear_and_dispose( Key::Dispose() );
}

void Animation::CurvePlug::addKey( const KeyPtr &key )
{
	if( Key *previousKey = getKey( key->getTime() ) )
	{
		if( key == previousKey )
		{
			return;
		}
		removeKey( previousKey );
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

	Action::enact(
		this,
		// Do
		[ this, key, time ] {
			if( key->m_time != time ) throw IECore::Exception( "Key time changed outside undo system." );
			assert( key->m_parent == 0 );
			assert( ! key->m_hook.is_linked() );
			assert( m_keys.count( key->m_time ) == static_cast< Keys::size_type >( 0 ) );
			m_keys.insert( *key ); // NOTE : never throws or fails as long as no key with same time in keys
			key->m_parent = this; // NOTE : never throws or fails
			key->addRef();        // NOTE : take ownership
			propagateDirtiness( outPlug() );
		},
		// Undo
		[ this, key ] {
			assert( key->m_parent == this );
			assert( key->m_hook.is_linked() );
			m_keys.erase_and_dispose( m_keys.iterator_to( *key ), Key::Dispose() );
			propagateDirtiness( outPlug() );
		}
	);
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

	Action::enact(
		this,
		// Do
		[ this, key ] {
			assert( key->m_parent == this );
			assert( key->m_hook.is_linked() );
			m_keys.erase_and_dispose( m_keys.iterator_to( *key ), Key::Dispose() );
			propagateDirtiness( outPlug() );
		},
		// Undo
		[ this, key, time ] {
			if( key->m_time != time ) throw IECore::Exception( "Key time changed outside undo system." );
			assert( key->m_parent == 0 );
			assert( ! key->m_hook.is_linked() );
			assert( m_keys.count( key->m_time ) == static_cast< Keys::size_type >( 0 ) );
			m_keys.insert( *key ); // NOTE : never throws or fails as long as no key with same time in keys
			key->m_parent = this; // NOTE : never throws or fails
			key->addRef();        // NOTE : take ownership
			propagateDirtiness( outPlug() );
		}
	);
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
