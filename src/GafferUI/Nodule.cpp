//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2011-2012, John Haddon. All rights reserved.
//  Copyright (c) 2011, Image Engine Design Inc. All rights reserved.
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

#include "GafferUI/Nodule.h"

#include "Gaffer/Metadata.h"
#include "Gaffer/Node.h"
#include "Gaffer/Plug.h"

#include "IECore/SimpleTypedData.h"

#include "fmt/format.h"

using namespace GafferUI;
using namespace IECore;
using namespace Imath;
using namespace std;

GAFFER_GRAPHCOMPONENT_DEFINE_TYPE( Nodule );

Nodule::Nodule( Gaffer::PlugPtr plug )
	:	ConnectionCreator( defaultName<Nodule>() ), m_plug( plug )
{
}

Nodule::~Nodule()
{
}

Gaffer::Plug *Nodule::plug()
{
	return m_plug.get();
}

const Gaffer::Plug *Nodule::plug() const
{
	return m_plug.get();
}

Nodule *Nodule::nodule( const Gaffer::Plug *plug )
{
	return nullptr;
}

const Nodule *Nodule::nodule( const Gaffer::Plug *plug ) const
{
	return nullptr;
}

void Nodule::updateDragEndPoint( const Imath::V3f position, const Imath::V3f &tangent )
{
}

Nodule::TypeNameCreatorMap &Nodule::typeNameCreators()
{
	static TypeNameCreatorMap m;
	return m;
}

Nodule::PlugCreatorMap &Nodule::plugCreators()
{
	static PlugCreatorMap m;
	return m;
}

NodulePtr Nodule::create( Gaffer::PlugPtr plug )
{
	IECore::ConstStringDataPtr noduleType = Gaffer::Metadata::value<IECore::StringData>( plug.get(), "nodule:type" );
	if( noduleType )
	{
		if( noduleType->readable() == "" )
		{
			return nullptr;
		}
		const TypeNameCreatorMap &m = typeNameCreators();
		TypeNameCreatorMap::const_iterator it = m.find( noduleType->readable() );
		if( it != m.end() )
		{
			return it->second( plug );
		}
		else
		{
			IECore::msg( IECore::Msg::Warning, "Nodule::create", fmt::format( "Nonexistent nodule type \"{}\" requested for plug \"{}\"", noduleType->readable(), plug->fullName() ) );
		}
	}

	const PlugCreatorMap &m = plugCreators();
	IECore::TypeId t = plug->typeId();
	while( t!=IECore::InvalidTypeId )
	{
		PlugCreatorMap::const_iterator it = m.find( t );
		if( it!=m.end() )
		{
			return it->second( plug );
		}
		t = IECore::RunTimeTyped::baseTypeId( t );
	}

	return nullptr;
}

void Nodule::registerNodule( const std::string &noduleTypeName, NoduleCreator creator, IECore::TypeId plugType )
{
	typeNameCreators()[noduleTypeName] = creator;
	if( plugType != IECore::InvalidTypeId )
	{
		plugCreators()[plugType] = creator;
	}
}

std::string Nodule::getToolTip( const IECore::LineSegment3f &line ) const
{
	std::string result = Gadget::getToolTip( line );
	if( result.size() )
	{
		return result;
	}

	result = m_plug->fullName();
	if( const Gaffer::Node *node = m_plug->node() )
	{
		result = m_plug->relativeName( node->parent<Gaffer::GraphComponent>() );
	}

	result = "# " + result;
	if( ConstStringDataPtr description = Gaffer::Metadata::value<StringData>( m_plug.get(), "description" ) )
	{
		result += "\n\n" + description->readable();
	}

	return result;
}
