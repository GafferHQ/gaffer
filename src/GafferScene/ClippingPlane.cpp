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

#include "GafferScene/ClippingPlane.h"

#include "Gaffer/StringPlug.h"

#include "IECoreScene/ClippingPlane.h"

using namespace Gaffer;
using namespace GafferScene;
using namespace Imath;

static IECore::InternedString g_clippingPlanesSetName( "__clippingPlanes" );

GAFFER_NODE_DEFINE_TYPE( ClippingPlane );

ClippingPlane::ClippingPlane( const std::string &name )
	:	ObjectSource( name, "clippingPlane" )
{
}

ClippingPlane::~ClippingPlane()
{
}

void ClippingPlane::hashSource( const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
}

IECore::ConstObjectPtr ClippingPlane::computeSource( const Context *context ) const
{
	return new IECoreScene::ClippingPlane();
}

IECore::ConstInternedStringVectorDataPtr ClippingPlane::computeStandardSetNames() const
{
	IECore::InternedStringVectorDataPtr result = new IECore::InternedStringVectorData();
	result->writable().push_back( g_clippingPlanesSetName );
	return result;
}
