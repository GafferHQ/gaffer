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

#include "Gaffer/TypedObjectPlug.h"

#include "GafferImage/ChannelMaskPlug.h"

using namespace GafferImage;
using namespace IECore;

IE_CORE_DEFINERUNTIMETYPED( ChannelMaskPlug );

ChannelMaskPlug::ChannelMaskPlug(
	const std::string &name,
	Direction direction,
	IECore::ConstStringVectorDataPtr defaultValue,
	unsigned flags
)
	:	Gaffer::StringVectorDataPlug( name, direction, defaultValue, flags )
{
}

ChannelMaskPlug::~ChannelMaskPlug()
{
}

void ChannelMaskPlug::maskChannels( std::vector<std::string> &inChannels ) const
{
	ConstStringVectorDataPtr channelNamesData = getValue();
	const std::vector<std::string> &maskChannels = channelNamesData->readable();

	// Intersect the inChannels and the maskChannels in place.
	std::vector<std::string>::iterator cIt( inChannels.begin() );
	while ( cIt != inChannels.end() )
	{
		if ( std::find( maskChannels.begin(), maskChannels.end(), (*cIt) ) == maskChannels.end() )
		{
			cIt = inChannels.erase( cIt );
		}
		else
		{
			++cIt;
		}
	}
}

void ChannelMaskPlug::removeDuplicateIndices( std::vector<std::string> &inChannels )
{
	if( inChannels.size() > 1 )
	{
		std::vector<std::string>::iterator cIt( inChannels.begin() );
		while ( cIt != inChannels.end() )
		{
			int idx = channelIndex( *cIt );
			std::vector<std::string>::iterator duplicateIt( cIt + 1 );
			while ( duplicateIt != inChannels.end() )
			{
				if ( channelIndex( *duplicateIt ) == idx )
				{
					inChannels.erase( duplicateIt );
					duplicateIt = cIt + 1;
				}
				else
				{	
					++duplicateIt;
				}
			}
			++cIt;
		}
	}
}

int ChannelMaskPlug::channelIndex( std::string channel )
{
	// Strip from the channel string any layer information...
	size_t pos = channel.find_last_of(".");
	if ( pos != std::string::npos )
	{
		channel.erase( channel.begin(), channel.begin()+pos+1 );
	}

	///\todo: Replace this temporary code below with a lookup into a table of channels and their indexes
	if ( channel == "R") return 0;
	if ( channel == "G") return 1;
	if ( channel == "B") return 2;
	if ( channel == "A") return 3;
	
	return 0;
}

