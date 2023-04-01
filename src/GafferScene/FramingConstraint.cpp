//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2023, Image Engine Design Inc. All rights reserved.
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

#include "GafferScene/FramingConstraint.h"

#include "GafferScene/SceneAlgo.h"

#include "Gaffer/StringPlug.h"

#include "IECoreScene/Camera.h"

#include "fmt/format.h"

#include <algorithm>
#include <cassert>
#include <cmath>
#include <limits>

using namespace Imath;
using namespace IECore;
using namespace Gaffer;
using namespace GafferScene;

GAFFER_NODE_DEFINE_TYPE( FramingConstraint );

size_t FramingConstraint::g_firstPlugIndex = 0;

FramingConstraint::FramingConstraint( const std::string &name )
	:	SceneElementProcessor( name, IECore::PathMatcher::NoMatch )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new ScenePlug( "targetScene" ) );
	addChild( new StringPlug( "target" ) );
	addChild( new BoolPlug( "ignoreMissingTarget" ) );
	addChild( new StringPlug( "boundMode", Plug::In, "sphere" ) );
	addChild( new FloatPlug( "padding" ) );
	addChild( new BoolPlug( "extendFarClip", Plug::In, true ) );
	addChild( new BoolPlug( "useTargetFrame" ) );
	addChild( new FloatPlug( "targetFrame" ) );

	addChild( new ObjectVectorPlug( "__transformAndObject", Plug::Out, new ObjectVector ) );

	// Pass through things we don't want to modify
	outPlug()->attributesPlug()->setInput( inPlug()->attributesPlug() );
}

FramingConstraint::~FramingConstraint()
{
}

ScenePlug *FramingConstraint::targetScenePlug()
{
	return getChild<ScenePlug>( g_firstPlugIndex );
}

const ScenePlug *FramingConstraint::targetScenePlug() const
{
	return getChild<ScenePlug>( g_firstPlugIndex );
}

Gaffer::StringPlug *FramingConstraint::targetPlug()
{
	return getChild<Gaffer::StringPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::StringPlug *FramingConstraint::targetPlug() const
{
	return getChild<Gaffer::StringPlug>( g_firstPlugIndex + 1 );
}

Gaffer::BoolPlug *FramingConstraint::ignoreMissingTargetPlug()
{
	return getChild<Gaffer::BoolPlug>( g_firstPlugIndex + 2 );
}

const Gaffer::BoolPlug *FramingConstraint::ignoreMissingTargetPlug() const
{
	return getChild<Gaffer::BoolPlug>( g_firstPlugIndex + 2 );
}

Gaffer::StringPlug *FramingConstraint::boundModePlug()
{
	return getChild<Gaffer::StringPlug>( g_firstPlugIndex + 3 );
}

const Gaffer::StringPlug *FramingConstraint::boundModePlug() const
{
	return getChild<Gaffer::StringPlug>( g_firstPlugIndex + 3 );
}

Gaffer::FloatPlug *FramingConstraint::paddingPlug()
{
	return getChild<Gaffer::FloatPlug>( g_firstPlugIndex + 4 );
}

const Gaffer::FloatPlug *FramingConstraint::paddingPlug() const
{
	return getChild<Gaffer::FloatPlug>( g_firstPlugIndex + 4 );
}

Gaffer::BoolPlug *FramingConstraint::extendFarClipPlug()
{
	return getChild<Gaffer::BoolPlug>( g_firstPlugIndex + 5 );
}

const Gaffer::BoolPlug *FramingConstraint::extendFarClipPlug() const
{
	return getChild<Gaffer::BoolPlug>( g_firstPlugIndex + 5 );
}

Gaffer::BoolPlug *FramingConstraint::useTargetFramePlug()
{
	return getChild<Gaffer::BoolPlug>( g_firstPlugIndex + 6 );
}

const Gaffer::BoolPlug *FramingConstraint::useTargetFramePlug() const
{
	return getChild<Gaffer::BoolPlug>( g_firstPlugIndex + 6 );
}

Gaffer::FloatPlug *FramingConstraint::targetFramePlug()
{
	return getChild<Gaffer::FloatPlug>( g_firstPlugIndex + 7 );
}

const Gaffer::FloatPlug *FramingConstraint::targetFramePlug() const
{
	return getChild<Gaffer::FloatPlug>( g_firstPlugIndex + 7 );
}

Gaffer::ObjectVectorPlug *FramingConstraint::transformAndObjectPlug()
{
	return getChild<Gaffer::ObjectVectorPlug>( g_firstPlugIndex + 8 );
}

const Gaffer::ObjectVectorPlug *FramingConstraint::transformAndObjectPlug() const
{
	return getChild<Gaffer::ObjectVectorPlug>( g_firstPlugIndex + 8 );
}

void FramingConstraint::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	SceneElementProcessor::affects( input, outputs );

	if(
		input == targetScenePlug()->transformPlug() ||
		input == targetScenePlug()->boundPlug() ||
		input == targetScenePlug()->existsPlug() ||
		input == inPlug()->transformPlug() ||
		input == inPlug()->boundPlug() ||
		input == inPlug()->existsPlug() ||
		input == inPlug()->objectPlug() ||
		input == inPlug()->globalsPlug() ||
		input == targetPlug() ||
		input == ignoreMissingTargetPlug() ||
		input == boundModePlug() ||
		input == paddingPlug() ||
		input == extendFarClipPlug() ||
		input == useTargetFramePlug() ||
		input == targetFramePlug()
	)
	{
		outputs.push_back( transformAndObjectPlug() );
	}

	if( input == transformAndObjectPlug() )
	{
		outputs.push_back( outPlug()->transformPlug() );
		outputs.push_back( outPlug()->objectPlug() );
	}
}

// This is the one piece of functionality we share with Constraint - since we otherwise differ
// substantially, and affect the object as well as the transform, I've just copied it, rather than
// trying to share it
std::optional<FramingConstraint::Target> FramingConstraint::target() const
{
	std::string targetPathAsString = targetPlug()->getValue();
	if( targetPathAsString == "" )
	{
		return std::nullopt;
	}

	ScenePath targetPath;
	ScenePlug::stringToPath( targetPathAsString, targetPath );

	const ScenePlug *targetScene = targetScenePlug();
	if( !targetScene->getInput() )
	{
		// Default to using the main input if no specific `targetScene` plug
		// has been connected
		targetScene = inPlug();
	}

	if( !targetScene->exists( targetPath ) )
	{
		if( ignoreMissingTargetPlug()->getValue() )
		{
			return std::nullopt;
		}
		else
		{
			throw IECore::Exception( fmt::format(
				"FramingConstraint target does not exist: \"{}\". Use 'ignoreMissingTarget' option if you want to just skip this constraint",
				targetPathAsString
			) );
		}
	}

	return Target( { targetPath, targetScene } );
}

namespace
{

// Multiplies a vector by the transpose of the upper left 3x3 portion of a 4x4 matrix.
// Saves allocating a transposed matrix before multiplying, and makes the code a little bit more concise anyway
// ( It feels rather annoying that multDirMatrix doesn't return a value )
V3f multDirM44fTransposed( const M44f &m, const V3f &v )
{
	return V3f(
		m[0][0] * v[0] + m[0][1] * v[1] + m[0][2] * v[2],
		m[1][0] * v[0] + m[1][1] * v[1] + m[1][2] * v[2],
		m[2][0] * v[0] + m[2][1] * v[1] + m[2][2] * v[2]
	);
}

// Computes the signed distances from a set of planes to each of the corners of a box.
// The planes are given by a shared origin, and a normal for each plane.
// Can return the minimum and/or maximum distances from each planes depending on which
// result pointer is non-null
inline void planeDistsFromBox(
	const Box3f &box, const M44f &boxTransform,
	const V3f &planeOrigin, std::vector< V3f > &planeNormals,
	std::vector<float> *minDists, std::vector<float> *maxDists
)
{
	// Convert the plane normals into the space of the box
	std::vector<V3f> boxSpaceNormals;
	boxSpaceNormals.reserve( planeNormals.size() );

	for( const V3f &n : planeNormals )
	{
		boxSpaceNormals.push_back( multDirM44fTransposed( boxTransform, n ) );
	}

	// Initialize result vectors
	if( minDists )
	{
		minDists->resize( planeNormals.size(), std::numeric_limits<float>::infinity() );
	}

	if( maxDists )
	{
		maxDists->resize( planeNormals.size(), -std::numeric_limits<float>::infinity() );
	}

	// Visit the 8 corners of the box. Note: if we use this somewhere performance critical in the future,
	// should probably unroll it
	for( int c = 0; c < 8; c++ )
	{
		V3f corner(
			( c & 1 ) ? box.min.x : box.max.x,
			( c & 2 ) ? box.min.y : box.max.y,
			( c & 4 ) ? box.min.z : box.max.z
		);

		for( unsigned int i = 0; i < planeNormals.size(); i++ )
		{
			// Dot each corner with each plane normal and compare to the appropriate result
			float dot = boxSpaceNormals[i].dot( corner );
			if( minDists )
			{
				(*minDists)[i] = std::min( (*minDists)[i], dot );
			}

			if( maxDists )
			{
				(*maxDists)[i] = std::max( (*maxDists)[i], dot );
			}
		}
	}

	// Add an offset to all results to account for the transform of the boxes origin
	V3f boxOriginWorld = boxTransform.translation();
	for( unsigned int i = 0; i < planeNormals.size(); i++ )
	{
		float dot = planeNormals[i].dot( boxOriginWorld - planeOrigin );
		if( minDists )
		{
			(*minDists)[i] += dot;
		}

		if( maxDists )
		{
			(*maxDists)[i] += dot;
		}
	}
}

// The same signature as planeDistsFromBox, except for a sphere specified by a center point and a
// a point on the surface of the sphere
inline void planeDistsFromSphere(
	const V3f &center, const V3f &pointOnSurface, const M44f &sphereTransform,
	const V3f &planeOrigin, std::vector< V3f > &planeNormals,
	std::vector<float> *minDists, std::vector<float> *maxDists
)
{
	V3f worldCenter = center * sphereTransform;
	float radius = ( pointOnSurface * sphereTransform - worldCenter ).length();

	V3f disp = worldCenter - planeOrigin;

	if( minDists )
	{
		minDists->resize( planeNormals.size() );
	}

	if( maxDists )
	{
		maxDists->resize( planeNormals.size() );
	}

	for( unsigned int i = 0; i < planeNormals.size(); i++ )
	{
		float dot = planeNormals[i].dot( disp );
		float scaledRad = radius * planeNormals[i].length();
		if( minDists )
		{
			(*minDists)[i] = dot - scaledRad;
		}

		if( maxDists )
		{
			(*maxDists)[i] = dot + scaledRad;
		}
	}
}

// Set an ObjectVector plug to store a transform and object
void setTransformAndObject( Gaffer::ValuePlug *output, const M44f &transform, const IECore::Object *object )
{
	ObjectVectorPtr result = new ObjectVector();
	result->members().resize( 2 );
	result->members()[0] = new M44fData( transform );
	// const_cast is safe because the resulting ObjectVector as a whole is treated as const
	result->members()[1] = const_cast< IECore::Object *>( object );

	static_cast<ObjectVectorPlug *>( output )->setValue( result );
}

} // namespace

void FramingConstraint::hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	SceneElementProcessor::hash( output, context, h );
	if( output != transformAndObjectPlug() )
	{
		return;
	}

	inPlug()->transformPlug()->hash( h );
	const ScenePath &path = context->get<ScenePath>( ScenePlug::scenePathContextName );
	const ScenePath parentPath( path.begin(), path.end() - 1 );
	h.append( inPlug()->fullTransformHash( parentPath ) );

	inPlug()->objectPlug()->hash( h );

	{
		std::optional<Context::EditableScope> useFrameScope;
		if( useTargetFramePlug()->getValue() )
		{
			useFrameScope.emplace( context );
			useFrameScope->setFrame( targetFramePlug()->getValue() );
		}

		auto targetOpt = target();
		if( !targetOpt )
		{
			return;
		}

		h.append( targetOpt->scene->fullTransformHash( targetOpt->path ) );
		h.append( targetOpt->scene->boundHash( targetOpt->path ) );
	}

	boundModePlug()->hash( h );
	extendFarClipPlug()->hash( h );
	paddingPlug()->hash( h );

	h.append( inPlug()->globalsHash() );

}

void FramingConstraint::compute( Gaffer::ValuePlug *output, const Gaffer::Context *context ) const
{
	if( output != transformAndObjectPlug() )
	{
		SceneElementProcessor::compute( output, context);
		return;
	}

	// Read the local transform and full transform of the parent separately and combine them to find
	// the world camera transform, because the final camera transform we output needs to be relative
	// to the parent
	M44f cameraTransform = inPlug()->transformPlug()->getValue();
	const ScenePath &path = context->get<ScenePath>( ScenePlug::scenePathContextName );
	const ScenePath parentPath( path.begin(), path.end() - 1 );
	M44f parentTransform = inPlug()->fullTransform( parentPath );
	M44f worldCameraTransform = cameraTransform * parentTransform;

	ConstObjectPtr object = inPlug()->objectPlug()->getValue();
	IECoreScene::ConstCameraPtr camera = IECore::runTimeCast< const IECoreScene::Camera >( object.get() )->copy();

	M44f targetTransform;
	Box3f targetBound;

	{
		std::optional<Context::EditableScope> useFrameScope;
		if( useTargetFramePlug()->getValue() )
		{
			useFrameScope.emplace( context );
			useFrameScope->setFrame( targetFramePlug()->getValue() );
		}

		auto targetOpt = target();
		if( !targetOpt || !camera )
		{
			setTransformAndObject( output, cameraTransform, object.get() );
			return;
		}

		targetTransform = targetOpt->scene->fullTransform( targetOpt->path );
		targetBound = targetOpt->scene->bound( targetOpt->path );
	}


	M44f worldCameraTransformInverse = worldCameraTransform.inverse();

	V3f cameraOriginWorld = worldCameraTransform.translation() ;

	const bool extendFarClip = extendFarClipPlug()->getValue();
	const bool sphereMode = boundModePlug()->getValue() == "sphere";
	const std::string projection = camera->getProjection();

	// When there is padding required, we can scale down the frustum accordingly - in order to frame
	// the object with the smaller frustum, the algorithm will produce more padding
	const float paddingFactor = 1.0f - paddingPlug()->getValue();

	IECoreScene::CameraPtr cameraWithGlobals = camera->copy();
	SceneAlgo::applyCameraGlobals( cameraWithGlobals.get(), inPlug()->globals().get(), inPlug() );
	Box2f frustum = cameraWithGlobals->frustum();

	if( paddingFactor != 1.0f )
	{
		// Shrink based on padding
		frustum = Box2f(
			( frustum.min - frustum.center() ) * paddingFactor + frustum.center(),
			( frustum.max - frustum.center() ) * paddingFactor + frustum.center()
		);
	}


	if( projection == "perspective" )
	{
		// Set up normals for each plane of the frustum. We will measure the closest point on the target
		// to each of these planes, which will determine how far the camera must back up to frame the target.
		std::vector<V3f> frustumPlanes( 6 );
		frustumPlanes[0] = V3f( 1.0f, 0.0, frustum.min.x );
		frustumPlanes[1] = V3f( -1.0f, 0.0, -frustum.max.x );
		frustumPlanes[2] = V3f( 0.0, 1.0f, frustum.min.y );
		frustumPlanes[3] = V3f( 0.0, -1.0f, -frustum.max.y );
		frustumPlanes[4] = V3f( 0.0, 0.0f, 1.0f );
		frustumPlanes[5] = V3f( 0.0, 0.0f, -1.0f );

		// Convert to world space
		std::vector<V3f> frustumPlanesWorld;
		frustumPlanesWorld.reserve( frustumPlanes.size() );
		for( const V3f &n : frustumPlanes )
		{
			frustumPlanesWorld.push_back( multDirM44fTransposed( worldCameraTransformInverse, n ) );
		}

		// Use helper function for box or sphere
		std::vector< float > frustumDistances;
		if( sphereMode )
		{
			planeDistsFromSphere( targetBound.center(), targetBound.max, targetTransform, cameraOriginWorld, frustumPlanesWorld, &frustumDistances, nullptr );
		}
		else
		{
			planeDistsFromBox( targetBound, targetTransform, cameraOriginWorld, frustumPlanesWorld, &frustumDistances, nullptr );
		}

		// Now that we have distances from each frustum plane, we can compute a point in camera space where the
		// x frustum planes intersect, and another point where the y frustum planes intersect
		const V2f frustumSize = frustum.size();
		const V3f xFrustumIntersect = V3f(
			frustumDistances[1] * frustum.min.x + frustumDistances[0] * frustum.max.x,
			0.0f,
			-frustumDistances[1] - frustumDistances[0]
		) / frustumSize.x;

		const V3f yFrustumIntersect = V3f(
			0.0f,
			frustumDistances[3] * frustum.min.y + frustumDistances[2] * frustum.max.y,
			-frustumDistances[3] - frustumDistances[2]
		) / frustumSize.y;

		// Minimum distance needed to make sure target is at least nearClip away
		const float pushClip = camera->getClippingPlanes().x - frustumDistances[5];

		// The Z value for the camera is determined by the maximum of how far back it must be pushed to
		// include the width of the target, how far it must be pushed to include the height of the target,
		// and how far it must be pushed to handle the nearClip
		const float resultZ = std::max( std::max( xFrustumIntersect.z, yFrustumIntersect.z ), pushClip );

		// We now take the x coordinate and y coordinate from the 2 frustum intersect points.
		// When sliding back in depth, we travel in the directiion of the frustum center - this
		// is the one place where we need to explicitly account for cameras with an aperture
		// offset.
		const V3f result(
			xFrustumIntersect.x + frustum.center().x * ( xFrustumIntersect.z - resultZ ),
			yFrustumIntersect.y + frustum.center().y * ( yFrustumIntersect.z - resultZ ),
			resultZ
		);

		// Compute an updated camera world transform
		worldCameraTransform = M44f( M33f(), result ) * worldCameraTransform;

		if( extendFarClip )
		{
			// If extending the far clip, we use the value from the one frustum plane we haven't used yet
			if( camera->getClippingPlanes().y < -frustumDistances[4] + resultZ )
			{
				IECoreScene::CameraPtr newCamera = camera->copy();
				newCamera->setClippingPlanes( V2f( camera->getClippingPlanes().x, -frustumDistances[4] + resultZ ) );
				camera = newCamera;
			}
		}
	}
	else if( projection == "orthographic" )
	{
		// Set up normals for the 3 axis planes. We will measure the closest and farthest point on the target
		// to each of these planes, which will determine the size of frustum required
		std::vector<V3f> camDirs( 3 );
		camDirs[0] = V3f( 1.0f, 0.0, 0.0 );
		camDirs[1] = V3f( 0.0, 1.0f, 0.0 );
		camDirs[2] = V3f( 0.0, 0.0, 1.0f );

		// Convert to world space
		std::vector<V3f> camDirsWorld;
		camDirsWorld.reserve( camDirs.size() );
		for( const V3f &n : camDirs )
		{
			camDirsWorld.push_back( multDirM44fTransposed( worldCameraTransformInverse, n ) );
		}

		std::vector< float > distancesMin;
		std::vector< float > distancesMax;
		if( sphereMode )
		{
			planeDistsFromSphere( targetBound.center(), targetBound.max, targetTransform, cameraOriginWorld, camDirsWorld, &distancesMin, &distancesMax );
		}
		else
		{
			planeDistsFromBox( targetBound, targetTransform, cameraOriginWorld, camDirsWorld, &distancesMin, &distancesMax );
		}

		// Compute an updated camera world transform based on the center of the frustum required
		worldCameraTransform = M44f(
			M33f(),
			V3f(
				( distancesMin[0] + distancesMax[0] ) * 0.5f,
				( distancesMin[1] + distancesMax[1] ) * 0.5f,
				distancesMax[2] + camera->getClippingPlanes().x
			)
		) * worldCameraTransform;

		// Compute how much larger the frustum needs to be. Handling this as an isotropic scaling factor
		// means we preserve the shape of the aperture, and is compatible with how paddingPlug() works
		const float scale = std::max(
			( distancesMax[0] - distancesMin[0] ) / frustum.size().x,
			( distancesMax[1] - distancesMin[1] ) / frustum.size().y
		);

		// Create a camera with the scaled aperture
		IECoreScene::CameraPtr newCamera = camera->copy();
		newCamera->setAperture( camera->getAperture() * scale );
		newCamera->setApertureOffset( V2f( 0.0 ) );

		if( extendFarClip )
		{
			V2f origClip = camera->getClippingPlanes();
			if( origClip.y - origClip.x < distancesMax[2] - distancesMin[2] )
			{
				newCamera->setClippingPlanes( V2f( origClip.x, origClip.x + distancesMax[2] - distancesMin[2] ) );
			}
		}

		camera = newCamera;
	}
	else
	{
		msg( Msg::Warning, "FramingConstraint", "Cannot frame camera using custom projection " + projection );
	}

	setTransformAndObject( output, worldCameraTransform * parentTransform.inverse(), camera.get() );
}

bool FramingConstraint::processesTransform() const
{
	return true;
}

void FramingConstraint::hashProcessedTransform( const ScenePath &path, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	transformAndObjectPlug()->hash( h );
}

Imath::M44f FramingConstraint::computeProcessedTransform( const ScenePath &path, const Gaffer::Context *context, const Imath::M44f &inputTransform ) const
{
	// Just pull the transform from our cache plug
	ConstObjectVectorPtr transformAndObject = transformAndObjectPlug()->getValue();
	assert( transformAndObject->members().size() == 2 );

	M44fData* transformData = IECore::runTimeCast< M44fData >( transformAndObject->members()[0].get() );
	assert( transformData );
	return transformData->readable();
}

bool FramingConstraint::processesObject() const
{
	return true;
}

void FramingConstraint::hashProcessedObject( const ScenePath &path, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	transformAndObjectPlug()->hash( h );
}

IECore::ConstObjectPtr FramingConstraint::computeProcessedObject( const ScenePath &path, const Gaffer::Context *context, IECore::ConstObjectPtr inputObject ) const
{
	// Just pull the object from our cache plug
	ConstObjectVectorPtr transformAndObject = transformAndObjectPlug()->getValue();
	assert( transformAndObject->members().size() == 2 );
	return transformAndObject->members()[1];
}
