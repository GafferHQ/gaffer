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
#include "GafferImage/FilterProcessor.h"
#include "IECore/BoxAlgo.h"
#include "IECore/BoxOps.h"

using namespace Gaffer;
using namespace GafferImage;

IE_CORE_DEFINERUNTIMETYPED( FilterProcessor );

FilterProcessor::FilterProcessor( const std::string &name, int minimumInputs, int maximumInputs )
	:	ImageProcessor( name ),
	m_inputs( this, inPlug(), minimumInputs, maximumInputs )
{
}

FilterProcessor::~FilterProcessor()
{
}

const GafferImage::ImagePlug *FilterProcessor::inPlug( int index ) const
{
	return m_inputs.inputs()[index];
}

GafferImage::ImagePlug *FilterProcessor::inPlug( int index )
{
	return m_inputs.inputs()[index];
}

void FilterProcessor::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	const ImagePlugList& inputs( m_inputs.inputs() );
	for( ImagePlugList::const_iterator it( inputs.begin() ); it < inputs.end(); it++ )
	{
		if( input == (*it)->formatPlug() ||
				input == (*it)->dataWindowPlug() ||
				input == (*it)->channelNamesPlug() )
		{
			outputs.push_back( outPlug()->getChild<ValuePlug>( input->getName() ) );
			return;
		}
	}
	ImageProcessor::affects( input, outputs );
}

bool FilterProcessor::enabled() const
{
	if ( !ImageProcessor::enabled() )
	{
		return false;
	}

	const ImagePlugList::const_iterator end( m_inputs.endIterator() );
	for( ImagePlugList::const_iterator it( m_inputs.inputs().begin() ); it != end; it++ )
	{
		if ( !(*it)->getInput<ValuePlug>() )
		{
			return false;
		}
	}
	return true;
}

void FilterProcessor::hashFormatPlug( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	const ImagePlugList& inputs( m_inputs.inputs() );
	const ImagePlugList::const_iterator end( m_inputs.endIterator() );
	for( ImagePlugList::const_iterator it( inputs.begin() ); it != end; it++ )
	{
		if ( (*it)->getInput<ValuePlug>() )	(*it)->formatPlug()->hash( h );
	}
}

void FilterProcessor::hashDataWindowPlug( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	const ImagePlugList& inputs( m_inputs.inputs() );
	const ImagePlugList::const_iterator end( m_inputs.endIterator() );
	for( ImagePlugList::const_iterator it( inputs.begin() ); it != end; it++ )
	{
		if ( (*it)->getInput<ValuePlug>() )	(*it)->dataWindowPlug()->hash( h );
	}
}

void FilterProcessor::hashChannelNamesPlug( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	const ImagePlugList& inputs( m_inputs.inputs() );
	const ImagePlugList::const_iterator end( m_inputs.endIterator() );
	for( ImagePlugList::const_iterator it( inputs.begin() ); it != end; it++ )
	{
		if ( (*it)->getInput<ValuePlug>() )	(*it)->channelNamesPlug()->hash( h );
	}
}

void FilterProcessor::hashChannelDataPlug( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	const ImagePlugList& inputs( m_inputs.inputs() );
	const ImagePlugList::const_iterator end( m_inputs.endIterator() );
	for( ImagePlugList::const_iterator it( inputs.begin() ); it != end; it++ )
	{
		if ( (*it)->getInput<ValuePlug>() )	(*it)->channelDataPlug()->hash( h );
	}
}

Imath::Box2i FilterProcessor::computeDataWindow( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	Imath::Box2i dataWindow = inPlug()->dataWindowPlug()->getValue();
	const ImagePlugList& inputs( m_inputs.inputs() );
	const ImagePlugList::const_iterator end( m_inputs.endIterator() );
	for( ImagePlugList::const_iterator it( inputs.begin() ); it != end; it++ )
	{
		// We don't need to check that the plug is connected here as unconnected plugs don't have data windows.
		IECore::boxExtend( dataWindow, (*it)->dataWindowPlug()->getValue() );
	}
	return dataWindow;
}

GafferImage::Format FilterProcessor::computeFormat( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	const ImagePlugList& inputs( m_inputs.inputs() );
	const ImagePlugList::const_iterator end( m_inputs.endIterator() );
	for( ImagePlugList::const_iterator it( inputs.begin() ); it != end; it++ )
	{
		if ( (*it)->getInput<ValuePlug>() )	return (*it)->formatPlug()->getValue();
	}
	return inPlug()->formatPlug()->defaultValue();
}

IECore::ConstStringVectorDataPtr FilterProcessor::computeChannelNames( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	IECore::StringVectorDataPtr outChannelStrVectorData( new IECore::StringVectorData() );
	std::vector<std::string> &outChannels( outChannelStrVectorData->writable() );
	
	// Iterate over the connected inputs.
	const ImagePlugList& inputs( m_inputs.inputs() );
	const ImagePlugList::const_iterator end( m_inputs.endIterator() );
	for( ImagePlugList::const_iterator it( inputs.begin() ); it != end; it++ )
	{
		if ( (*it)->getInput<ValuePlug>() )
		{
			IECore::ConstStringVectorDataPtr inChannelStrVectorData((*it)->channelNamesPlug()->getValue() );
			const std::vector<std::string> &inChannels( inChannelStrVectorData->readable() );
			for ( std::vector<std::string>::const_iterator cIt( inChannels.begin() ); cIt != inChannels.end(); cIt++ )
			{
				if ( std::find( outChannels.begin(), outChannels.end(), (*cIt) ) == outChannels.end() )
				{
					outChannels.push_back(*cIt);
				}
			}
		}
	}

	if ( outChannels.empty() ) return inPlug()->channelNamesPlug()->defaultValue();
	return outChannelStrVectorData;
}

