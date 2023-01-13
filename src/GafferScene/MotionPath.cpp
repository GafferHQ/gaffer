//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2021, Image Engine Design Inc. All rights reserved.
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

#include "GafferScene/MotionPath.h"

#include "GafferScene/Isolate.h"
#include "GafferScene/SceneAlgo.h"

#include "Gaffer/Context.h"
#include "Gaffer/NumericPlug.h"

#include "IECoreScene/CurvesPrimitive.h"

#include "OpenEXR/OpenEXRConfig.h"
#if OPENEXR_VERSION_MAJOR < 3
#include "OpenEXR/ImathMatrixAlgo.h"
#else
#include "Imath/ImathMatrixAlgo.h"
#endif

using namespace IECore;
using namespace IECoreScene;
using namespace Gaffer;
using namespace GafferScene;

namespace
{

InternedString g_lightsSetName( "__lights" );
InternedString g_defaultLightsSetName( "defaultLights" );
InternedString g_camerasSetName( "__cameras" );

} // namespace

GAFFER_NODE_DEFINE_TYPE( MotionPath );

size_t MotionPath::g_firstPlugIndex = 0;

MotionPath::MotionPath( const std::string &name )
	:	FilteredSceneProcessor( name, PathMatcher::NoMatch )
{
	storeIndexOfNextChild( g_firstPlugIndex );

	ValuePlugPtr startPlug = new ValuePlug( "start", Plug::In );
	startPlug->addChild( new IntPlug( "mode", Plug::In, (int)FrameMode::Relative, /* min */ (int)FrameMode::Relative, /* max */ (int)FrameMode::Absolute ) );
	startPlug->addChild( new FloatPlug( "frame", Plug::In, -2 ) );
	addChild( startPlug );

	ValuePlugPtr endPlug = new ValuePlug( "end", Plug::In );
	endPlug->addChild( new IntPlug( "mode", Plug::In, (int)FrameMode::Relative, /* min */ (int)FrameMode::Relative, /* max */ (int)FrameMode::Absolute ) );
	endPlug->addChild( new FloatPlug( "frame", Plug::In, 2 ) );
	addChild( endPlug );

	addChild( new IntPlug( "samplingMode", Plug::In, (int)SamplingMode::Variable, /* min */ (int)SamplingMode::Variable, /* max */ (int)SamplingMode::Fixed ) );
	addChild( new FloatPlug( "step", Plug::In, 1, 1e-6 ) );
	addChild( new IntPlug( "samples", Plug::In, 10, 2 ) );

	addChild( new BoolPlug( "adjustBounds", Plug::In, true ) );

	addChild( new ScenePlug( "__isolatedScene", Plug::In, Plug::Default & ~Plug::Serialisable ) );
	IsolatePtr isolate = new Isolate( "__Isolate" );
	addChild( isolate );
	isolate->filterPlug()->setInput( filterPlug() );
	isolate->inPlug()->setInput( inPlug() );
	isolatedInPlug()->setInput( isolate->outPlug() );

	outPlug()->childNamesPlug()->setInput( isolatedInPlug()->childNamesPlug() );
	outPlug()->globalsPlug()->setInput( isolatedInPlug()->globalsPlug() );
}

MotionPath::~MotionPath()
{
}

IntPlug *MotionPath::startModePlug()
{
	return getChild<ValuePlug>( g_firstPlugIndex )->getChild<IntPlug>( 0 );
}

const IntPlug *MotionPath::startModePlug() const
{
	return getChild<ValuePlug>( g_firstPlugIndex )->getChild<IntPlug>( 0 );
}

FloatPlug *MotionPath::startFramePlug()
{
	return getChild<ValuePlug>( g_firstPlugIndex )->getChild<FloatPlug>( 1 );
}

const FloatPlug *MotionPath::startFramePlug() const
{
	return getChild<ValuePlug>( g_firstPlugIndex )->getChild<FloatPlug>( 1 );
}

IntPlug *MotionPath::endModePlug()
{
	return getChild<ValuePlug>( g_firstPlugIndex + 1 )->getChild<IntPlug>( 0 );
}

const IntPlug *MotionPath::endModePlug() const
{
	return getChild<ValuePlug>( g_firstPlugIndex + 1 )->getChild<IntPlug>( 0 );
}

FloatPlug *MotionPath::endFramePlug()
{
	return getChild<ValuePlug>( g_firstPlugIndex + 1 )->getChild<FloatPlug>( 1 );
}

const FloatPlug *MotionPath::endFramePlug() const
{
	return getChild<ValuePlug>( g_firstPlugIndex + 1 )->getChild<FloatPlug>( 1 );
}

Gaffer::IntPlug *MotionPath::samplingModePlug()
{
	return getChild<IntPlug>( g_firstPlugIndex + 2 );
}

const Gaffer::IntPlug *MotionPath::samplingModePlug() const
{
	return getChild<IntPlug>( g_firstPlugIndex + 2 );
}

Gaffer::FloatPlug *MotionPath::stepPlug()
{
	return getChild<FloatPlug>( g_firstPlugIndex + 3 );
}

const Gaffer::FloatPlug *MotionPath::stepPlug() const
{
	return getChild<FloatPlug>( g_firstPlugIndex + 3 );
}

Gaffer::IntPlug *MotionPath::samplesPlug()
{
	return getChild<IntPlug>( g_firstPlugIndex + 4 );
}

const Gaffer::IntPlug *MotionPath::samplesPlug() const
{
	return getChild<IntPlug>( g_firstPlugIndex + 4 );
}

BoolPlug *MotionPath::adjustBoundsPlug()
{
	return getChild<BoolPlug>( g_firstPlugIndex + 5 );
}

const BoolPlug *MotionPath::adjustBoundsPlug() const
{
	return getChild<BoolPlug>( g_firstPlugIndex + 5 );
}

ScenePlug *MotionPath::isolatedInPlug()
{
	return getChild<ScenePlug>( g_firstPlugIndex + 6 );
}

const ScenePlug *MotionPath::isolatedInPlug() const
{
	return getChild<ScenePlug>( g_firstPlugIndex + 6 );
}

void MotionPath::affects( const Plug *input, DependencyNode::AffectedPlugsContainer &outputs ) const
{
	FilteredSceneProcessor::affects( input, outputs );

	if(
		input == filterPlug() ||
		input == adjustBoundsPlug() ||
		input == outPlug()->objectPlug()
	)
	{
		outputs.push_back( outPlug()->boundPlug() );
	}

	if(
		input == filterPlug() ||
		input == startModePlug() ||
		input == startFramePlug() ||
		input == endModePlug() ||
		input == endFramePlug() ||
		input == samplingModePlug() ||
		input == stepPlug() ||
		input == samplesPlug() ||
		input == inPlug()->transformPlug()
	)
	{
		outputs.push_back( outPlug()->objectPlug() );
	}

	if( input == isolatedInPlug()->setNamesPlug() )
	{
		outputs.push_back( outPlug()->setNamesPlug() );
	}

	if( input == isolatedInPlug()->setPlug() )
	{
		outputs.push_back( outPlug()->setPlug() );
	}
}

void MotionPath::hashBound( const ScenePath &path, const Context *context, const ScenePlug *parent, MurmurHash &h ) const
{
	if( !adjustBoundsPlug()->getValue() )
	{
		h = inPlug()->boundPlug()->hash();
		return;
	}

	FilteredSceneProcessor::hashBound( path, context, parent, h );

	const PathMatcher::Result m = filterValue( context );
	if( m & PathMatcher::DescendantMatch )
	{
		outPlug()->childBoundsPlug()->hash( h );
	}

	if( m & PathMatcher::ExactMatch )
	{
		outPlug()->objectPlug()->hash( h );
	}
}

Imath::Box3f MotionPath::computeBound( const ScenePath &path, const Context *context, const ScenePlug *parent ) const
{
	if( !adjustBoundsPlug()->getValue() )
	{
		return inPlug()->boundPlug()->getValue();
	}

	Imath::Box3f result;

	const PathMatcher::Result m = filterValue( context );
	if( m & PathMatcher::DescendantMatch )
	{
		result = outPlug()->childBoundsPlug()->getValue();
	}

	if( m & PathMatcher::ExactMatch )
	{
		if( ConstCurvesPrimitivePtr motionPath = runTimeCast<const CurvesPrimitive>( outPlug()->objectPlug()->getValue() ) )
		{
			result.extendBy( SceneAlgo::bound( motionPath.get() ) );
		}
	}

	return result;
}

void MotionPath::hashTransform( const ScenePath &path, const Context *context, const ScenePlug *parent, MurmurHash &h ) const
{
	h = inPlug()->transformPlug()->defaultHash();
}

Imath::M44f MotionPath::computeTransform( const ScenePath &path, const Context *context, const ScenePlug *parent ) const
{
	return inPlug()->transformPlug()->defaultValue();
}

void MotionPath::hashAttributes( const ScenePath &path, const Context *context, const ScenePlug *parent, MurmurHash &h ) const
{
	h = inPlug()->attributesPlug()->defaultHash();
}

ConstCompoundObjectPtr MotionPath::computeAttributes( const ScenePath &path, const Context *context, const ScenePlug *parent ) const
{
	return inPlug()->attributesPlug()->defaultValue();
}

void MotionPath::hashObject( const ScenePath &path, const Context *context, const ScenePlug *parent, MurmurHash &h ) const
{
	if( !(filterValue( context ) & PathMatcher::ExactMatch) )
	{
		h = inPlug()->objectPlug()->defaultHash();
		return;
	}

	FilteredSceneProcessor::hashObject( path, context, parent, h );

	h.append( inPlug()->fullTransformHash( path ) );

	h.append( context->getFrame() );

	startModePlug()->hash( h );
	startFramePlug()->hash( h );
	endModePlug()->hash( h );
	endFramePlug()->hash( h );
	samplingModePlug()->hash( h );
	stepPlug()->hash( h );
	samplesPlug()->hash( h );
}

ConstObjectPtr MotionPath::computeObject( const ScenePath &path, const Context *context, const ScenePlug *parent ) const
{
	if( !(filterValue( context ) & PathMatcher::ExactMatch) )
	{
		return inPlug()->objectPlug()->defaultValue();
	}

	float start = ( (FrameMode)startModePlug()->getValue() == FrameMode::Absolute ) ? startFramePlug()->getValue() : context->getFrame() + startFramePlug()->getValue();
	float end = ( (FrameMode)endModePlug()->getValue() == FrameMode::Absolute ) ? endFramePlug()->getValue() : context->getFrame() + endFramePlug()->getValue();
	if( start >= end )
	{
		return inPlug()->objectPlug()->defaultValue();
	}

	float step = 0;
	int samples = 0;
	if( (SamplingMode)samplingModePlug()->getValue() == SamplingMode::Variable )
	{
		step = stepPlug()->getValue();
		samples = ceil( ( end - start ) / step - 1e-6 ) + 1;
	}
	else
	{
		samples = samplesPlug()->getValue();
		step = ( end - start ) / ( samples - 1 );
	}

	V3fVectorDataPtr points = new V3fVectorData;
	points->setInterpretation( GeometricData::Point );
	auto &p = points->writable();
	p.reserve( samples );

	QuatfVectorDataPtr orientations = new QuatfVectorData;
	auto &orients = orientations->writable();
	orients.reserve( samples );

	V3fVectorDataPtr scaleData = new V3fVectorData;
	auto &scales = scaleData->writable();
	scales.reserve( samples );

	FloatVectorDataPtr sampleFrames = new FloatVectorData;
	auto &frames = sampleFrames->writable();
	frames.reserve( samples );

	Imath::V3f s;
	Imath::V3f h;
	Imath::Eulerf r;
	Imath::V3f t;

	Context::EditableScope scope( context );
	for( int i = 0; i < samples - 1; ++i )
	{
		float f = start + step * i;
		scope.setFrame( f );
		Imath::extractSHRT( inPlug()->fullTransform( path ), s, h, r, t );
		p.emplace_back( t );
		orients.emplace_back( r.toQuat() );
		scales.emplace_back( s );
		frames.emplace_back( f );
	}

	scope.setFrame( end );
	Imath::extractSHRT( inPlug()->fullTransform( path ), s, h, r, t );
	p.emplace_back( t );
	orients.emplace_back( r.toQuat() );
	scales.emplace_back( s );
	frames.emplace_back( end );

	CurvesPrimitivePtr motionPath = new CurvesPrimitive( new IntVectorData( { (int)p.size() } ), CubicBasisf::linear(), false, points );
	motionPath->variables["orientation"] = PrimitiveVariable( PrimitiveVariable::Vertex, orientations );
	motionPath->variables["scale"] = PrimitiveVariable( PrimitiveVariable::Vertex, scaleData );
	motionPath->variables["frame"] = PrimitiveVariable( PrimitiveVariable::Vertex, sampleFrames );
	return motionPath;
}

void MotionPath::hashSetNames( const Context *context, const ScenePlug *parent, MurmurHash &h ) const
{
	FilteredSceneProcessor::hashSetNames( context, parent, h );

	isolatedInPlug()->setNamesPlug()->hash( h );
}

ConstInternedStringVectorDataPtr MotionPath::computeSetNames( const Context *context, const ScenePlug *parent ) const
{
	ConstInternedStringVectorDataPtr setNames = isolatedInPlug()->setNamesPlug()->getValue();

	InternedStringVectorDataPtr result = new InternedStringVectorData;
	for( auto &setName : setNames->readable() )
	{
		if( setName == g_camerasSetName || setName == g_lightsSetName || setName == g_defaultLightsSetName )
		{
			continue;
		}

		result->writable().emplace_back( setName );
	}

	return result;
}

void MotionPath::hashSet( const InternedString &setName, const Context *context, const ScenePlug *parent, MurmurHash &h ) const
{
	if( setName == g_camerasSetName || setName == g_lightsSetName || setName == g_defaultLightsSetName )
	{
		h = inPlug()->setPlug()->defaultHash();
	}
	else
	{
		h = isolatedInPlug()->setPlug()->hash();
	}
}

ConstPathMatcherDataPtr MotionPath::computeSet( const InternedString &setName, const Context *context, const ScenePlug *parent ) const
{
	if( setName == g_camerasSetName || setName == g_lightsSetName || setName == g_defaultLightsSetName )
	{
		return outPlug()->setPlug()->defaultValue();
	}

	return isolatedInPlug()->setPlug()->getValue();
}
