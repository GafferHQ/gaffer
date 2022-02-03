//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2015, Image Engine Design Inc. All rights reserved.
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

#include "GafferImage/DisplayTransform.h"

#include "Gaffer/StringPlug.h"

using namespace std;
using namespace IECore;
using namespace Gaffer;
using namespace GafferImage;

GAFFER_NODE_DEFINE_TYPE( DisplayTransform );

size_t DisplayTransform::g_firstPlugIndex = 0;

DisplayTransform::DisplayTransform( const std::string &name )
	:	OpenColorIOTransform( name, true )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new StringPlug( "inputColorSpace" ) );
	addChild( new StringPlug( "display" ) );
	addChild( new StringPlug( "view" ) );
}

DisplayTransform::~DisplayTransform()
{
}

Gaffer::StringPlug *DisplayTransform::inputColorSpacePlug()
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

const Gaffer::StringPlug *DisplayTransform::inputColorSpacePlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

Gaffer::StringPlug *DisplayTransform::displayPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::StringPlug *DisplayTransform::displayPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

Gaffer::StringPlug *DisplayTransform::viewPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 2 );
}

const Gaffer::StringPlug *DisplayTransform::viewPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 2 );
}

bool DisplayTransform::affectsTransform( const Gaffer::Plug *input ) const
{
	return ( input == inputColorSpacePlug() || input == displayPlug() || input == viewPlug() );
}

void DisplayTransform::hashTransform( const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	std::string colorSpace = inputColorSpacePlug()->getValue();
	std::string display = displayPlug()->getValue();
	std::string view = viewPlug()->getValue();

	if( colorSpace.empty() || display.empty() || view.empty() )
	{
		h = MurmurHash();
		return;
	}

	h.append( colorSpace );
	h.append( display );
	h.append( view );
}

OCIO_NAMESPACE::ConstTransformRcPtr DisplayTransform::transform() const
{
	std::string colorSpace = inputColorSpacePlug()->getValue();
	std::string display = displayPlug()->getValue();
	std::string view = viewPlug()->getValue();

	// no need to run the processor if we don't
	// have valid inputs
	if( colorSpace.empty() || display.empty() || view.empty() )
	{
		return OCIO_NAMESPACE::ConstTransformRcPtr();
	}

#if OCIO_VERSION_HEX > 0x02000000
	OCIO_NAMESPACE::DisplayViewTransformRcPtr result = OCIO_NAMESPACE::DisplayViewTransform::Create();
	result->setSrc( colorSpace.c_str() );
#else
	OCIO_NAMESPACE::DisplayTransformRcPtr result = OCIO_NAMESPACE::DisplayTransform::Create();
	result->setInputColorSpaceName( colorSpace.c_str() );
#endif

	result->setDisplay( display.c_str() );
	result->setView( view.c_str() );

	return result;
}
