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

#include "GafferUI/NodeGadget.h"

#include "GafferUI/LinearContainer.h"
#include "GafferUI/NameGadget.h"
#include "GafferUI/Nodule.h"
#include "GafferUI/Style.h"

#include "Gaffer/Metadata.h"
#include "Gaffer/ScriptNode.h"

#include "IECore/SimpleTypedData.h"

#include "boost/algorithm/string/find.hpp"

using namespace GafferUI;
using namespace Imath;
using namespace IECore;
using namespace std;
using namespace boost;

//////////////////////////////////////////////////////////////////////////
// Factory internals
//////////////////////////////////////////////////////////////////////////

namespace
{

typedef std::map<std::string, NodeGadget::NodeGadgetCreator> TypeCreatorMap;
TypeCreatorMap &typeCreators()
{
	// We tactically "leak" this map. NodeGadgetCreators are
	// registered from Python, meaning we hold python objects in the TypeCreatorMap.
	// Python completes shutdown before static destructors are run, and trying
	// to destroy a Python object after Python shutdown can lead to crashes.
	static auto c = new TypeCreatorMap;
	return *c;
}

typedef std::map<IECore::TypeId, NodeGadget::NodeGadgetCreator> NodeCreatorMap;
NodeCreatorMap &nodeCreators()
{
	// See `typeCreators()` for note on "leak".
	static auto c = new NodeCreatorMap;
	return *c;
}

} // namespace

//////////////////////////////////////////////////////////////////////////
// NodeGadget
//////////////////////////////////////////////////////////////////////////

GAFFER_GRAPHCOMPONENT_DEFINE_TYPE( NodeGadget );

NodeGadget::NodeGadget( Gaffer::NodePtr node )
	:	m_node( node.get() )
{
}

NodeGadget::~NodeGadget()
{
}

NodeGadgetPtr NodeGadget::create( Gaffer::NodePtr node )
{
	IECore::ConstStringDataPtr nodeGadgetType = Gaffer::Metadata::value<IECore::StringData>( node.get(), "nodeGadget:type" );
	if( nodeGadgetType )
	{
		if( nodeGadgetType->readable() == "" )
		{
			return nullptr;
		}
		const TypeCreatorMap &m = typeCreators();
		TypeCreatorMap::const_iterator it = m.find( nodeGadgetType->readable() );
		if( it != m.end() )
		{
			return it->second( node );
		}
		else
		{
			IECore::msg( IECore::Msg::Warning, "NodeGadget::create", boost::format( "Nonexistent type \"%s\" requested for node \"%s\"" ) % nodeGadgetType->readable() % node->fullName() );
		}
	}

	const NodeCreatorMap &cr = nodeCreators();

	IECore::TypeId typeId = node->typeId();
	while( typeId != IECore::InvalidTypeId )
	{
		const NodeCreatorMap::const_iterator it = cr.find( typeId );
		if( it != cr.end() )
		{
			return it->second( node );
		}
		typeId = IECore::RunTimeTyped::baseTypeId( typeId );
	}

	return nullptr;
}

void NodeGadget::registerNodeGadget( const std::string &nodeGadgetType, NodeGadgetCreator creator, IECore::TypeId nodeType )
{
	typeCreators()[nodeGadgetType] = creator;
	if( nodeType != IECore::InvalidTypeId )
	{
		nodeCreators()[nodeType] = creator;
	}
}

void NodeGadget::registerNodeGadget( IECore::TypeId nodeType, NodeGadgetCreator creator )
{
	nodeCreators()[nodeType] = creator;
}

Gaffer::Node *NodeGadget::node()
{
	return m_node;
}

const Gaffer::Node *NodeGadget::node() const
{
	return m_node;
}

Nodule *NodeGadget::nodule( const Gaffer::Plug *plug )
{
	return nullptr;
}

const Nodule *NodeGadget::nodule( const Gaffer::Plug *plug ) const
{
	return nullptr;
}

Imath::V3f NodeGadget::connectionTangent( const ConnectionCreator *creator ) const
{
	return V3f( 0, 1, 0 );
}

NodeGadget::NoduleSignal &NodeGadget::noduleAddedSignal()
{
	return m_noduleAddedSignal;
}

NodeGadget::NoduleSignal &NodeGadget::noduleRemovedSignal()
{
	return m_noduleRemovedSignal;
}

std::string NodeGadget::getToolTip( const IECore::LineSegment3f &line ) const
{
	std::string result = Gadget::getToolTip( line );
	if( result.size() )
	{
		return result;
	}

	std::string title = m_node->typeName();
	boost::iterator_range<string::const_iterator> r = boost::find_last( title, ":" );
	if( r )
	{
		title = &*(r.end());
	}

	result = "# " + title;

	if( ConstStringDataPtr description = Gaffer::Metadata::value<StringData>( m_node, "description" ) )
	{
		result += "\n\n" + description->readable();
	}

	if( ConstStringDataPtr summary = Gaffer::Metadata::value<StringData>( m_node, "summary" ) )
	{
		result += "\n\n" + summary->readable();
	}

	return result;
}
