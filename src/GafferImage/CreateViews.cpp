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

#include "GafferImage/CreateViews.h"

#include "GafferImage/BufferAlgo.h"
#include "GafferImage/ImageAlgo.h"

#include "Gaffer/ArrayPlug.h"
#include "Gaffer/Context.h"
#include "Gaffer/NameValuePlug.h"

#include "boost/bind/bind.hpp"
#include "boost/range/adaptor/reversed.hpp"

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace Gaffer;
using namespace GafferImage;

//////////////////////////////////////////////////////////////////////////
// CreateViews
//////////////////////////////////////////////////////////////////////////

GAFFER_NODE_DEFINE_TYPE( CreateViews );

size_t CreateViews::g_firstPlugIndex = 0;

CreateViews::CreateViews( const std::string &name )
	:	ImageNode( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );

	ArrayPlugPtr views = new ArrayPlug(
		"views",
		Plug::In,
		new NameValuePlug(
			/* nameDefault = */ "",
			/* valuePlug = */ new ImagePlug(),
			/* defaultEnabled = */ true,
			/* name = */ "view0"
		),
		0,
		std::numeric_limits<size_t>::max(),
		Plug::Default,
		/* resizeWhenInputsChange = */ false
	);

	addChild( views );

	addChild( new IntPlug( "__index", Plug::Out ) );

	SwitchPtr s = new Switch( "__switch" );
	addChild( s );

	s->setup( new ImagePlug() );
	s->indexPlug()->setInput( indexPlug() );

	ImagePlug *switchOut = runTimeCast< ImagePlug >( s->outPlug() );
	outPlug()->setFlags( Plug::Serialisable, false );
	outPlug()->formatPlug()->setInput( switchOut->formatPlug() );
	outPlug()->dataWindowPlug()->setInput( switchOut->dataWindowPlug() );
	outPlug()->metadataPlug()->setInput( switchOut->metadataPlug() );
	outPlug()->deepPlug()->setInput( switchOut->deepPlug() );
	outPlug()->sampleOffsetsPlug()->setInput( switchOut->sampleOffsetsPlug() );
	outPlug()->channelNamesPlug()->setInput( switchOut->channelNamesPlug() );
	outPlug()->channelDataPlug()->setInput( switchOut->channelDataPlug() );

	views->childAddedSignal().connect( boost::bind( &CreateViews::synchronizeSwitch, this ) );
	views->childRemovedSignal().connect( boost::bind( &CreateViews::synchronizeSwitch, this ) );

}

CreateViews::~CreateViews()
{
}

Gaffer::ArrayPlug *CreateViews::viewsPlug()
{
	return getChild<Gaffer::ArrayPlug>( g_firstPlugIndex + 0 );
}

const Gaffer::ArrayPlug *CreateViews::viewsPlug() const
{
	return getChild<Gaffer::ArrayPlug>( g_firstPlugIndex + 0 );
}

Gaffer::IntPlug *CreateViews::indexPlug()
{
	return getChild<Gaffer::IntPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::IntPlug *CreateViews::indexPlug() const
{
	return getChild<Gaffer::IntPlug>( g_firstPlugIndex + 1 );
}

Gaffer::Switch *CreateViews::switchNode()
{
	return getChild<Gaffer::Switch>( g_firstPlugIndex + 2 );
}

const Gaffer::Switch *CreateViews::switchNode() const
{
	return getChild<Gaffer::Switch>( g_firstPlugIndex + 2 );
}

void CreateViews::synchronizeSwitch()
{
	int numViews = viewsPlug()->children().size();
	switchNode()->inPlugs()->resize( numViews );
	for( int i = 0; i < numViews; i++ )
	{
		NameValuePlug *source = viewsPlug()->getChild<NameValuePlug>( i );
		ImagePlug *dest = switchNode()->inPlugs()->getChild<ImagePlug>( i );
		dest->setInput( source->valuePlug() );
	}
}

void CreateViews::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	ImageNode::affects( input, outputs );

	auto nameValuePlug = input->ancestor<NameValuePlug>();
	if(
		nameValuePlug && nameValuePlug->parent() == viewsPlug() &&
		( input == nameValuePlug->namePlug() || input == nameValuePlug->enabledPlug() || input == nameValuePlug->valuePlug<ImagePlug>()->viewNamesPlug() )
	)
	{
		outputs.push_back( outPlug()->viewNamesPlug() );
		outputs.push_back( indexPlug() );
	}

}

void CreateViews::hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ImageNode::hash( output, context, h );

	if( output != indexPlug() )
	{
		return;
	}

	h.append( context->get<std::string>( ImagePlug::viewNameContextName, ImagePlug::defaultViewName ) );

	Context::EditableScope s( context );
	s.remove( ImagePlug::viewNameContextName );

	for( auto &nameValue : NameValuePlug::Range( *viewsPlug() ) )
	{
		if( nameValue->enabledPlug() )
		{
			nameValue->enabledPlug()->hash( h );
		}
		nameValue->namePlug()->hash( h );
		nameValue->valuePlug<ImagePlug>()->viewNamesPlug()->hash( h );
	}
}

void CreateViews::compute( Gaffer::ValuePlug *output, const Gaffer::Context *context ) const
{
	if( output != indexPlug() )
	{
		ImageNode::compute( output, context );
		return;
	}

	const std::string &currentView = context->get<std::string>( ImagePlug::viewNameContextName, ImagePlug::defaultViewName );

	Context::EditableScope s( context );
	s.remove( ImagePlug::viewNameContextName );

	int matchIndex = -1;
	int defaultIndex = -1;
	int index = 0;
	for( auto &nameValue : NameValuePlug::Range( *viewsPlug()  ) )
	{
		if( !nameValue->enabledPlug() || nameValue->enabledPlug()->getValue() )
		{
			if( nameValue->valuePlug<ImagePlug>()->viewNamesPlug()->getValue()->readable() != ImagePlug::defaultViewNames()->readable() )
			{
				throw IECore::Exception( "CreateViews : Inputs must have just a default view." );
			}

			std::string n = nameValue->namePlug()->getValue();

			if( n == currentView )
			{
				matchIndex = index;
			}
			else if( matchIndex == -1 && n == ImagePlug::defaultViewName )
			{
				defaultIndex = index;
			}
		}
		index++;
	}

	int result;
	if( matchIndex != -1 )
	{
		result = matchIndex;
	}
	else if( defaultIndex != -1 )
	{
		result = defaultIndex;
	}
	else
	{
		throw IECore::Exception( "CreateViews : Not outputting view \"" + currentView + "\"." );
	}

	static_cast<IntPlug *>( output )->setValue( result );
}

void CreateViews::hashViewNames( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ImageNode::hashViewNames( output, context, h );
	for( auto &nameValue : NameValuePlug::Range( *viewsPlug() ) )
	{
		if( nameValue->enabledPlug() )
		{
			nameValue->enabledPlug()->hash( h );
		}
		nameValue->namePlug()->hash( h );
	}
}

IECore::ConstStringVectorDataPtr CreateViews::computeViewNames( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	StringVectorDataPtr resultData = new StringVectorData();
	std::vector< string > &result = resultData->writable();
	std::vector< std::string > newNames;
	for( auto &nameValue : NameValuePlug::Range( *viewsPlug()  ) )
	{
		if( !nameValue->enabledPlug() || nameValue->enabledPlug()->getValue() )
		{
			std::string n = nameValue->namePlug()->getValue();

			if( n.size() && std::find( result.begin(), result.end(), n ) == result.end() )
			{
				result.push_back( n );
			}
		}
	}

	return resultData;
}
