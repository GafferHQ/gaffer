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

#include "Gaffer/ValuePlug.h"
#include "Gaffer/PlugAlgo.h"

using namespace std;
using namespace IECore;
using namespace Gaffer;

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
		c.input = existingPlug->getInput<Plug>();
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
