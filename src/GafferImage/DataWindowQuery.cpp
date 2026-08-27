//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2025, Cinesite VFX Inc. All rights reserved.
//
//  Redistribution and use in source and binary forms, with or without
//  modification, are permitted provided that the following conditions are
//  met:
//
//	  * Redistributions of source code must retain the above
//		copyright notice, this list of conditions and the following
//		disclaimer.
//
//	  * Redistributions in binary form must reproduce the above
//		copyright notice, this list of conditions and the following
//		disclaimer in the documentation and/or other materials provided with
//		the distribution.
//
//	  * Neither the name of John Haddon nor the names of
//		any other contributors to this software may be used to endorse or
//		promote products derived from this software without specific prior
//		written permission.
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

#include "GafferImage/DataWindowQuery.h"

using namespace Imath;
using namespace IECore;
using namespace Gaffer;
using namespace GafferImage;

GAFFER_NODE_DEFINE_TYPE( DataWindowQuery );

size_t DataWindowQuery::g_firstPlugIndex = 0;

DataWindowQuery::DataWindowQuery( const std::string &name ) : ComputeNode( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );

	addChild( new ImagePlug( "in" ) );
	addChild( new StringPlug( "view" ) );
	addChild( new Box2iPlug( "dataWindow", Plug::Direction::Out ) );
	addChild( new V2fPlug( "center", Plug::Direction::Out ) );
	addChild( new V2iPlug( "size", Plug::Direction::Out ) );
}

DataWindowQuery::~DataWindowQuery()
{
}

ImagePlug *DataWindowQuery::inPlug()
{
	return getChild<ImagePlug>( g_firstPlugIndex );
}

const ImagePlug *DataWindowQuery::inPlug() const
{
	return getChild<ImagePlug>( g_firstPlugIndex );
}

StringPlug *DataWindowQuery::viewPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

const StringPlug *DataWindowQuery::viewPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

Box2iPlug *DataWindowQuery::dataWindowPlug()
{
	return getChild<Box2iPlug>( g_firstPlugIndex + 2 );
}

const Box2iPlug *DataWindowQuery::dataWindowPlug() const
{
	return getChild<Box2iPlug>( g_firstPlugIndex + 2 );
}

V2fPlug *DataWindowQuery::centerPlug()
{
	return getChild<V2fPlug>( g_firstPlugIndex + 3 );
}

const V2fPlug *DataWindowQuery::centerPlug() const
{
	return getChild<V2fPlug>( g_firstPlugIndex + 3 );
}

V2iPlug *DataWindowQuery::sizePlug()
{
	return getChild<V2iPlug>( g_firstPlugIndex + 4 );
}

const V2iPlug *DataWindowQuery::sizePlug() const
{
	return getChild<V2iPlug>( g_firstPlugIndex + 4 );
}

void DataWindowQuery::affects( const Plug *input, AffectedPlugsContainer &outputs ) const
{
	ComputeNode::affects( input, outputs );
	if(
		input == viewPlug() ||
		input == inPlug()->viewNamesPlug() ||
		input == inPlug()->dataWindowPlug()
	)
	{
		for( int i = 0; i < 2; ++i )
		{
			outputs.push_back( dataWindowPlug()->minPlug()->getChild( i ) );
			outputs.push_back( dataWindowPlug()->maxPlug()->getChild( i ) );
			outputs.push_back( centerPlug()->getChild( i ) );
			outputs.push_back( sizePlug()->getChild( i ) );
		}
	}
}

void DataWindowQuery::hash( const ValuePlug *output, const Context *context, MurmurHash &hash ) const
{
	ComputeNode::hash( output, context, hash );

	std::string view = viewPlug()->getValue();
	if( view.empty() )
	{
		view = context->get<std::string>( ImagePlug::viewNameContextName, ImagePlug::defaultViewName );
	}

	ImagePlug::ViewScope viewScope( context );
	viewScope.setViewNameChecked( &view, inPlug()->viewNames().get() );
	hash.append( inPlug()->dataWindowHash() );
}

void DataWindowQuery::compute( ValuePlug *output, const Context *context) const
{
	std::string view = viewPlug()->getValue();
	if( view.empty() )
	{
		view = context->get<std::string>( ImagePlug::viewNameContextName, ImagePlug::defaultViewName );
	}

	ImagePlug::ViewScope viewScope( context );
	viewScope.setViewNameChecked( &view, inPlug()->viewNames().get() );

	const Box2i dataWindow = inPlug()->dataWindow();

	const GraphComponent *parent = output->parent();

	if( parent == dataWindowPlug()->minPlug() )
	{
		static_cast<IntPlug *>( output )->setValue( output == parent->getChild( 0 ) ? dataWindow.min[0] : dataWindow.min[1] );
	}
	else if( parent == dataWindowPlug()->maxPlug() )
	{
		static_cast<IntPlug *>( output )->setValue( output == parent->getChild( 0 ) ? dataWindow.max[0] : dataWindow.max[1] );
	}
	else if( parent == centerPlug() )
	{
		Box2f floatWindow( dataWindow.min, dataWindow.max );
		static_cast<FloatPlug *>( output )->setValue( output == parent->getChild( 0 ) ? floatWindow.center()[0] : floatWindow.center()[1] );
	}
	else if( parent == sizePlug() )
	{
		static_cast<IntPlug *>( output )->setValue( output == parent->getChild( 0 ) ? dataWindow.size()[0] : dataWindow.size()[1] );
	}
	else
	{
		ComputeNode::compute( output, context );
	}
}