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

#include "boost/python.hpp"

#include "GafferBindings/NodeBinding.h"

#include "GafferBindings/MetadataBinding.h"

#include "Gaffer/Plug.h"

using namespace boost::python;
using namespace IECorePython;
using namespace Gaffer;
using namespace GafferBindings;

void NodeSerialiser::moduleDependencies( const Gaffer::GraphComponent *graphComponent, std::set<std::string> &modules, const Serialisation &serialisation ) const
{
	Serialiser::moduleDependencies( graphComponent, modules, serialisation );
}

std::string NodeSerialiser::postHierarchy( const Gaffer::GraphComponent *graphComponent, const std::string &identifier, Serialisation &serialisation ) const
{
	return Serialiser::postHierarchy( graphComponent, identifier, serialisation ) +
		metadataSerialisation( static_cast<const Gaffer::Node *>( graphComponent ), identifier, serialisation );
}

bool NodeSerialiser::childNeedsSerialisation( const Gaffer::GraphComponent *child, const Serialisation &serialisation ) const
{
	if( const Plug *childPlug = IECore::runTimeCast<const Plug>( child ) )
	{
		return childPlug->getFlags( Plug::Serialisable );
	}
	else
	{
		assert( child->isInstanceOf( Node::staticTypeId() ) );
		// Typically we expect internal nodes to be part of the private
		// implementation of the parent node, and to be created explicitly
		// in the parent constructor. Therefore we don't expect them to
		// need serialisation. But, if the root of the serialisation is
		// the node itself, it won't be included, so we must serialise the
		// children explicitly. This is most useful to allow nodes to be
		// cut + pasted out of Reference nodes, but implementing it here
		// makes it possible to inspect the internals of other nodes too.
		return serialisation.parent() == child->parent();
	}
}

bool NodeSerialiser::childNeedsConstruction( const Gaffer::GraphComponent *child, const Serialisation &serialisation ) const
{
	if( const Plug *childPlug = IECore::runTimeCast<const Plug>( child ) )
	{
		return childPlug->getFlags( Plug::Dynamic );
	}
	else
	{
		assert( child->isInstanceOf( Node::staticTypeId() ) );
		return true;
	}
}
