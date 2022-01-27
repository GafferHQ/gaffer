//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2018, Image Engine Design Inc. All rights reserved.
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

#include "GafferUI/CompoundNumericNodule.h"

#include "GafferUI/NoduleLayout.h"
#include "GafferUI/PlugAdder.h"

#include "Gaffer/CompoundNumericPlug.h"
#include "Gaffer/Metadata.h"
#include "Gaffer/MetadataAlgo.h"

#include "boost/bind/bind.hpp"
#include "boost/bind/placeholders.hpp"

using namespace std;
using namespace boost::placeholders;
using namespace Imath;
using namespace IECore;
using namespace Gaffer;
using namespace GafferUI;

//////////////////////////////////////////////////////////////////////////
// Internal utilities
//////////////////////////////////////////////////////////////////////////

namespace
{

InternedString g_childrenVisibleKey( "compoundNumericNodule:childrenVisible" );

bool canConnect( const Plug *p1, const Plug *p2 )
{
	if( p1->direction() == p2->direction() || p1->node() == p2->node() )
	{
		return false;
	}
	if( p1->direction() == Plug::In )
	{
		return p1->acceptsInput( p2 );
	}
	else
	{
		return p2->acceptsInput( p1 );
	}
}

void connect( Plug *p1, Plug *p2 )
{
	if( p1->direction() == Plug::In )
	{
		p1->setInput( p2 );
	}
	else
	{
		p2->setInput( p1 );
	}
}

bool canConnectAllSourceComponents( const Plug *source, const Plug *destination )
{
	if( source->direction() != Plug::Out || destination->direction() != Plug::In )
	{
		return false;
	}

	if( !source->children().size() || destination->children().size() <= source->children().size() )
	{
		return false;
	}

	for( size_t i = 0; i < source->children().size(); ++i )
	{
		if( !canConnect( source->getChild<Plug>( i ), destination->getChild<Plug>( i ) ) )
		{
			return false;
		}
	}

	return true;
}

void connectAllSourceComponents( Plug *source, Plug *destination )
{
	for( size_t i = 0; i < source->children().size(); ++i )
	{
		connect( source->getChild<Plug>( i ), destination->getChild<Plug>( i ) );
	}
}

IECore::TypeId g_compoundNumericTypeIds[] = {
	V2fPlug::staticTypeId(), V3fPlug::staticTypeId(),
	V2iPlug::staticTypeId(), V3iPlug::staticTypeId(),
	Color3fPlug::staticTypeId(), Color4fPlug::staticTypeId()
};

struct TypeDescription
{
	TypeDescription()
	{
		for( auto t : g_compoundNumericTypeIds )
		{
			Nodule::registerNodule(
				CompoundNumericNodule::staticTypeName(),
				[]( PlugPtr p ) { return new CompoundNumericNodule( p ); },
				t
			);
		}
	}
};

static TypeDescription g_typeDescription;

} // namespace

//////////////////////////////////////////////////////////////////////////
// CompoundNumericNodule
//////////////////////////////////////////////////////////////////////////

GAFFER_GRAPHCOMPONENT_DEFINE_TYPE( CompoundNumericNodule );

CompoundNumericNodule::CompoundNumericNodule( Gaffer::PlugPtr plug )
	:	StandardNodule( plug )
{
	Metadata::plugValueChangedSignal( plug->node() ).connect( boost::bind( &CompoundNumericNodule::plugMetadataChanged, this, ::_1, ::_2 ) );
	updateChildNoduleVisibility();
}

CompoundNumericNodule::~CompoundNumericNodule()
{
}

Nodule *CompoundNumericNodule::nodule( const Gaffer::Plug *plug )
{
	if( plug->parent() == this->plug() )
	{
		if( NoduleLayout *l = noduleLayout() )
		{
			return l->nodule( plug );
		}
	}
	return nullptr;
}

const Nodule *CompoundNumericNodule::nodule( const Gaffer::Plug *plug ) const
{
	if( plug->parent() == this->plug() )
	{
		if( const NoduleLayout *l = noduleLayout() )
		{
			return l->nodule( plug );
		}
	}
	return nullptr;
}

bool CompoundNumericNodule::canCreateConnection( const Gaffer::Plug *endpoint ) const
{
	if( StandardNodule::canCreateConnection( endpoint ) )
	{
		return true;
	}

	if( noduleLayout() )
	{
		return false;
	}

	// Things like Color3f -> Color4f
	if( canConnectAllSourceComponents( endpoint, plug() ) )
	{
		return true;
	}

	// Things like float <-> Color3f.[rgb]
	for( Plug::Iterator it( plug() ); !it.done(); ++it )
	{
		if( canConnect( endpoint, it->get() ) )
		{
			return true;
		}
	}
	return false;
}

void CompoundNumericNodule::createConnection( Gaffer::Plug *endpoint )
{
	if( StandardNodule::canCreateConnection( endpoint ) )
	{
		StandardNodule::createConnection( endpoint );
		return;
	}

	// Things like Color3f -> Color4f

	if( canConnectAllSourceComponents( endpoint, plug() ) )
	{
		connectAllSourceComponents( endpoint, plug() );
		Gaffer::Metadata::registerValue( plug(), g_childrenVisibleKey, new BoolData( true ) );
		return;
	}

	// Things like float <-> Color3f.[rgb]

	vector<Plug *> plugs;
	string allName;
	for( Plug::Iterator it( plug() ); !it.done(); ++it )
	{
		if( canConnect( endpoint, it->get() ) )
		{
			plugs.push_back( it->get() );
			allName += (*it)->getName();
		}
	}

	PlugPtr allProxy;
	if( allName.size() && plug()->direction() == Plug::In )
	{
		allProxy = new Plug( allName );
		plugs.push_back( allProxy.get() );
	}

	Plug *p = PlugAdder::plugMenuSignal()( "Connect To", plugs );
	if( p )
	{
		if( p == allProxy )
		{
			for( const auto &p : plugs )
			{
				connect( p, endpoint );
			}
		}
		else
		{
			connect( p, endpoint );
		}

		Gaffer::Metadata::registerValue( plug(), g_childrenVisibleKey, new BoolData( true ) );
	}
}

Imath::Box3f CompoundNumericNodule::bound() const
{
	if( !noduleLayout() )
	{
		return StandardNodule::bound();
	}
	else
	{
		const V3f border( 0.1, 0.1, 0 );
		Box3f b = Nodule::bound();
		b.min -= border;
		b.max += border;
		return b;
	}
}

void CompoundNumericNodule::renderLayer( Layer layer, const Style *style, RenderReason reason ) const
{
	if( !noduleLayout() )
	{
		StandardNodule::renderLayer( layer, style, reason );
	}
}

unsigned CompoundNumericNodule::layerMask() const
{
	if( !noduleLayout() )
	{
		return StandardNodule::layerMask();
	}
	else
	{
		return 0;
	}
}

Imath::Box3f CompoundNumericNodule::renderBound() const
{
	if( !noduleLayout() )
	{
		return StandardNodule::renderBound();
	}
	else
	{
		return Box3f();
	}
}

NoduleLayout *CompoundNumericNodule::noduleLayout()
{
	return children().size() ? getChild<NoduleLayout>( 0 ) : nullptr;
}

const NoduleLayout *CompoundNumericNodule::noduleLayout() const
{
	return children().size() ? getChild<NoduleLayout>( 0 ) : nullptr;
}

void CompoundNumericNodule::plugMetadataChanged( const Gaffer::Plug *plug, IECore::InternedString key )
{
	if( plug != this->plug() )
	{
		return;
	}

	if( key == g_childrenVisibleKey )
	{
		updateChildNoduleVisibility();
	}
}

void CompoundNumericNodule::updateChildNoduleVisibility()
{
	bool childrenVisible = false;
	if( ConstBoolDataPtr d = Metadata::value<BoolData>( plug(), g_childrenVisibleKey ) )
	{
		childrenVisible = d->readable();
	}

	if( childrenVisible )
	{
		if( !noduleLayout() )
		{
			NoduleLayoutPtr layout = new NoduleLayout( plug() );
			layout->setTransform( M44f().scale( V3f( 0.75 ) ) );
			addChild( layout );
			if( NodeGadget *nodeGadget = ancestor<NodeGadget>() )
			{
				for( Plug::Iterator it( plug() ); !it.done(); ++it )
				{
					if( Nodule *nodule = layout->nodule( it->get() ) )
					{
						nodeGadget->noduleAddedSignal()( nodeGadget, nodule );
					}
				}
			}
		}
	}
	else
	{
		if( NoduleLayoutPtr layout = noduleLayout() )
		{
			removeChild( layout );
			if( NodeGadget *nodeGadget = ancestor<NodeGadget>() )
			{
				for( Plug::Iterator it( plug() ); !it.done(); ++it )
				{
					if( Nodule *nodule = layout->nodule( it->get() ) )
					{
						nodeGadget->noduleRemovedSignal()( nodeGadget, nodule );
					}
				}
			}
		}
	}
}
