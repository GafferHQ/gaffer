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

#include "boost/algorithm/string/find.hpp"

#include "IECore/SimpleTypedData.h"

#include "Gaffer/ScriptNode.h"

#include "GafferUI/NodeGadget.h"
#include "GafferUI/NameGadget.h"
#include "GafferUI/Style.h"
#include "GafferUI/LinearContainer.h"
#include "GafferUI/Nodule.h"
#include "GafferUI/Metadata.h"

using namespace GafferUI;
using namespace Imath;
using namespace IECore;
using namespace std;
using namespace boost;

IE_CORE_DEFINERUNTIMETYPED( NodeGadget );

NodeGadget::NodeGadget( Gaffer::NodePtr node )
	:	m_node( node.get() )
{
}

NodeGadget::~NodeGadget()
{
}

NodeGadgetPtr NodeGadget::create( Gaffer::NodePtr node )
{
	const CreatorMap &cr = creators();
	CreatorMap::const_iterator it = cr.find( node->typeId() );
	if( it==cr.end() )
	{
		const std::vector<IECore::TypeId> &baseTypes = IECore::RunTimeTyped::baseTypeIds( node->typeId() );
		for( std::vector<IECore::TypeId>::const_iterator tIt=baseTypes.begin(); tIt!=baseTypes.end(); tIt++ )
		{
			if( ( it = cr.find( *tIt ) )!=cr.end() )
			{
				break;
			}
		}
	}
	
	return it->second( node );
}

void NodeGadget::registerNodeGadget( IECore::TypeId nodeType, NodeGadgetCreator creator )
{
	creators()[nodeType] = creator;
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
	return 0;
}

const Nodule *NodeGadget::nodule( const Gaffer::Plug *plug ) const
{
	return 0;
}

Imath::V3f NodeGadget::noduleTangent( const Nodule *nodule ) const
{
	return V3f( 0, 1, 0 );
}

NodeGadget::CreatorMap &NodeGadget::creators()
{
	static CreatorMap c;
	return c;
}

std::string NodeGadget::getToolTip( const IECore::LineSegment3f &line ) const
{
	std::string result = IndividualContainer::getToolTip( line );
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
	
	result = "<h3>" + title + "</h3>";
	
	std::string description = Metadata::nodeDescription( m_node );
	if( description.size() )
	{
		result += "\n\n" + description;
	}
	
	if( ConstStringDataPtr summary = Metadata::nodeValue<StringData>( m_node, "summary" ) )
	{
		result += "\n\n" + summary->readable();
	}
	
	return result;
}
