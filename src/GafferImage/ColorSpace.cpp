//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2012, John Haddon. All rights reserved.
//  Copyright (c) 2012-2015, Image Engine Design Inc. All rights reserved.
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

#include "GafferImage/ColorSpace.h"

#include "Gaffer/StringPlug.h"

using namespace std;
using namespace IECore;
using namespace Gaffer;

// code is in the namespace to avoid clashes between OpenColorIO the gaffer class,
// and OpenColorIO the library namespace.
namespace GafferImage
{

GAFFER_NODE_DEFINE_TYPE( ColorSpace );

size_t ColorSpace::g_firstPlugIndex = 0;

ColorSpace::ColorSpace( const std::string &name )
	:	OpenColorIOTransform( name, true )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new StringPlug( "inputSpace" ) );
	addChild( new StringPlug( "outputSpace" ) );
}

ColorSpace::~ColorSpace()
{
}

Gaffer::StringPlug *ColorSpace::inputSpacePlug()
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

const Gaffer::StringPlug *ColorSpace::inputSpacePlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

Gaffer::StringPlug *ColorSpace::outputSpacePlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::StringPlug *ColorSpace::outputSpacePlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

bool ColorSpace::affectsTransform( const Gaffer::Plug *input ) const
{
	return ( input == inputSpacePlug() || input == outputSpacePlug() );
}

void ColorSpace::hashTransform( const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	std::string inSpace = inputSpacePlug()->getValue();
	std::string outSpace = outputSpacePlug()->getValue();

	if( inSpace == outSpace || inSpace.empty() || outSpace.empty() )
	{
		h = MurmurHash();
		return;
	}

	inputSpacePlug()->hash( h );
	outputSpacePlug()->hash( h );
}

OpenColorIO::ConstTransformRcPtr ColorSpace::transform() const
{
	string inputSpace( inputSpacePlug()->getValue() );
	string outputSpace( outputSpacePlug()->getValue() );

	// no need to run the processor if we're not
	// actually changing the color space.
	if( ( inputSpace == outputSpace ) || inputSpace.empty() || outputSpace.empty() )
	{
		return OpenColorIO::ColorSpaceTransformRcPtr();
	}

	OpenColorIO::ColorSpaceTransformRcPtr result = OpenColorIO::ColorSpaceTransform::Create();
	result->setSrc( inputSpace.c_str() );
	result->setDst( outputSpace.c_str() );

	return result;
}

} // namespace GafferImage
