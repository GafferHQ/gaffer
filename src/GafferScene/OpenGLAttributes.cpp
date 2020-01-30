//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2012, Image Engine Design Inc. All rights reserved.
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

#include "GafferScene/OpenGLAttributes.h"
#include "Gaffer/NameValuePlug.h"

using namespace Imath;
using namespace Gaffer;
using namespace GafferScene;

GAFFER_GRAPHCOMPONENT_DEFINE_TYPE( OpenGLAttributes );

OpenGLAttributes::OpenGLAttributes( const std::string &name )
	:	Attributes( name )
{
	Gaffer::CompoundDataPlug *attributes = attributesPlug();

	// drawing parameters

	attributes->addChild( new NameValuePlug( "gl:primitive:solid", new IECore::BoolData( true ), false, "primitiveSolid" ) ); 

	attributes->addChild( new NameValuePlug( "gl:primitive:wireframe", new IECore::BoolData( true ), false, "primitiveWireframe" ) ); 
	attributes->addChild( new NameValuePlug( "gl:primitive:wireframeColor", new IECore::Color4fData( Color4f( 0.25, 0.6, 0.85, 1 ) ), false, "primitiveWireframeColor" ) ); 
	attributes->addChild( new NameValuePlug( "gl:primitive:wireframeWidth", new FloatPlug( "value", Gaffer::Plug::Direction::In, 1.0f, 0.1f, 32.0f ), false, "primitiveWireframeWidth" ) );

	attributes->addChild( new NameValuePlug( "gl:primitive:outline", new IECore::BoolData( true ), false, "primitiveOutline" ) );
	attributes->addChild( new NameValuePlug( "gl:primitive:outlineColor", new IECore::Color4fData( Color4f( 0.85, 0.75, 0.45, 1 ) ), false, "primitiveOutlineColor" ) );
	attributes->addChild( new NameValuePlug( "gl:primitive:outlineWidth", new IECore::FloatData( 1.0f ), false, "primitiveOutlineWidth" ) );

	attributes->addChild( new NameValuePlug( "gl:primitive:points", new IECore::BoolData( true ), false, "primitivePoint" ) );
	attributes->addChild( new NameValuePlug( "gl:primitive:pointColor", new IECore::Color4fData( Color4f( 0.85, 0.45, 0, 1 ) ), false, "primitivePointColor" ) );
	attributes->addChild( new NameValuePlug( "gl:primitive:pointWidth", new IECore::FloatData( 1.0f ), false, "primitivePointWidth" ) );

	attributes->addChild( new NameValuePlug( "gl:primitive:bound", new IECore::BoolData( true ), false, "primitiveBound" ) );
	attributes->addChild( new NameValuePlug( "gl:primitive:boundColor", new IECore::Color4fData( Color4f( 0.36, 0.8, 0.85, 1 ) ), false, "primitiveBoundColor" ) );

	// points primitive parameters

	attributes->addChild( new NameValuePlug( "gl:pointsPrimitive:useGLPoints", new IECore::StringData( "forGLPoints" ), false, "pointsPrimitiveUseGLPoints" ) );
	attributes->addChild( new NameValuePlug( "gl:pointsPrimitive:glPointWidth", new FloatPlug( "value", Gaffer::Plug::Direction::In, 1.0f, 0.1f, 128.0f ), false, "pointsPrimitiveGLPointWidth" ) ); 

	// curves primitive parameters

	attributes->addChild( new NameValuePlug( "gl:curvesPrimitive:useGLLines", new IECore::BoolData( false ), false, "curvesPrimitiveUseGLLines" ) );
	attributes->addChild( new NameValuePlug( "gl:curvesPrimitive:glLineWidth", new FloatPlug( "value", Gaffer::Plug::Direction::In, 1.0f, 0.1f, 32.0f ), false, "curvesPrimitiveGLLineWidth" ) );
	attributes->addChild( new NameValuePlug( "gl:curvesPrimitive:ignoreBasis", new IECore::BoolData( false ), false, "curvesPrimitiveIgnoreBasis" ) );

	// visualisers

	attributes->addChild( new Gaffer::NameValuePlug( "gl:visualiser:ornamentScale", new FloatPlug( "value", Gaffer::Plug::Direction::In, 1.0f, 0.01f ), false, "visualiserOrnamentScale" ) );
	attributes->addChild( new Gaffer::NameValuePlug( "gl:visualiser:maxTextureResolution", new IntPlug( "value", Gaffer::Plug::Direction::In, 512, 2, 2048 ), false, "visualiserMaxTextureResolution" ) );
	attributes->addChild( new Gaffer::NameValuePlug( "gl:visualiser:frustum", new IECore::BoolData( true ), false, "visualiserFrustum" ) );
	attributes->addChild( new Gaffer::NameValuePlug( "gl:light:drawingMode", new IECore::StringData( "texture" ), false, "lightDrawingMode" ) );
}

OpenGLAttributes::~OpenGLAttributes()
{
}
