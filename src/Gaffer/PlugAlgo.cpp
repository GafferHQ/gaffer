//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2012, John Haddon. All rights reserved.
//  Copyright (c) 2014, Image Engine Design Inc. All rights reserved.
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

#include "boost/format.hpp"
#include "boost/algorithm/string/replace.hpp"
#include "boost/algorithm/string/predicate.hpp"

#include "Gaffer/ValuePlug.h"
#include "Gaffer/Node.h"
#include "Gaffer/PlugAlgo.h"
#include "Gaffer/MetadataAlgo.h"
#include "Gaffer/Box.h"

using namespace std;
using namespace IECore;
using namespace Gaffer;

//////////////////////////////////////////////////////////////////////////
// Replace
//////////////////////////////////////////////////////////////////////////

namespace
{

struct Connections
{
	Plug *plug;
	PlugPtr input;
	vector<PlugPtr> outputs;
};

typedef vector<Connections> ConnectionsVector;

void replacePlugWalk( Plug *existingPlug, Plug *plug, ConnectionsVector &connections )
{
	// Record output connections.
	Connections c;
	c.plug = plug;
	c.outputs.insert( c.outputs.begin(), existingPlug->outputs().begin(), existingPlug->outputs().end() );

	if( plug->children().size() )
	{
		// Recurse
		for( PlugIterator it( plug ); !it.done(); ++it )
		{
			if( Plug *existingChildPlug = existingPlug->getChild<Plug>( (*it)->getName() ) )
			{
				replacePlugWalk( existingChildPlug, it->get(), connections );
			}
		}
	}
	else
	{
		// At a leaf - record input connection and transfer values if
		// necessary. We only store inputs for leaves because automatic
		// connection tracking will take care of connecting the parent
		// levels when all children are connected.
		c.input = existingPlug->getInput();
		if( !c.input && plug->direction() == Plug::In )
		{
			ValuePlug *existingValuePlug = runTimeCast<ValuePlug>( existingPlug );
			ValuePlug *valuePlug = runTimeCast<ValuePlug>( plug );
			if( existingValuePlug && valuePlug )
			{
				valuePlug->setFrom( existingValuePlug );
			}
		}
	}

	connections.push_back( c );
}

} // namespace

namespace Gaffer
{

namespace PlugAlgo
{

void replacePlug( Gaffer::GraphComponent *parent, PlugPtr plug )
{
	Plug *existingPlug = parent->getChild<Plug>( plug->getName() );
	if( !existingPlug )
	{
		parent->addChild( plug );
		return;
	}

	// Transfer values where necessary, and store connections
	// to transfer after reparenting.

	ConnectionsVector connections;
	replacePlugWalk( existingPlug, plug.get(), connections );

	// Replace old plug by parenting in new one.

	parent->setChild( plug->getName(), plug );

	// Transfer old connections. We do this after
	// parenting because downstream acceptsInput() methods
	// might care what sort of node the connection is coming
	// from.

	for( ConnectionsVector::const_iterator it = connections.begin(), eIt = connections.end(); it != eIt; ++it )
	{
		if( it->input )
		{
			it->plug->setInput( it->input.get() );
		}
		for( vector<PlugPtr>::const_iterator oIt = it->outputs.begin(), oeIt = it->outputs.end(); oIt != oeIt; ++oIt )
		{
			(*oIt)->setInput( it->plug );
		}
	}
}

} // namespace PlugAlgo

} // namespace Gaffer

//////////////////////////////////////////////////////////////////////////
// Promotion
//////////////////////////////////////////////////////////////////////////

namespace
{

Node *externalNode( Plug *plug )
{
	Node *node = plug->node();
	return node ? node->parent<Node>() : nullptr;
}

const Node *externalNode( const Plug *plug )
{
	const Node *node = plug->node();
	return node ? node->parent<Node>() : nullptr;
}

bool validatePromotability( const Plug *plug, const Plug *parent, bool throwExceptions, bool childPlug = false )
{
	if( !plug )
	{
		if( !throwExceptions )
		{
			return false;
		}
		else
		{
			throw IECore::Exception(  "Cannot promote null plug" );
		}
	}

	if( PlugAlgo::isPromoted( plug ) )
	{
		if( !throwExceptions )
		{
			return false;
		}
		else
		{
			throw IECore::Exception(
				boost::str(
					boost::format( "Cannot promote plug \"%s\" as it is already promoted." ) % plug->fullName()
				)
			);
		}
	}

	if( plug->direction() == Plug::In )
	{
		if( plug->getFlags( Plug::ReadOnly ) )
		{
			if( !throwExceptions )
			{
				return false;
			}
			else
			{
				throw IECore::Exception(
					boost::str(
						boost::format( "Cannot promote plug \"%s\" as it is read only." ) % plug->fullName()
					)
				);
			}
		}

		// The plug must be serialisable, as we need its input to be saved,
		// but we only need to check this for the topmost plug and not for
		// children, because a setInput() call for a parent plug will also
		// restore child inputs.
		if( !childPlug && !plug->getFlags( Plug::Serialisable ) )
		{
			if( !throwExceptions )
			{
				return false;
			}
			else
			{
				throw IECore::Exception(
					boost::str(
						boost::format( "Cannot promote plug \"%s\" as it is not serialisable." ) % plug->fullName()
					)
				);
			}
		}

		if( !plug->getFlags( Plug::AcceptsInputs ) )
		{
			if( !throwExceptions )
			{
				return false;
			}
			else
			{
				throw IECore::Exception(
					boost::str(
						boost::format( "Cannot promote plug \"%s\" as it does not accept inputs." ) % plug->fullName()
					)
				);
			}
		}

		if( plug->getInput() )
		{
			if( !throwExceptions )
			{
				return false;
			}
			else
			{
				throw IECore::Exception(
					boost::str(
						boost::format( "Cannot promote plug \"%s\" as it already has an input." ) % plug->fullName()
					)
				);
			}
		}
	}

	if( !childPlug )
	{
		const Node *node = externalNode( plug );
		if( !node )
		{
			if( !throwExceptions )
			{
				return false;
			}
			else
			{
				throw IECore::Exception(
					boost::str(
						boost::format( "Cannot promote plug \"%s\" as there is no external node." ) % plug->fullName()
					)
				);
			}
		}

		if( parent && parent->node() != node )
		{
			if( !throwExceptions )
			{
				return false;
			}
			else
			{
				throw IECore::Exception(
					boost::str(
						boost::format( "Cannot promote plug \"%s\" because parent \"%s\" is not a descendant of \"%s\"." ) %
							plug->fullName() % parent % node
					)
				);
			}
		}
	}

	// Check all the children of this plug too
	for( RecursivePlugIterator it( plug ); !it.done(); ++it )
	{
		if( !validatePromotability( it->get(), parent, throwExceptions, /* childPlug = */ true ) )
		{
			return false;
		}
	}

	return true;
}

std::string promotedName( const Plug *plug )
{
	std::string result = plug->relativeName( plug->node() );
	boost::replace_all( result, ".", "_" );
	return result;
}

void applyDynamicFlag( Plug *plug )
{
	plug->setFlags( Plug::Dynamic, true );

	// Flags are not automatically propagated to the children of compound plugs,
	// so we need to do that ourselves. We don't want to propagate them to the
	// children of plug types which create the children themselves during
	// construction though, hence the typeId checks for the base classes
	// which add no children during construction. I'm not sure this approach is
	// necessarily the best - the alternative would be to set everything dynamic
	// unconditionally and then implement Serialiser::childNeedsConstruction()
	// for types like CompoundNumericPlug that create children in their constructors.
	// Or, even better, abolish the Dynamic flag entirely and deal with everything
	// via serialisers.
	const Gaffer::TypeId compoundTypes[] = { PlugTypeId, ValuePlugTypeId, CompoundPlugTypeId, ArrayPlugTypeId };
	const Gaffer::TypeId *compoundTypesEnd = compoundTypes + 4;
	if( find( compoundTypes, compoundTypesEnd, (Gaffer::TypeId)plug->typeId() ) != compoundTypesEnd )
	{
		for( RecursivePlugIterator it( plug ); !it.done(); ++it )
		{
			(*it)->setFlags( Plug::Dynamic, true );
			if( find( compoundTypes, compoundTypesEnd, (Gaffer::TypeId)(*it)->typeId() ) != compoundTypesEnd )
			{
				it.prune();
			}
		}
	}
}

} // namespace

namespace Gaffer
{

namespace PlugAlgo
{

bool canPromote( const Plug *plug, const Plug *parent )
{
	return validatePromotability( plug, parent, /* throwExceptions = */ false );
}

Plug *promote( Plug *plug, Plug *parent, const StringAlgo::MatchPattern &excludeMetadata )
{
	return promoteWithName( plug, promotedName( plug ), parent, excludeMetadata );
}

Plug *promoteWithName( Plug *plug, const InternedString &name, Plug *parent, const StringAlgo::MatchPattern &excludeMetadata )
{
	validatePromotability( plug, parent, /* throwExceptions = */ true );

	PlugPtr externalPlug = plug->createCounterpart( name, plug->direction() );
	if( externalPlug->direction() == Plug::In )
	{
		if( ValuePlug *externalValuePlug = IECore::runTimeCast<ValuePlug>( externalPlug.get() ) )
		{
			externalValuePlug->setFrom( static_cast<ValuePlug *>( plug ) );
		}
	}

	Node *externalNode = ::externalNode( plug );
	const bool dynamic = runTimeCast<Box>( externalNode ) || parent == externalNode->userPlug();
	MetadataAlgo::copy( plug, externalPlug.get(), excludeMetadata, /* persistentOnly = */ true, /* persistent = */ dynamic );
	if( dynamic )
	{
		applyDynamicFlag( externalPlug.get() );
	}

	if( parent )
	{
		parent->addChild( externalPlug );
	}
	else
	{
		externalNode->addChild( externalPlug );
	}

	if( externalPlug->direction() == Plug::In )
	{
		plug->setInput( externalPlug );
	}
	else
	{
		externalPlug->setInput( plug );
	}

	return externalPlug.get();
}

bool isPromoted( const Plug *plug )
{
	if( !plug )
	{
		return false;
	}

	const Node *node = plug->node();
	if( !node )
	{
		return false;
	}

	const Node *enclosingNode = node->parent<Node>();
	if( !enclosingNode )
	{
		return false;
	}

	if( plug->direction() == Plug::In )
	{
		const Plug *input = plug->getInput();
		return input && input->node() == enclosingNode;
	}
	else
	{
		for( Plug::OutputContainer::const_iterator it = plug->outputs().begin(), eIt = plug->outputs().end(); it != eIt; ++it )
		{
			if( (*it)->node() == enclosingNode )
			{
				return true;
			}
		}
		return false;
	}
}

void unpromote( Plug *plug )
{
	if( !isPromoted( plug ) )
	{
		if( plug )
		{
			throw IECore::Exception(
				boost::str(
					boost::format( "Cannot unpromote plug \"%s\" as it has not been promoted." ) % plug->fullName()
				)
			);
		}
		else
		{
			throw IECore::Exception( "Cannot unpromote null plug" );
		}
	}

	Node *externalNode = ::externalNode( plug );
	Plug *externalPlug = nullptr;
	if( plug->direction() == Plug::In )
	{
		externalPlug = plug->getInput();
		plug->setInput( nullptr );
	}
	else
	{
		for( Plug::OutputContainer::const_iterator it = plug->outputs().begin(), eIt = plug->outputs().end(); it != eIt; ++it )
		{
			if( (*it)->node() == externalNode )
			{
				externalPlug = *it;
				break;
			}
		}
		assert( externalPlug ); // should be true because we checked isPromoted()
		externalPlug->setInput( nullptr );
	}

	// Remove the top level external plug , but only if
	// all the children are unused too in the case of a compound plug.
	bool remove = true;
	Plug *plugToRemove = externalPlug;
	while( plugToRemove->parent<Plug>() && plugToRemove->parent<Plug>() != externalNode->userPlug() )
	{
		plugToRemove = plugToRemove->parent<Plug>();
		for( PlugIterator it( plugToRemove ); !it.done(); ++it )
		{
			if(
				( (*it)->direction() == Plug::In && (*it)->outputs().size() ) ||
				( (*it)->direction() == Plug::Out && (*it)->getInput() )
			)
			{
				remove = false;
				break;
			}
		}
	}
	if( remove )
	{
		plugToRemove->parent()->removeChild( plugToRemove );
	}
}

} // namespace PlugAlgo

} // namespace Gaffer
