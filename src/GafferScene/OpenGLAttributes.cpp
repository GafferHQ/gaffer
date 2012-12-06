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

using namespace Imath;
using namespace GafferScene;

IE_CORE_DEFINERUNTIMETYPED( OpenGLAttributes );

OpenGLAttributes::OpenGLAttributes( const std::string &name )
	:	Attributes( name, Gaffer::Plug::Default )
{
	Gaffer::CompoundDataPlug *attributes = attributesPlug();
	
	// drawing parameters
	
	attributes->addOptionalMember( "gl:primitive:solid", new IECore::BoolData( true ), "primitiveSolid", false );
	
	attributes->addOptionalMember( "gl:primitive:wireframe", new IECore::BoolData( true ), "primitiveWireframe", false );
	attributes->addOptionalMember( "gl:primitive:wireframeColor", new IECore::Color4fData( Color4f( 0.25, 0.6, 0.85, 1 ) ), "primitiveWireframeColor", false );
	attributes->addOptionalMember( "gl:primitive:wireframeWidth", new IECore::FloatData( 1.0f ), "primitiveWireframeWidth", false );
	
	attributes->addOptionalMember( "gl:primitive:outline", new IECore::BoolData( true ), "primitiveOutline", false );
	attributes->addOptionalMember( "gl:primitive:outlineColor", new IECore::Color4fData( Color4f( 0.85, 0.75, 0.45, 1 ) ), "primitiveOutlineColor", false );
	attributes->addOptionalMember( "gl:primitive:outlineWidth", new IECore::FloatData( 1.0f ), "primitiveOutlineWidth", false );
	
	attributes->addOptionalMember( "gl:primitive:points", new IECore::BoolData( true ), "primitivePoints", false );
	attributes->addOptionalMember( "gl:primitive:pointColor", new IECore::Color4fData( Color4f( 0.85, 0.45, 0, 1 ) ), "primitivePointColor", false );
	attributes->addOptionalMember( "gl:primitive:pointWidth", new IECore::FloatData( 1.0f ), "primitivePointWidth", false );
	
	attributes->addOptionalMember( "gl:primitive:bound", new IECore::BoolData( true ), "primitiveBound", false );
	attributes->addOptionalMember( "gl:primitive:boundColor", new IECore::Color4fData( Color4f( 0.36, 0.8, 0.85, 1 ) ), "primitiveBoundColor", false );

	// points primitive parameters
	
	attributes->addOptionalMember( "gl:pointsPrimitive:useGLPoints", new IECore::StringData( "forGLPoints" ), "pointsPrimitiveUseGLPoints", false );
	attributes->addOptionalMember( "gl:pointsPrimitive:glPointWidth", new IECore::FloatData( 1.0 ), "pointsPrimitiveGLPointWidth", false );
		
	// curves primitive parameters
	
	attributes->addOptionalMember( "gl:curvesPrimitive:useGLLines", new IECore::BoolData( false ), "curvesPrimitiveUseGLLines", false );
	attributes->addOptionalMember( "gl:curvesPrimitive:glLineWidth", new IECore::FloatData( 1.0 ), "curvesPrimitiveGLLineWidth", false );
	attributes->addOptionalMember( "gl:curvesPrimitive:ignoreBasis", new IECore::BoolData( false ), "curvesPrimitiveIgnoreBasis", false );
	
}

OpenGLAttributes::~OpenGLAttributes()
{
}
