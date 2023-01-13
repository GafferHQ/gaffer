//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2022, Image Engine Design Inc. All rights reserved.
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

#include "GafferImage/FormatQuery.h"

#include "OpenEXR/OpenEXRConfig.h"
#if OPENEXR_VERSION_MAJOR < 3
#include "OpenEXR/ImathBoxAlgo.h"
#else
#include "Imath/ImathBoxAlgo.h"
#endif

#include <cassert>

namespace
{

template <typename T>
void
setV2PlugComponentValue( T const& parent, Gaffer::NumericPlug< typename T::ValueType::BaseType >& child, typename T::ValueType const& value )
{
	float cv;

	if( & child == parent.getChild( 0 ) )
	{
		cv = value.x;
	}
	else if( & child == parent.getChild( 1 ) )
	{
		cv = value.y;
	}
	else
	{
		assert( 0 ); // NOTE : Unknown child plug
		cv = 0.f;
	}

	child.setValue( cv );

}

} // namespace

namespace GafferImage
{

size_t FormatQuery::g_firstPlugIndex = 0;

GAFFER_NODE_DEFINE_TYPE( FormatQuery );

FormatQuery::FormatQuery( std::string const& name )
: Gaffer::ComputeNode( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new ImagePlug( "image" ) );
	addChild( new Gaffer::StringPlug( "view", Gaffer::Plug::In, "" ) );
	addChild( new GafferImage::FormatPlug( "format", Gaffer::Plug::Out ) );
	addChild( new Gaffer::V2fPlug( "center", Gaffer::Plug::Out ) );
	addChild( new Gaffer::V2iPlug( "size", Gaffer::Plug::Out ) );
}

FormatQuery::~FormatQuery()
{}

ImagePlug* FormatQuery::imagePlug()
{
	return const_cast< ImagePlug* >(
		static_cast< FormatQuery const* >( this )->imagePlug() );
}

ImagePlug const* FormatQuery::imagePlug() const
{
	return getChild< ImagePlug >( g_firstPlugIndex );
}

Gaffer::StringPlug* FormatQuery::viewPlug()
{
	return const_cast< Gaffer::StringPlug* >( static_cast< FormatQuery const* >( this )->viewPlug() );
}

Gaffer::StringPlug const* FormatQuery::viewPlug() const
{
	return getChild< Gaffer::StringPlug >( g_firstPlugIndex + 1 );
}

FormatPlug* FormatQuery::formatPlug()
{
	return const_cast< FormatPlug* >( static_cast< FormatQuery const* >( this )->formatPlug() );
}

FormatPlug const* FormatQuery::formatPlug() const
{
	return getChild< FormatPlug >( g_firstPlugIndex + 2 );
}

Gaffer::V2fPlug* FormatQuery::centerPlug()
{
	return const_cast< Gaffer::V2fPlug* >(
		static_cast< FormatQuery const* >( this )->centerPlug() );
}

Gaffer::V2fPlug const* FormatQuery::centerPlug() const
{
	return getChild< Gaffer::V2fPlug >( g_firstPlugIndex + 3 );
}

Gaffer::V2iPlug* FormatQuery::sizePlug()
{
	return const_cast< Gaffer::V2iPlug* >(
		static_cast< FormatQuery const* >( this )->sizePlug() );
}

Gaffer::V2iPlug const* FormatQuery::sizePlug() const
{
	return getChild< Gaffer::V2iPlug >( g_firstPlugIndex + 4 );
}

void FormatQuery::affects( Gaffer::Plug const* const input, AffectedPlugsContainer& outputs ) const
{
	ComputeNode::affects( input, outputs );

	if( input == imagePlug()->formatPlug() || input == imagePlug()->viewNamesPlug() || input == viewPlug() )
	{
		outputs.push_back( formatPlug()->displayWindowPlug()->minPlug()->getChild( 0 ) );
		outputs.push_back( formatPlug()->displayWindowPlug()->minPlug()->getChild( 1 ) );
		outputs.push_back( formatPlug()->displayWindowPlug()->maxPlug()->getChild( 0 ) );
		outputs.push_back( formatPlug()->displayWindowPlug()->maxPlug()->getChild( 1 ) );
		outputs.push_back( formatPlug()->pixelAspectPlug() );
		outputs.push_back( centerPlug()->getChild( 0 ) );
		outputs.push_back( centerPlug()->getChild( 1 ) );
		outputs.push_back( sizePlug()->getChild( 0 ) );
		outputs.push_back( sizePlug()->getChild( 1 ) );
	}
}

void FormatQuery::hash( Gaffer::ValuePlug const* const output, Gaffer::Context const* const context, IECore::MurmurHash& h ) const
{
	ComputeNode::hash( output, context, h );

	std::string view = viewPlug()->getValue();
	if( !view.size() )
	{
		view = context->get<std::string>( ImagePlug::viewNameContextName, ImagePlug::defaultViewName );
	}

	ImagePlug::ViewScope viewScope( context );
	viewScope.setViewNameChecked( &view, imagePlug()->viewNames().get() );
	h.append( imagePlug()->formatHash() );

}

void FormatQuery::compute( Gaffer::ValuePlug* const output, Gaffer::Context const* const context ) const
{
	Gaffer::GraphComponent* const parent = output->parent();

	std::string view = viewPlug()->getValue();
	if( !view.size() )
	{
		view = context->get<std::string>( ImagePlug::viewNameContextName, ImagePlug::defaultViewName );
	}

	ImagePlug::ViewScope viewScope( context );
	viewScope.setViewNameChecked( &view, imagePlug()->viewNames().get() );
	Format f = imagePlug()->format();

	if( output == formatPlug()->pixelAspectPlug() )
	{
		static_cast< Gaffer::FloatPlug *>( output )->setValue( f.getPixelAspect() );
	}
	else if( parent == formatPlug()->displayWindowPlug()->minPlug() )
	{
		setV2PlugComponentValue(
			*( IECore::assertedStaticCast< Gaffer::V2iPlug >( parent ) ),
			*( IECore::assertedStaticCast< Gaffer::IntPlug >( output ) ), f.getDisplayWindow().min );
	}
	else if( parent == formatPlug()->displayWindowPlug()->maxPlug() )
	{
		setV2PlugComponentValue(
			*( IECore::assertedStaticCast< Gaffer::V2iPlug >( parent ) ),
			*( IECore::assertedStaticCast< Gaffer::IntPlug >( output ) ), f.getDisplayWindow().max );
	}
	else if( parent == centerPlug() )
	{
		// If the size is odd, then the center will be aligned to a half pixel, so we use float for the center
		Imath::Box2f floatBound( f.getDisplayWindow().min, f.getDisplayWindow().max );
		setV2PlugComponentValue(
			*( IECore::assertedStaticCast< Gaffer::V2fPlug >( parent ) ),
			*( IECore::assertedStaticCast< Gaffer::FloatPlug >( output ) ), floatBound.center() );
	}
	else if( parent == sizePlug() )
	{
		setV2PlugComponentValue(
			*( IECore::assertedStaticCast< Gaffer::V2iPlug >( parent ) ),
			*( IECore::assertedStaticCast< Gaffer::IntPlug >( output ) ), Imath::V2i( f.width(), f.height() ) );
	}
	else
	{
		ComputeNode::compute( output, context );
	}
}

} // GafferImage
