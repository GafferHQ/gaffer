//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2014, John Haddon. All rights reserved.
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

#include "GafferUI/Tool.h"

#include "GafferUI/View.h"

#include "boost/bind.hpp"

using namespace Gaffer;
using namespace GafferUI;

GAFFER_NODE_DEFINE_TYPE( Tool );

size_t Tool::g_firstPlugIndex = 0;

Tool::Tool( View *view, const std::string &name )
	:	Node( name ), m_view( view )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new BoolPlug( "active", Plug::In, false ) );
}

Tool::~Tool()
{
}

Gaffer::BoolPlug *Tool::activePlug()
{
	return getChild<BoolPlug>( g_firstPlugIndex );
}

const Gaffer::BoolPlug *Tool::activePlug() const
{
	return getChild<BoolPlug>( g_firstPlugIndex );
}

View *Tool::view()
{
	return m_view;
}

const View *Tool::view() const
{
	return m_view;
}

//////////////////////////////////////////////////////////////////////////
// Factory
//////////////////////////////////////////////////////////////////////////

namespace
{

typedef std::map<std::string, Tool::ToolCreator> NamedCreators;
typedef std::map<IECore::TypeId, NamedCreators> PerViewCreators;

NamedCreators &namedCreators( IECore::TypeId viewType )
{
	static PerViewCreators m;
	return m[viewType];
}

} // namespace

ToolPtr Tool::create( const std::string &toolName, View *view )
{
	IECore::TypeId typeId = view->typeId();
	do
	{
		const NamedCreators &creators = namedCreators( typeId );
		NamedCreators::const_iterator it = creators.find( toolName );
		if( it != creators.end() )
		{
			return it->second( view );
		}
		typeId = IECore::RunTimeTyped::baseTypeId( typeId );
	} while( typeId != (IECore::TypeId)NodeTypeId && typeId != IECore::InvalidTypeId );

	return nullptr;
}

void Tool::registerTool( const std::string &toolName, IECore::TypeId viewType, ToolCreator creator )
{
	namedCreators( viewType )[toolName] = creator;
}

void Tool::registeredTools( IECore::TypeId viewType, std::vector<std::string> &toolNames )
{
	do
	{
		const NamedCreators &creators = namedCreators( viewType );
		for( NamedCreators::const_iterator it = creators.begin(), eIt = creators.end(); it != eIt; ++it )
		{
			toolNames.push_back( it->first );
		}
		viewType = IECore::RunTimeTyped::baseTypeId( viewType );
	} while( viewType != (IECore::TypeId)NodeTypeId && viewType != IECore::InvalidTypeId );
}
