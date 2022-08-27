//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2014, Esteban Tovagliari. All rights reserved.
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

#include "GafferAppleseed/AppleseedAttributes.h"

#include "Gaffer/FilePathPlug.h"

using namespace Imath;
using namespace Gaffer;
using namespace GafferAppleseed;

GAFFER_NODE_DEFINE_TYPE( AppleseedAttributes );

AppleseedAttributes::AppleseedAttributes( const std::string &name )
	:	GafferScene::Attributes( name )
{
	Gaffer::CompoundDataPlug *attributes = attributesPlug();

	// visibility parameters
	attributes->addChild( new Gaffer::NameValuePlug( "as:visibility:camera", new IECore::BoolData( true ), false, "cameraVisibility" ) );
	attributes->addChild( new Gaffer::NameValuePlug( "as:visibility:light", new IECore::BoolData( true ), false, "lightVisibility" ) );
	attributes->addChild( new Gaffer::NameValuePlug( "as:visibility:shadow", new IECore::BoolData( true ), false, "shadowVisibility" ) );
	attributes->addChild( new Gaffer::NameValuePlug( "as:visibility:diffuse", new IECore::BoolData( true ), false, "diffuseVisibility" ) );
	attributes->addChild( new Gaffer::NameValuePlug( "as:visibility:specular", new IECore::BoolData( true ), false, "specularVisibility" ) );
	attributes->addChild( new Gaffer::NameValuePlug( "as:visibility:glossy", new IECore::BoolData( true ), false, "glossyVisibility" ) );

	// shading parameters
	attributes->addChild( new Gaffer::NameValuePlug( "as:shading_samples", new IECore::IntData( 1 ), false, "shadingSamples" ) );
	attributes->addChild( new Gaffer::NameValuePlug( "as:double_sided", new IECore::BoolData( true ), false, "doubleSided" ) );
	attributes->addChild( new Gaffer::NameValuePlug( "as:medium_priority", new IECore::IntData( 0 ), false, "mediumPriority" ) );

	// alpha map parameters
	attributes->addChild( new Gaffer::NameValuePlug( "as:alpha_map", new Gaffer::FilePathPlug(), false, "alphaMap" ) );

	// mesh parameters
	attributes->addChild( new Gaffer::NameValuePlug( "as:smooth_normals", new IECore::BoolData(), false, "smoothNormals" ) );
	attributes->addChild( new Gaffer::NameValuePlug( "as:smooth_tangents", new IECore::BoolData(), false, "smoothTangents" ) );
}

AppleseedAttributes::~AppleseedAttributes()
{
}
