//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2018, Alex Fuller. All rights reserved.
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

#include "GafferCycles/CyclesAttributes.h"

#include "Gaffer/StringPlug.h"

using namespace Gaffer;
using namespace GafferCycles;

IE_CORE_DEFINERUNTIMETYPED( CyclesAttributes );

CyclesAttributes::CyclesAttributes( const std::string &name )
	:	GafferScene::Attributes( name )
{
	Gaffer::CompoundDataPlug *attributes = attributesPlug();

	// Visibility parameters
	attributes->addChild( new Gaffer::NameValuePlug( "cycles:visibility:camera", new IECore::BoolData( true ), false, "cameraVisibility" ) );
	attributes->addChild( new Gaffer::NameValuePlug( "cycles:visibility:diffuse", new IECore::BoolData( true ), false, "diffuseVisibility" ) );
	attributes->addChild( new Gaffer::NameValuePlug( "cycles:visibility:glossy", new IECore::BoolData( true ), false, "glossyVisibility" ) );
	attributes->addChild( new Gaffer::NameValuePlug( "cycles:visibility:transmission", new IECore::BoolData( true ), false, "transmissionVisibility" ) );
	attributes->addChild( new Gaffer::NameValuePlug( "cycles:visibility:shadow", new IECore::BoolData( true ), false, "shadowVisibility" ) );
	attributes->addChild( new Gaffer::NameValuePlug( "cycles:visibility:scatter", new IECore::BoolData( true ), false, "scatterVisibility" ) );

	// Shading parameters
	attributes->addChild( new Gaffer::NameValuePlug( "cycles:use_holdout", new IECore::BoolData( false ), false, "useHoldout" ) );
	attributes->addChild( new Gaffer::NameValuePlug( "cycles:is_shadow_catcher", new IECore::BoolData( false ), false, "isShadowCatcher" ) );
	attributes->addChild( new Gaffer::NameValuePlug( "cycles:shadow_terminator_shading_offset", new IECore::FloatData( 0.0f ), false, "shadowTerminatorShadingOffset" ) );
	attributes->addChild( new Gaffer::NameValuePlug( "cycles:shadow_terminator_geometry_offset", new IECore::FloatData( 0.0f ), false, "shadowTerminatorGeometryOffset" ) );
	attributes->addChild( new Gaffer::NameValuePlug( "cycles:is_caustics_caster", new IECore::BoolData( false ), false, "isCausticsCaster" ) );
	attributes->addChild( new Gaffer::NameValuePlug( "cycles:is_caustics_receiver", new IECore::BoolData( false ), false, "isCausticsReceiver" ) );

	// Subdivision parameters
	attributes->addChild( new Gaffer::NameValuePlug( "cycles:max_level", new IECore::IntData( 1 ), false, "maxLevel" ) );
	attributes->addChild( new Gaffer::NameValuePlug( "cycles:dicing_rate", new IECore::FloatData( 1.0f ), false, "dicingScale" ) );

	// Light-Group
	attributes->addChild( new Gaffer::NameValuePlug( "cycles:lightgroup", new IECore::StringData( "" ), false, "lightGroup" ) );

	// Volume
	attributes->addChild( new Gaffer::NameValuePlug( "cycles:volume_clipping", new IECore::FloatData( 0.001f ), false, "volumeClipping" ) );
	attributes->addChild( new Gaffer::NameValuePlug( "cycles:volume_step_size", new IECore::FloatData( 0.0f ), false, "volumeStepSize" ) );
	attributes->addChild( new Gaffer::NameValuePlug( "cycles:volume_object_space", new IECore::BoolData( true ), false, "volumeObjectSpace" ) );

	// Per-object parameters
	attributes->addChild( new Gaffer::NameValuePlug( "cycles:dupli_generated", new IECore::V3fData( Imath::V3f( 0.0f ) ), false, "dupliGenerated" ) );
	attributes->addChild( new Gaffer::NameValuePlug( "cycles:dupli_uv", new IECore::V2fData( Imath::V2f( 0.0f ) ), false, "dupliUV" ) );

	// Asset name for cryptomatte
	attributes->addChild( new Gaffer::NameValuePlug( "cycles:asset_name", new IECore::StringData( "" ), false, "assetName" ) );

	// Shader-specific
	attributes->addChild( new Gaffer::NameValuePlug( "cycles:shader:emission_sampling_method", new IECore::StringData( "auto" ), false, "emissionSamplingMethod" ) );
	attributes->addChild( new Gaffer::NameValuePlug( "cycles:shader:use_transparent_shadow", new IECore::BoolData( true ), false, "useTransparentShadow" ) );
	attributes->addChild( new Gaffer::NameValuePlug( "cycles:shader:heterogeneous_volume", new IECore::BoolData( true ), false, "heterogeneousVolume" ) );
	attributes->addChild( new Gaffer::NameValuePlug( "cycles:shader:volume_sampling_method", new IECore::StringData( "multiple_importance" ), false, "volumeSamplingMethod" ) );
	attributes->addChild( new Gaffer::NameValuePlug( "cycles:shader:volume_interpolation_method", new IECore::StringData( "linear" ), false, "volumeInterpolationMethod" ) );
	attributes->addChild( new Gaffer::NameValuePlug( "cycles:shader:volume_step_rate", new IECore::FloatData( 1.0f ), false, "volumeStepRate" ) );
	attributes->addChild( new Gaffer::NameValuePlug( "cycles:shader:displacement_method", new IECore::StringData( "bump" ), false, "displacementMethod" ) );
}

CyclesAttributes::~CyclesAttributes()
{
}
