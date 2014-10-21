//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2011-2012, John Haddon. All rights reserved.
//  Copyright (c) 2011-2013, Image Engine Design Inc. All rights reserved.
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
#include "boost/bind/placeholders.hpp"
#include "boost/format.hpp"

#include "IECore/MurmurHash.h"

#include "Gaffer/CompoundPlug.h"
#include "Gaffer/Node.h"
#include "Gaffer/BlockedConnection.h"

using namespace Gaffer;
using namespace boost;

IE_CORE_DEFINERUNTIMETYPED( CompoundPlug )

CompoundPlug::CompoundPlug( const std::string &name, Direction direction, unsigned flags )
	:	ValuePlug( name, direction, flags )
{
	childAddedSignal().connect( boost::bind( &CompoundPlug::childAddedOrRemoved, this ) );
	childRemovedSignal().connect( boost::bind( &CompoundPlug::childAddedOrRemoved, this ) );
}

CompoundPlug::~CompoundPlug()
{
}

PlugPtr CompoundPlug::createCounterpart( const std::string &name, Direction direction ) const
{
	CompoundPlugPtr result = new CompoundPlug( name, direction, getFlags() );
	for( PlugIterator it( this ); it != it.end(); it++ )
	{
		result->addChild( (*it)->createCounterpart( (*it)->getName(), direction ) );
	}
	return result;
}

bool CompoundPlug::settable() const
{
	ChildContainer::const_iterator it, eIt;
	for( it=children().begin(), eIt=children().end(); it!=eIt; ++it )
	{
		ValuePlug *valuePlug = IECore::runTimeCast<ValuePlug>( it->get() );
		if( !valuePlug || !valuePlug->settable() )
		{
			return false;
		}
	}
	return true;
}

void CompoundPlug::setToDefault()
{
	ChildContainer::const_iterator it;
	for( it=children().begin(); it!=children().end(); it++ )
	{
		ValuePlug *valuePlug = IECore::runTimeCast<ValuePlug>( it->get() );
		if( valuePlug )
		{
			valuePlug->setToDefault();
		}
	}
}

void CompoundPlug::setFrom( const ValuePlug *other )
{
	const CompoundPlug *typedOther = IECore::runTimeCast<const CompoundPlug>( other );
	if( !typedOther )
	{
		throw IECore::Exception( "Unsupported plug type" );
	}

	ChildContainer::const_iterator it, otherIt;
	for( it = children().begin(), otherIt = typedOther->children().begin(); it!=children().end() && otherIt!=typedOther->children().end(); it++, otherIt++ )
	{
		ValuePlug *child = IECore::runTimeCast<ValuePlug>( it->get() );
		const ValuePlug *otherChild = IECore::runTimeCast<ValuePlug>( otherIt->get() );
		if( !child || !otherChild )
		{
			throw IECore::Exception( "Children are not ValuePlugs" );
		}
		child->setFrom( otherChild );
	}
}

IECore::MurmurHash CompoundPlug::hash() const
{
	IECore::MurmurHash h;
	for( ValuePlugIterator it( this ); it!=it.end(); it++ )
	{
		/// \todo Do we need to hash the child names too?
		(*it)->hash( h );
	}
	return h;
}

void CompoundPlug::hash( IECore::MurmurHash &h ) const
{
	ValuePlug::hash( h );
}

void CompoundPlug::childAddedOrRemoved()
{
	// addition or removal of a child to a compound is considered to
	// change its value, so we emit the appropriate signal. this is
	// mostly of use for the SplinePlug, as points are added by adding
	// plugs and removed by removing them.
	/// \todo Do we really need this?
	emitPlugSet();
}
