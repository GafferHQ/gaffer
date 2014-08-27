//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2013, Image Engine Design Inc. All rights reserved.
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

#include "Gaffer/Context.h"
#include "GafferImage/Select.h"

using namespace IECore;
using namespace Gaffer;

namespace GafferImage
{

IE_CORE_DEFINERUNTIMETYPED( Select );

size_t Select::g_firstPlugIndex = 0;

Select::Select( const std::string &name )
	:	FilterProcessor( name, 2, 50 )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new IntPlug( "select" ) );
}

Select::~Select()
{
}

Gaffer::IntPlug *Select::selectPlug()
{
	return getChild<IntPlug>( g_firstPlugIndex );
}

const Gaffer::IntPlug *Select::selectPlug() const
{
	return getChild<IntPlug>( g_firstPlugIndex );
}

void Select::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	if( input == selectPlug() )
	{
		outputs.push_back( outPlug()->channelDataPlug() );
	}
	else FilterProcessor::affects( input, outputs );
}

bool Select::enabled() const
{
	// Call enabled() on the image node as we don't care whether the inputs are connected or not.
	return ImageNode::enabled();
}

int Select::selectIndex() const
{
	int index = selectPlug()->getValue();
	return std::min( (int)m_inputs.inputs().size()-1, std::max( 0, index ) );
}

void Select::hashChannelData( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	inPlug( selectIndex() )->channelDataPlug()->hash(h);
}

void Select::hashFormat( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	inPlug( selectIndex() )->formatPlug()->hash(h);
}

void Select::hashDataWindow( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	inPlug( selectIndex() )->dataWindowPlug()->hash(h);
}

void Select::hashChannelNames( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	inPlug( selectIndex() )->channelNamesPlug()->hash(h);
}

IECore::ConstStringVectorDataPtr Select::computeChannelNames( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	return inPlug( selectIndex() )->channelNamesPlug()->getValue();
}

IECore::ConstFloatVectorDataPtr Select::computeChannelData( const std::string &channelName, const Imath::V2i &tileOrigin, const Gaffer::Context *context, const ImagePlug *parent ) const
{
	return inPlug( selectIndex() )->channelDataPlug()->getValue();
}

Imath::Box2i Select::computeDataWindow( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	return inPlug( selectIndex() )->dataWindowPlug()->getValue();
}

GafferImage::Format Select::computeFormat( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	return inPlug( selectIndex() )->formatPlug()->getValue();
}

} // namespace GafferImage

