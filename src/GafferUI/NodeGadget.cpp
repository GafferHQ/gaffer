//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2011, John Haddon. All rights reserved.
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
#include "GafferUI/NameGadget.h"
#include "GafferUI/Style.h"
#include "GafferUI/LinearContainer.h"
#include "GafferUI/Nodule.h"

#include "Gaffer/ScriptNode.h"

#include "IECore/SimpleTypedData.h"

#include "boost/bind.hpp"

using namespace GafferUI;
using namespace Imath;
using namespace IECore;
using namespace std;
using namespace boost;

IE_CORE_DEFINERUNTIMETYPED( NodeGadget );

NodeGadget::CreatorMap NodeGadget::g_creators;

NodeGadget::NodeGadget( Gaffer::NodePtr node )
	:	m_node( node.get() )
{
}

NodeGadget::~NodeGadget()
{
}

NodeGadgetPtr NodeGadget::create( Gaffer::NodePtr node )
{
	CreatorMap::const_iterator it = g_creators.find( node->typeId() );
	if( it==g_creators.end() )
	{
		const std::vector<IECore::TypeId> &baseTypes = IECore::RunTimeTyped::baseTypeIds( node->typeId() );
		for( std::vector<IECore::TypeId>::const_iterator tIt=baseTypes.begin(); tIt!=baseTypes.end(); tIt++ )
		{
			if( ( it = g_creators.find( *tIt ) )!=g_creators.end() )
			{
				break;
			}
		}
	}
	
	return it->second( node );
}

void NodeGadget::registerNodeGadget( IECore::TypeId nodeType, NodeGadgetCreator creator )
{
	g_creators[nodeType] = creator;
}

Gaffer::NodePtr NodeGadget::node()
{
	return m_node;
}

Gaffer::ConstNodePtr NodeGadget::node() const
{
	return m_node;
}

NodulePtr NodeGadget::nodule( Gaffer::ConstPlugPtr plug )
{
	return 0;
}

ConstNodulePtr NodeGadget::nodule( Gaffer::ConstPlugPtr plug ) const
{
	return 0;
}
