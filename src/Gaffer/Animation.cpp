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

#include "boost/bind.hpp"

#include "OpenEXR/ImathFun.h"

#include "Gaffer/Animation.h"
#include "Gaffer/Context.h"
#include "Gaffer/Action.h"

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace Gaffer;

//////////////////////////////////////////////////////////////////////////
// Key implementation
//////////////////////////////////////////////////////////////////////////

Animation::Key::Key()
	:	time( 0.0f ), value( 0.0f ), type( Invalid )
{

}

Animation::Key::Key( float time, float value, Type type )
	:	time( time ), value( value ), type( type )
{
}

bool Animation::Key::operator == ( const Key &rhs ) const
{
	return
		time == rhs.time &&
		value == rhs.value &&
		type == rhs.type;
}

bool Animation::Key::operator != ( const Key &rhs ) const
{
	return !(*this == rhs);
}

bool Animation::Key::operator < ( const Key &rhs ) const
{
	return time < rhs.time;
}

Animation::Key::operator bool() const
{
	return type != Invalid;
}

//////////////////////////////////////////////////////////////////////////
// CurvePlug implementation
//////////////////////////////////////////////////////////////////////////

IE_CORE_DEFINERUNTIMETYPED( Animation::CurvePlug );

Animation::CurvePlug::CurvePlug( const std::string &name, Direction direction, unsigned flags )
	:	ValuePlug( name, direction, flags & ~Plug::AcceptsInputs )
{
	addChild( new FloatPlug( "out", Plug::Out ) );
	outPlug()->setFlags( Plug::Cacheable, false );
}

void Animation::CurvePlug::addKey( const Key &key )
{
	Key existingKey = getKey( key.time );
	Action::enact(
		this,
		boost::bind( &CurvePlug::addOrRemoveKeyInternal, this, key ),
		boost::bind( &CurvePlug::addOrRemoveKeyInternal, this, existingKey )
	);
}

bool Animation::CurvePlug::hasKey( float time ) const
{
	return m_keys.find( time ) != m_keys.end();
}

Animation::Key Animation::CurvePlug::getKey( float time ) const
{
	Keys::const_iterator it = m_keys.find( time );
	if( it == m_keys.end() )
	{
		return Key( time, 0.0f, Animation::Invalid );
	}
	return *it;
}

Animation::Key Animation::CurvePlug::closestKey( float time ) const
{
	if( m_keys.empty() )
	{
		return Key();
	}

	Keys::const_iterator rightIt = m_keys.lower_bound( time );
	if( rightIt == m_keys.end() )
	{
		return *m_keys.rbegin();
	}
	else if( rightIt->time == time || rightIt == m_keys.begin() )
	{
		return *rightIt;
	}
	else
	{
		Keys::const_iterator leftIt = rightIt; leftIt--;
		return fabs( time - leftIt->time ) < fabs( time - rightIt->time ) ? *leftIt : *rightIt;
	}
}

Animation::Key Animation::CurvePlug::previousKey( float time ) const
{
	Keys::const_iterator rightIt = m_keys.lower_bound( time );
	if( rightIt == m_keys.begin() )
	{
		return Key();
	}
	return *(--rightIt);
}

Animation::Key Animation::CurvePlug::nextKey( float time ) const
{
	Keys::const_iterator rightIt = m_keys.upper_bound( time );
	if( rightIt == m_keys.end() )
	{
		return Key();
	}
	return *rightIt;
}

void Animation::CurvePlug::removeKey( float time )
{
	Key existingKey = getKey( time );
	if( !existingKey )
	{
		return;
	}

	Action::enact(
		this,
		boost::bind( &CurvePlug::addOrRemoveKeyInternal, this, Key( time, 0.0f, Animation::Invalid ) ),
		boost::bind( &CurvePlug::addOrRemoveKeyInternal, this, existingKey )
	);
}

const Animation::CurvePlug::Keys &Animation::CurvePlug::keys() const
{
	return m_keys;
}

float Animation::CurvePlug::evaluate( float time ) const
{
	if( m_keys.empty() )
	{
		return 0;
	}

	Keys::const_iterator right = m_keys.lower_bound( time );
	if( right == m_keys.end() )
	{
		return m_keys.rbegin()->value;
	}

	if( right->time == time || right == m_keys.begin() )
	{
		return right->value;
	}

	Keys::const_iterator left = right; left--;
	if( right->type == Linear )
	{
		const float t = ( time - left->time ) / ( right->time - left->time );
		return Imath::lerp( left->value, right->value, t );
	}
	else
	{
		// Step. We already dealt with the case where we're
		// exactly at the time of the right keyframe, so we
		// just return the value of the left keyframe.
		return left->value;
	}
}

FloatPlug *Animation::CurvePlug::outPlug()
{
	return getChild<FloatPlug>( 0 );
}

const FloatPlug *Animation::CurvePlug::outPlug() const
{
	return getChild<FloatPlug>( 0 );
}

void Animation::CurvePlug::addOrRemoveKeyInternal( const Key &key )
{
	if( !key )
	{
		m_keys.erase( key );
	}
	else
	{
		m_keys.erase( key );
		m_keys.insert( key );
	}
	propagateDirtiness( outPlug() );
}

//////////////////////////////////////////////////////////////////////////
// Animation implementation
//////////////////////////////////////////////////////////////////////////

IE_CORE_DEFINERUNTIMETYPED( Animation );

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
	if( plug->getFlags( Plug::ReadOnly ) )
	{
		return false;
	}
	if( !plug->getFlags( Plug::AcceptsInputs ) )
	{
		return false;
	}

	if( plug->getInput<Plug>() && !isAnimated( plug ) )
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

	for( RecursivePlugIterator it( plug->node() ); !it.done(); ++it )
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
		return NULL;
	}

	CurvePlug *curve = source->parent<CurvePlug>();
	if( !curve )
	{
		return NULL;
	}

	if( source == curve->outPlug() )
	{
		return curve;
	}

	return NULL;
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
