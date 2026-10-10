//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2026, Image Engine Design Inc. All rights reserved.
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

#include "GafferSceneUI/PaintTool.h"

// This private class uses a header in /src
#include "DepthRender.h"

#include "GafferSceneUI/SceneView.h"
#include "GafferSceneUI/ScriptNodeAlgo.h"

#include "GafferUI/Pointer.h"
#include "GafferUI/Style.h"

#include "GafferScene/AimConstraint.h"
#include "GafferScene/EditScopeAlgo.h"
#include "GafferScene/PrimitiveVariablePaint.h"

#include "Gaffer/Metadata.h"
#include "Gaffer/MetadataAlgo.h"
#include "Gaffer/ScriptNode.h"

#include "IECoreScene/MeshPrimitive.h"

#include "IECore/DataAlgo.h"
#include "IECore/NullObject.h"

#include "IECoreGL/Buffer.h"
#include "IECoreGL/CachedConverter.h"
#include "IECoreGL/MeshPrimitive.h"
#include "IECoreGL/ShaderLoader.h"

#include "Imath/ImathMatrixAlgo.h"

#include "boost/bind/bind.hpp"

#include "fmt/format.h"

#include <unordered_set>

using namespace std;
using namespace boost::placeholders;
using namespace Imath;
using namespace IECore;
using namespace Gaffer;
using namespace GafferUI;
using namespace GafferScene;
using namespace GafferSceneUI;

//////////////////////////////////////////////////////////////////////////
// Utilities
//////////////////////////////////////////////////////////////////////////

namespace
{

// Given a PaintOperation which may have already been allocated, make sure it is correctly
// allocated for the given value type, number of vertices, and opacity if needed ( but don't
// perform any new allocations if everything is already OK )
void ensurePaintOperationAllocated(
	PrimitiveVariablePaint::PaintOperation &op, IECore::TypeId variableType, size_t numVerts, bool includeOpacity
)
{
	if(
		!op.m_valueData ||
		op.m_valueData->typeId() != variableType
	)
	{
		if( variableType == FloatVectorData::staticTypeId() )
		{
			op.m_valueData = new FloatVectorData();
		}
		else if( variableType == Color3fVectorData::staticTypeId() )
		{
			op.m_valueData = new Color3fVectorData();
		}
		else
		{
			throw IECore::Exception( fmt::format( "Unsupported type for PaintTool : {}", variableType ) );
		}
	}

	if( IECore::size( op.m_valueData.get() ) != numVerts )
	{
		IECore::dispatch(
			op.m_valueData.get(),
			[numVerts]( auto *typedData )
			{
				using DataType = std::remove_pointer_t<decltype( typedData )>;
				if constexpr ( std::is_same_v< DataType, FloatVectorData > || std::is_same_v< DataType, Color3fVectorData > )
				{
					typedData->writable().resize( numVerts, typename DataType::ValueType::value_type( 0 ) );
				}
				else
				{
					throw IECore::Exception( std::string( "Unsupported type " ) + typedData->typeName() );
				}
			}
		);
	}

	if( includeOpacity )
	{
		if( !op.m_opacityData )
		{
			op.m_opacityData = new FloatVectorData();
		}

		if( IECore::size( op.m_opacityData.get() ) != numVerts )
		{
			op.m_opacityData->writable().resize( numVerts, 0.0f );
		}
	}
}

// Given two paint operations, output a new paint operation that applies the combined effect.
// When paintMode is set to Over, the result is equivalent to applying `a` and then `b`.
// When paintMode is set to Erase, the result the parts of `a` covered by `b` will removed.
// The parameter `opacity` is a multiplier on `b` before the composition.
// If outputOpacity is true, then the opacity on the result will be set to the combined opacity.
// Preconditions:
// `a` and `b` have the same valueData type, are the same size, and are both dense, without indices.
// `b` must have value and opacity.
void composePaintOperations( const PrimitiveVariablePaint::PaintOperation &a, const PrimitiveVariablePaint::PaintOperation &b, PaintTool::PaintMode paintMode, float opacity, PrimitiveVariablePaint::PaintOperation &result, bool outputOpacity )
{
	const std::vector<float> &bOpacity = static_cast<const FloatVectorData*>( b.m_opacityData.get() )->readable();

	ensurePaintOperationAllocated( result, b.m_valueData->typeId(), IECore::size( b.m_valueData.get() ), outputOpacity );

	if( !a.m_valueData )
	{
		if( paintMode == PaintTool::PaintMode::Over )
		{
			result.m_valueData->Object::copyFrom( b.m_valueData.get() );
		}
	}
	else
	{
		IECore::dispatch(
			b.m_valueData.get(),
			[&result, &a, &bOpacity, paintMode, opacity]( const auto *typedBValueData )
			{
				using DataType = std::remove_const_t< std::remove_pointer_t<decltype( typedBValueData )> >;
				if constexpr ( std::is_same_v< DataType, FloatVectorData > || std::is_same_v< DataType, Color3fVectorData > )
				{
					const DataType *typedAValueData = IECore::runTimeCast<const DataType>( a.m_valueData.get() );
					if( !typedAValueData )
					{
						throw IECore::Exception( fmt::format(
							"Type mismatch : {} != {}", a.m_valueData->typeName(), typedBValueData->typeName()
						) );
					}

					const auto &aValue = typedAValueData->readable();
					const auto &bValue = typedBValueData->readable();

					DataType* resultValueData = IECore::runTimeCast<DataType >( result.m_valueData.get() );
					auto &resultValue = resultValueData->writable();

					if( paintMode == PaintTool::PaintMode::Erase )
					{
						for( size_t i = 0; i < resultValue.size(); i++ )
						{
							resultValue[i] = ( 1.0f - bOpacity[i] * opacity ) * aValue[i];
						}
					}
					else
					{
						for( size_t i = 0; i < resultValue.size(); i++ )
						{
							resultValue[i] = ( 1.0f - bOpacity[i] * opacity ) * aValue[i] + bValue[i] * opacity;
						}
					}
				}
				else
				{
					throw IECore::Exception( std::string( "Unsupported type " ) + typedBValueData->typeName() );
				}
			}
		);
	}

	if( !outputOpacity )
	{
		return;
	}

	if( !a.m_opacityData )
	{
		if( paintMode == PaintTool::PaintMode::Over )
		{
			result.m_opacityData->Object::copyFrom( b.m_opacityData.get() );
		}
	}
	else
	{
		const std::vector<float> &aOpacity = static_cast<const FloatVectorData*>( a.m_opacityData.get() )->readable();

		if( !result.m_opacityData )
		{
			result.m_opacityData = new FloatVectorData();
		}

		std::vector<float> &resultOpacity = result.m_opacityData->writable();

		if( paintMode == PaintTool::PaintMode::Erase )
		{
			for( size_t i = 0; i < resultOpacity.size(); i++ )
			{
				resultOpacity[i] = ( 1.0f - bOpacity[i] * opacity ) * aOpacity[i];
			}
		}
		else
		{
			for( size_t i = 0; i < resultOpacity.size(); i++ )
			{
				resultOpacity[i] = 1.0f - ( 1.0f - bOpacity[i] * opacity ) * ( 1.0f - aOpacity[i] );
			}
		}
	}
}

// Convert a PaintOperation to a sparse PaintOperation with indices, if omitting the elements where
// value and opacity are zero would save space.
template< class T >
void makeSparsePaintOperation( PrimitiveVariablePaint::PaintOperation &op )
{
	const typename T::ValueType &sourceValues = IECore::runTimeCast<T>( op.m_valueData.get() )->readable();
	const std::vector<float> &sourceOpacities = op.m_opacityData->readable();

	const typename T::ValueType::value_type zeroValue( 0.0f );

	size_t numOccupied = 0;
	for( size_t i = 0; i < sourceValues.size(); i++ )
	{
		if( sourceValues[i] != zeroValue || sourceOpacities[i] != 0.0f )
		{
			numOccupied++;
		}
	}

	constexpr int valueSize = sizeof( typename T::ValueType::value_type );
	if( numOccupied * ( valueSize + sizeof( float ) ) >= sourceValues.size() * valueSize )
	{
		// If converting to sparse and adding indices wouldn't save any size, then
		// just return.
		return;
	}

	typename T::Ptr newValueData = new T;
	FloatVectorDataPtr newOpacityData = new FloatVectorData();
	IntVectorDataPtr newIndicesData = new IntVectorData;

	typename T::ValueType &newValues = newValueData->writable();
	std::vector<float> &newOpacities = newOpacityData->writable();
	std::vector<int> &newIndices = newIndicesData->writable();

	newValues.reserve( numOccupied );
	newOpacities.reserve( numOccupied );
	newIndices.reserve( numOccupied );

	for( size_t i = 0; i < sourceValues.size(); i++ )
	{
		if( sourceValues[i] != zeroValue || sourceOpacities[i] != 0.0f )
		{
			newValues.push_back( sourceValues[i] );
			newOpacities.push_back( sourceOpacities[i] );
			newIndices.push_back( i );
		}
	}

	op.m_valueData = newValueData;
	op.m_opacityData = newOpacityData;
	op.m_indicesData = newIndicesData;
}

// Uniform block structure (std140 layout)
struct UniformBlockColorShader
{
	alignas( 16 ) M44f o2c;
};


// Name of P primitive variable
const std::string g_pName = "P";

const GLuint g_uniformBlockBindingIndex = 0;

#define UNIFORM_BLOCK_COLOR_SHADER_GLSL_SOURCE \
	"layout( std140, row_major ) uniform UniformBlock\n" \
	"{\n" \
	"   mat4 o2c;\n" \
	"} uniforms;\n"

#define ATTRIB_GLSL_LOCATION_PS 0
#define ATTRIB_GLSL_LOCATION_VSX 1
#define ATTRIB_GLSL_LOCATION_VSY 2
#define ATTRIB_GLSL_LOCATION_VSZ 3

#define ATTRIB_COLOR_SHADER_GLSL_SOURCE \
	"layout( location = " BOOST_PP_STRINGIZE( ATTRIB_GLSL_LOCATION_PS ) " ) in vec3 ps;\n" \
	"layout( location = " BOOST_PP_STRINGIZE( ATTRIB_GLSL_LOCATION_VSX ) " ) in float vsx;\n" \
	"layout( location = " BOOST_PP_STRINGIZE( ATTRIB_GLSL_LOCATION_VSY ) " ) in float vsy;\n" \
	"layout( location = " BOOST_PP_STRINGIZE( ATTRIB_GLSL_LOCATION_VSZ ) " ) in float vsz;\n" \


#define INTERFACE_BLOCK_COLOR_SHADER_GLSL_SOURCE( STORAGE, NAME ) \
	BOOST_PP_STRINGIZE( STORAGE ) " InterfaceBlock\n" \
	"{\n" \
	"   smooth vec3 value;\n" \
	"} " BOOST_PP_STRINGIZE( NAME ) ";\n"


// Opengl vertex shader code

const std::string g_colorShaderVertSource(
	"#version 330\n"

	UNIFORM_BLOCK_COLOR_SHADER_GLSL_SOURCE

	ATTRIB_COLOR_SHADER_GLSL_SOURCE

	INTERFACE_BLOCK_COLOR_SHADER_GLSL_SOURCE( out, outputs )

	"void main()\n"
	"{\n"
	"   outputs.value = vec3( vsx, vsy, vsz );\n"
	"   gl_Position = vec4( ps, 1.0 ) * uniforms.o2c;\n"
	"}\n"
);

// Opengl fragment shader code

const std::string g_colorShaderFragSource
(
	"#version 330\n"

	UNIFORM_BLOCK_COLOR_SHADER_GLSL_SOURCE

	INTERFACE_BLOCK_COLOR_SHADER_GLSL_SOURCE( in, inputs )

	"layout( location = 0 ) out vec4 cs;\n"

	"void main()\n"
	"{\n"
	"   cs = vec4( inputs.value, 1.0 );\n"
	"}\n"
);

float frustumWidthFromProjectionMatrix( const Imath::M44f &m )
{
	Imath::M44f mInverse = m;
	mInverse.invert();

	V3f center, deep, side, approxOrigin;
	mInverse.multVecMatrix( Imath::V3f( 0, 0, 1 ), center );
	mInverse.multVecMatrix( Imath::V3f( 1, 0, 1 ), side );
	mInverse.multVecMatrix( Imath::V3f( 0, 0, -1 ), approxOrigin );

	return (side - center ).length() / (approxOrigin - center).length();
}

// Used by LocationCache::paintToCurrentStroke, this performs the actual update of the values corresponding
// to vertices that have been found to be within the brush's influence.
template< class T >
bool applyPaint( T &outValue, float &outOpacity, const T &value, float hardness, const V3f &p, const M44f& localPaintMatrix, int resolution, const float *depthMap, float depthToleranceMult )
{
	V3f brushPos;
	localPaintMatrix.multVecMatrix( p, brushPos );

	float l2 = brushPos.x * brushPos.x + brushPos.y * brushPos.y;
	if( l2 > 1.0f )
	{
		return false;
	}

	float brushShape;
	if( hardness == 1.0f )
	{
		brushShape = l2 <= 1.0f ? 1.0f : 0.0f;
	}
	else
	{
		brushShape = std::min( ( 1 - sqrtf( l2 ) ) / ( 1.0f - hardness ), 1.0f );
	}

	float rasterX = ( brushPos.x * 0.5f + 0.5f ) * ( resolution - 1 );
	float rasterY = ( brushPos.y * 0.5f + 0.5f ) * ( resolution - 1 );

	float iX = std::min( floorf( rasterX ), resolution - 2.0f );
	float iY = std::min( floorf( rasterY ), resolution - 2.0f );

	float lerpX = rasterX - iX;
	float lerpY = rasterY - iY;

	int iiX = iX;
	int iiY = iY;

	float depthMapDepth =
		( depthMap[ iiY * resolution + iiX ] * ( 1.0f - lerpX ) + ( depthMap[ iiY * resolution + iiX + 1 ] * lerpX ) ) * ( 1.0f - lerpY ) +
		( depthMap[ ( iiY + 1 ) * resolution + iiX ] * ( 1.0f - lerpX ) + ( depthMap[ ( iiY + 1 ) * resolution + iiX + 1 ] * lerpX ) ) * lerpY;

	const float lookupDepthApproxLinear = 1.0f / ( -0.5f * brushPos.z + 0.5f );
	const float depthMapDepthApproxLinear = 1.0f / ( 1.0f - depthMapDepth );

	const float depthTolerance = lookupDepthApproxLinear * depthToleranceMult;

	// We fade out the contribution over `depthTolerance`. This fade doesn't start until the depth difference
	// is half of depthTolerance ( we want the mask to be 100% as long as the depth is about right ).
	float depthMask = std::max( 0.0f, std::min( 1.0f, 1.5f + ( depthMapDepthApproxLinear - lookupDepthApproxLinear ) / depthTolerance ) );

	float curOpac = brushShape * depthMask;
	if( curOpac > 0 )
	{
		// \todo : Currently, the color is constant within the stroke, so there's no actual need
		// to store it: outValue[i] is always equal to value * outOpacity[i].
		// There's also an artistic question about whether the composition of each brush instance
		// within the stroke should actually be an `over` like this - if we just did a `max`,
		// that would give different behaviour for the hardness parameter, that might feel
		// more consistent.
		outValue = ( 1.0f - curOpac ) * outValue + curOpac * value;
		outOpacity = 1.0f - ( 1.0f - curOpac ) * ( 1.0f - outOpacity );

		return true;
	}

	return false;
}


// Convert mesh topology to a list of indices that can be used to render triangulated polygons from the
// original data ( We really need to find a way of improving our usual draw code path so it works like this
// rather than triangulating the whole mesh before passing it to GL, but the current API makes that tricky,
// so currently we only get fast drawing for meshes being painted ).
void triangulatedMeshIndices(
	const IECoreScene::MeshPrimitive *mesh,
	IECoreScene::PrimitiveVariable::Interpolation varInterpolation,
	std::vector<int> &newIds,
	const IECore::Canceller *canceller
)
{
	const std::vector<int> &verticesPerFace = mesh->verticesPerFace()->readable();

	newIds.clear();

	int numTris = 0;
	for( auto n : verticesPerFace )
	{
		numTris += n - 2;
	}

	newIds.reserve( numTris * 3 );

	int faceVertexIdStart = 0;
	for( int faceIdx = 0; faceIdx < (int)verticesPerFace.size(); faceIdx++ )
	{
		if( ( faceIdx % 100 ) == 0 )
		{
			IECore::Canceller::check( canceller );
		}

		int numFaceVerts = verticesPerFace[ faceIdx ];

		const int i0 = faceVertexIdStart + 0;

		for( int i = 1; i < numFaceVerts - 1; i++ )
		{
			const int i1 = faceVertexIdStart + i;
			const int i2 = faceVertexIdStart + i + 1;

			/// Store the indices required to rebuild the facevarying primvars
			newIds.push_back( i0 );
			newIds.push_back( i1 );
			newIds.push_back( i2 );
		}

		faceVertexIdStart += numFaceVerts;
	}

	if( varInterpolation == IECoreScene::PrimitiveVariable::Vertex || varInterpolation == IECoreScene::PrimitiveVariable::Varying )
	{
		const std::vector<int> &vertexIds = mesh->vertexIds()->readable();
		for( int &i : newIds )
		{
			i = vertexIds[i];
		}
	}
}

PaintTool::ColorChooserFunction &colorChooserFunction()
{
	// We deliberately make no attempt to free this, because typically a python
	// function is registered here, and we can't free that at exit because python
	// is already shut down by then.
	static PaintTool::ColorChooserFunction *g_colorChooserFunction = new PaintTool::ColorChooserFunction;
	return *g_colorChooserFunction;
}

// This is kinda formatted in such a way it could theoretically be shared with VisualiserTool
void setVertexArrayAttribsForTypeAndComponents( GLenum type, int components )
{
	if( components != 0 )
	{
		glEnableVertexAttribArray( ATTRIB_GLSL_LOCATION_VSX );
		glVertexAttribPointer( ATTRIB_GLSL_LOCATION_VSX, 1, type, GL_FALSE, components * sizeof( GLfloat ), nullptr );
	}
	else
	{
		glDisableVertexAttribArray( ATTRIB_GLSL_LOCATION_VSX );
		glVertexAttrib1f( ATTRIB_GLSL_LOCATION_VSX, 0.f );
	}

	if( components != 0 )
	{
		glEnableVertexAttribArray( ATTRIB_GLSL_LOCATION_VSY );
		glVertexAttribPointer(
			ATTRIB_GLSL_LOCATION_VSY,
			1,
			type,
			GL_FALSE,
			components * sizeof( GLfloat ),
			( void const *)( ( components != 1 ? 1 : 0 ) * sizeof( GLfloat ) )
		);
	}
	else
	{
		glDisableVertexAttribArray( ATTRIB_GLSL_LOCATION_VSY );
		glVertexAttrib1f( ATTRIB_GLSL_LOCATION_VSY, 0.f );
	}

	if( components == 1 || components == 3 )
	{
		glEnableVertexAttribArray( ATTRIB_GLSL_LOCATION_VSZ );
		glVertexAttribPointer(
			ATTRIB_GLSL_LOCATION_VSZ,
			1,
			type,
			GL_FALSE,
			components * sizeof( GLfloat ),
			( void const *)( ( components != 1 ? 2 : 0 ) * sizeof( GLfloat ) )
		);
	}
	else
	{
		glDisableVertexAttribArray( ATTRIB_GLSL_LOCATION_VSZ );
		glVertexAttrib1f( ATTRIB_GLSL_LOCATION_VSZ, 0.f );
	}
}

M44f paintMatrixFromViewport( const ViewportGadget *viewportGadget, const V2f &rasterPos, float toolSize )
{
	return viewportGadget->worldToRasterMatrix() * M44f(
		1.0f / toolSize, 0.0f, 0.0f, 0.0f,
		0.0f, 1.0f / toolSize, 0.0f, 0.0f,
		0.0f, 0.0f, 1.0f, 0.0f,
		-rasterPos.x / toolSize, -rasterPos.y / toolSize, 0.0f, 1.0f
	);
}

// Find Planes matching the frustum of the projection matrix
void frustumPlanes( const M44f &projectionMatrix, std::vector<V3f> &frustumPlaneNormals, std::vector<V3f> &frustumPlaneOrigins )
{

	M44f projInverse = projectionMatrix.inverse();

	// Start by transforming 2 point to get the central direction of projection
	V3f projectionBack, projectionFront;
	projInverse.multVecMatrix( V3f( 0, 0, 1 ), projectionFront );
	projInverse.multVecMatrix( V3f( 0, 0, -1 ), projectionBack );
	V3f projectionDir = ( projectionFront - projectionBack ).normalized();


	// For each of the 4 planes of the frustum, we take a point on the center edge of that plane,
	// shift it forward to get the direction of the plane, and then take the normal as being perpendicular
	// to that direction, in the plane of the central direction.
	std::vector<V3f> frustumPlaneOriginsProjected = { V3f( 1, 0, 0 ), V3f( -1, 0, 0 ), V3f( 0, 1, 0 ), V3f( 0, -1, 0 ) };
	for( V3f &i : frustumPlaneOriginsProjected )
	{
		V3f origin;
		V3f offset;
		projInverse.multVecMatrix( i, origin );
		projInverse.multVecMatrix( i + V3f( 0, 0, 1 ), offset );
		V3f planeDir = offset - origin;
		V3f planePerp = projectionDir.cross( planeDir );

		frustumPlaneOrigins.push_back( origin );
		frustumPlaneNormals.push_back( -planePerp.cross( planeDir ).normalized() );
	}
}

// \todo : At some point, this should probably be unified with ColorInspectorTool's renderCircle2D
// and moved to somewhere central. Currently, a lot of this stuff lives in StandardStyle, but John
// suggests that all the basic drawing stuff should all be moved from StandardStyle to somewhere else.
void renderCircle( const Imath::V2f &pos, float radius )
{
    glBegin( GL_LINE_LOOP );

    const int numDivisions = 100;
    for( int i = 0; i < numDivisions; ++i )
    {
        const float angle = 2 * M_PI * (float)i/(float)(numDivisions-1);
        glVertex2f( radius * cos( angle ) + pos.x, radius * sin( angle ) + pos.y );
    }

    glEnd();
}

} // namespace

//////////////////////////////////////////////////////////////////////////
// PaintTool::LocationCache
//////////////////////////////////////////////////////////////////////////

// Store the all the working data that the paint tool needs at each location
class PaintTool::LocationCache : public Gaffer::Signals::Trackable
{
	public:
		LocationCache( const GafferScene::ScenePlug::ScenePath &path );

		const GafferScene::ScenePlug::ScenePath &path() const;

		// Called by PaintTool::locationCaches before returning a location
		std::string update(
			Private::PrimitiveVariableInspector* inspector,
			const Gaffer::Context *context,
			const std::string &variableName,
			const IECore::TypeId &variableType,
			const ScenePlug *toolScene
		);

		// Whether we can call applyCurrentStroke successfully
		bool editable() const;

		// The DataStore that will be used to edit this location ( or null if there is no DataStore yet )
		const DataStore* paintEdit();

		// If there is a valid mesh at this location ( otherwise we won't try to paint ).
		bool hasMesh() const;

		// Used by PaintGadget::renderPaintVisualiser.
		// Returns all the OpenGL data needed to render the paint at this location.
		// The return tuple contains:
		// meshIndicesGL, meshIndicesSize, meshPosGL, valueBuffer, valueBufferSize, valueBufferComponents
		std::tuple< const IECoreGL::Buffer *, size_t, const IECoreGL::Buffer *, const IECoreGL::Buffer *, size_t, int>
		glBuffers( const std::string &variableName, IECore::TypeId variableType, PaintMode paintMode, float toolOpacity );

		// Add one brush circle to the current stroke. Takes a projection matrix defining the brush's position
		// in world space, the objectTransform of this location, the brush parameters, and a depth map used
		// for occlusion.
		void paintToCurrentStroke(
			const M44f &paintMatrix, const M44f &objectTransform,
			const std::variant<float, Color3f> &value, float hardness,
			int resolution, const float* depthMap
		);

		// Update or create an edit in the given EditScope that applies the current stroke.
		void applyCurrentStroke( EditScope *editScope, const std::string &variableName, PaintMode paintMode, float opacity );

	private :

		// Set an edit in an EditScope. Used by applyCurrentStroke.
		void edit( Gaffer::EditScope *editScope, const std::string &variableName, const GafferScene::PrimitiveVariablePaint::PaintOperation* value );

		// Used by glBuffers.
		void updateGLValueBuffer( const Data *valueData );

		// The path for this location.
		const GafferScene::ScenePlug::ScenePath m_path;

		// A per-vertex value and opacity representing the current brushstroke.
		// This is the only per-location data that we hold uniquely, rather than
		// just caching. m_currentStroke is allocated when we get the first
		// paintToCurrentStroke of a new brushstroke, and freed in
		// applyCurrentStroke ( when the mouse button is released )
		GafferScene::PrimitiveVariablePaint::PaintOperationPtr m_currentStroke;

		// State maintained by update()

		GafferSceneUI::Private::Inspector::ResultPtr m_inspectorResult;

		bool m_editable;

		Gaffer::DataStore* m_paintEdit;

		IECore::MurmurHash m_sourceMeshHash;
		IECoreScene::ConstMeshPrimitivePtr m_sourceMesh;

		IECore::MurmurHash m_initialEditValueHash;
		GafferScene::PrimitiveVariablePaint::ConstPaintOperationPtr m_initialEditValue;

		// Intermediate state used by glBuffers()

		bool m_composedInputValueDirty;
		GafferScene::PrimitiveVariablePaint::PaintOperationPtr m_composedInputValue;
		GafferScene::PrimitiveVariablePaint::PaintOperationPtr m_composedEditValue;
		GafferScene::PrimitiveVariablePaint::PaintOperationPtr m_composedValue;

		// Outputs from glBuffers()

		IECore::MurmurHash m_topologyHashGL;
		size_t m_meshIndicesSize;
		IECoreGL::ConstBufferPtr m_meshIndicesGL;

		IECore::MurmurHash m_meshHashGL;
		IECoreGL::ConstBufferPtr m_meshPosGL;

		bool m_valueBufferDirty;
		IECoreGL::BufferPtr m_valueBuffer;
		size_t m_valueBufferSize;
		int m_valueBufferComponents;

		// State maintained by paintToCurrentStroke

		IECore::MurmurHash m_kdTreeHash;
		IECore::ConstV3fVectorDataPtr m_kdTreePointsData;
		IECore::V3fTree m_kdTree;
};

PaintTool::LocationCache::LocationCache( const GafferScene::ScenePlug::ScenePath &path )
	:	m_path( path ),
		m_editable( false ),
		m_paintEdit( nullptr ),
		m_composedInputValueDirty( true ),
		m_composedInputValue( new PrimitiveVariablePaint::PaintOperation ),
		m_composedEditValue( new PrimitiveVariablePaint::PaintOperation ),
		m_composedValue( new PrimitiveVariablePaint::PaintOperation ),
		m_valueBufferDirty( true ),
		m_valueBufferComponents( 0 )
{
}

const GafferScene::ScenePlug::ScenePath &PaintTool::LocationCache::path() const
{
	return m_path;
}

std::string PaintTool::LocationCache::update(
	Private::PrimitiveVariableInspector *inspector,
	const Context *context,
	const std::string &variableName,
	const IECore::TypeId &variableType,
	const ScenePlug *toolScene
)
{
	ScenePlug::PathScope scope( context, &m_path );
	m_inspectorResult = inspector->inspect();

	m_editable = false;
	std::string warning = "";

	EditScope *editScope = nullptr;

	if( m_inspectorResult )
	{
		if( m_inspectorResult->editScopeInHistory() )
		{
			editScope = m_inspectorResult->editScope();
		}
	}
	else
	{
		warning = fmt::format( "Location not found : \"{}\"", ScenePlug::pathToString( m_path ) );
	}

	if( editScope )
	{
		if( !editScope->enabledPlug()->getValue() )
		{
			warning = fmt::format(
				"EditScope is not enabled : \"{}\"",
				editScope->relativeName( editScope->ancestor<ScriptNode>() )
			);
			editScope = nullptr;
		}
		else
		{
			const GraphComponent *readOnlyReason = EditScopeAlgo::paintEditReadOnlyReason( editScope, variableName );

			if( readOnlyReason )
			{
				warning = fmt::format(
					"{} is locked.",
					readOnlyReason->relativeName( readOnlyReason->ancestor<ScriptNode>() )
				);
			}
			else
			{
				m_editable = true;
			}
		}
	}
	else
	{
		warning = "Target an EditScope in order to create paint.";
	}

	GafferScene::PrimitiveVariablePaint::ConstPaintOperationPtr paintEntry = nullptr;

	if( m_editable && editScope )
	{
		m_paintEdit = EditScopeAlgo::acquirePaintEdit( editScope, variableName, false );

		if( m_paintEdit )
		{
			// \todo : Path not tracked.
			// This should be getting the path from the upstream context, in case the path has been
			// changed in between the viewed node and the paint edit. But Inspector doesn't currently support
			// this for non-plug-based edits, so for now we just assume the path hasn't changed.
			paintEntry = IECore::runTimeCast<const PrimitiveVariablePaint::PaintOperation>(
				m_paintEdit->getEntry( ScenePlug::pathToString( path() ), false )
			);
		}
	}
	else
	{
		m_paintEdit = nullptr;
	}

	const ScenePlug *sourceScene = nullptr;

	if( m_paintEdit )
	{
		const auto &editOutputs = m_paintEdit->outPlug()->outputs();

		// I guess these exceptions don't hurt just in case ... I don't actually see a way to trigger
		// them in the final version of this code, since acquirePaintEdit finds the DataStore from the
		// PrimitiveVariablePaint: if this isn't set up correctly, we never get to this branch because
		// m_paintEdit will be unset.
		if( editOutputs.size() != 1 )
		{
			throw IECore::Exception( "PrimitiveVariablePaint not connected to DataStore as expected, PaintTool doesn't know how to handle this network." );
		}
		const PrimitiveVariablePaint *primVarPaint = IECore::runTimeCast<PrimitiveVariablePaint>( (*editOutputs.begin())->node() );
		if( !primVarPaint )
		{
			throw IECore::Exception( "PrimitiveVariablePaint not connected to DataStore as expected, PaintTool doesn't know how to handle this network." );
		}
		sourceScene = primVarPaint->inPlug();
	}
	else if( editScope && m_editable )
	{
		sourceScene = IECore::runTimeCast<const ScenePlug>( editScope->inPlug() );
	}
	else
	{
		sourceScene = toolScene;
	}

	if( sourceScene->existsPlug()->getValue() )
	{
		IECore::MurmurHash newHash = sourceScene->objectPlug()->hash();
		if( newHash != m_sourceMeshHash )
		{
			m_sourceMesh = IECore::runTimeCast< const IECoreScene::MeshPrimitive>( sourceScene->objectPlug()->getValue( &newHash ) );

			if( !m_sourceMesh )
			{
				warning = fmt::format( "Cannot paint non-mesh : \"{}\"", ScenePlug::pathToString( m_path ) );
			}
			else if( !m_sourceMesh->arePrimitiveVariablesValid() )
			{
				m_sourceMesh = nullptr;
				warning = fmt::format( "Cannot paint mesh with invalid variables : \"{}\"", ScenePlug::pathToString( m_path ) );
			}

			m_sourceMeshHash = newHash;
		}
	}
	else
	{
		m_sourceMesh = nullptr;
		m_sourceMeshHash = IECore::MurmurHash();
	}

	IECore::MurmurHash initialEditValueHash;
	if( paintEntry )
	{
		paintEntry->hash( initialEditValueHash );
	}

	if( m_sourceMesh )
	{
		size_t numVerts = m_sourceMesh->variableSize( IECoreScene::PrimitiveVariable::Interpolation::Vertex );
		initialEditValueHash.append( numVerts );
	}
	initialEditValueHash.append( variableType );

	if( m_initialEditValueHash != initialEditValueHash || !m_initialEditValue )
	{
		if( !m_sourceMesh )
		{
			m_initialEditValue.reset();
		}
		else
		{
			size_t numVerts = m_sourceMesh->variableSize( IECoreScene::PrimitiveVariable::Interpolation::Vertex );

			if( !paintEntry )
			{
				PrimitiveVariablePaint::PaintOperationPtr initialEditValue = new PrimitiveVariablePaint::PaintOperation();
				ensurePaintOperationAllocated( *initialEditValue, variableType, numVerts, true );
				m_initialEditValue = initialEditValue;
			}
			else if( paintEntry->m_indicesData )
			{
				PrimitiveVariablePaint::PaintOperationPtr initialEditValue = new PrimitiveVariablePaint::PaintOperation();
				ensurePaintOperationAllocated( *initialEditValue, variableType, numVerts, true );
				paintEntry->apply( initialEditValue->m_valueData, numVerts );

				const std::vector<int> &sourceIndices = paintEntry->m_indicesData->readable();
				const std::vector<float> &sourceOpacities = paintEntry->m_opacityData->readable();
				std::vector<float> &expandedOpacities = initialEditValue->m_opacityData->writable();
				for( size_t i = 0; i < sourceIndices.size(); i++ )
				{
					expandedOpacities[ sourceIndices[i] ] = sourceOpacities[i];
				}
				m_initialEditValue = initialEditValue;
			}
			else
			{
				m_initialEditValue = paintEntry;
				if( !paintEntry->m_opacityData )
				{
					throw IECore::Exception( "Internal error : stored paint has no opacity" );
				}
			}
		}

		m_initialEditValueHash = initialEditValueHash;
	}

	// These only need to be dirtied if the m_initialEditValueHash has changed, or variableName
	// has changed. But we don't track variableName, and in the important case for performance,
	// m_initialEditValueHash will have changed anyway, so we can just dirty these.
	m_valueBufferDirty = true;
	m_composedInputValueDirty = true;

	if( m_currentStroke )
	{
		m_currentStroke.reset();
		warning = "Internal error : Paint Tool caches invalidated during stroke";
	}

	return warning;
}

bool PaintTool::LocationCache::editable() const
{
	return hasMesh() && m_editable;
}

const DataStore* PaintTool::LocationCache::paintEdit()
{
	return m_paintEdit;
}

bool PaintTool::LocationCache::hasMesh() const
{
	return m_sourceMesh != nullptr;
}

std::tuple< const IECoreGL::Buffer *, size_t, const IECoreGL::Buffer *, const IECoreGL::Buffer *, size_t, int>
PaintTool::LocationCache::glBuffers( const std::string &variableName, IECore::TypeId variableType, PaintMode paintMode, float toolOpacity )
{
	IECore::MurmurHash topologyHash;
	m_sourceMesh->topologyHash( topologyHash );
	if( m_topologyHashGL != topologyHash || !m_meshIndicesGL )
	{

		IntVectorDataPtr meshIndices = new IntVectorData();
		triangulatedMeshIndices( m_sourceMesh.get(), IECoreScene::PrimitiveVariable::Interpolation::Vertex, meshIndices->writable(), nullptr );

		m_meshIndicesSize = meshIndices->readable().size();

		// Get the cached converter from IECoreGL, this is used to convert primitive
		// variable data to opengl buffers which will be shared with the IECoreGL renderer
		m_meshIndicesGL = runTimeCast<const IECoreGL::Buffer>( IECoreGL::CachedConverter::defaultCachedConverter()->convert( meshIndices.get() ) );
		m_topologyHashGL = topologyHash;
	}

	IECore::MurmurHash meshHash;
	m_sourceMesh->hash( meshHash );
	if( m_meshHashGL != meshHash || !m_meshPosGL )
	{
		// Find opengl "P" buffer data
		ConstV3fVectorDataPtr pData = m_sourceMesh->expandedVariableData<V3fVectorData>( g_pName, IECoreScene::PrimitiveVariable::Interpolation::Vertex, true );
		m_meshPosGL = runTimeCast<const IECoreGL::Buffer>( IECoreGL::CachedConverter::defaultCachedConverter()->convert( pData.get() ) );
		m_meshHashGL = meshHash;

		m_composedInputValueDirty = true;
		m_valueBufferDirty = true;
	}

	if( m_valueBufferDirty )
	{
		PrimitiveVariablePaint::PaintOperationPtr initialMeshValue = new PrimitiveVariablePaint::PaintOperation(
			m_sourceMesh->expandedVariableData<Data>( variableName, IECoreScene::PrimitiveVariable::Interpolation::Vertex )
		);

		if( m_currentStroke )
		{
			if( paintMode == PaintMode::Over )
			{
				if( m_composedInputValueDirty )
				{
					composePaintOperations( *initialMeshValue, *m_initialEditValue, PaintMode::Over, 1.0f, *m_composedInputValue, false );
					m_composedInputValueDirty = false;
				}

				composePaintOperations( *m_composedInputValue, *m_currentStroke, PaintMode::Over, toolOpacity, *m_composedValue, false );
			}
			else
			{
				composePaintOperations( *m_initialEditValue, *m_currentStroke, PaintMode::Erase, toolOpacity, *m_composedEditValue, true );

				composePaintOperations( *initialMeshValue, *m_composedEditValue, PaintMode::Over, 1.0f, *m_composedValue, false );

			}
			updateGLValueBuffer( m_composedValue->m_valueData.get() );
		}
		else
		{
			if( m_composedInputValueDirty )
			{

				composePaintOperations( *initialMeshValue, *m_initialEditValue, PaintMode::Over, 1.0f, *m_composedInputValue, true );
				m_composedInputValueDirty = false;
			}
			updateGLValueBuffer( m_composedInputValue->m_valueData.get() );
		}

		m_valueBufferDirty = false;
	}

	return { m_meshIndicesGL.get(), m_meshIndicesSize, m_meshPosGL.get(), m_valueBuffer.get(), m_valueBufferSize, m_valueBufferComponents };
}

void PaintTool::LocationCache::paintToCurrentStroke(
	const M44f &paintMatrix, const M44f &objectTransform,
	const std::variant<float, Color3f> &value, float hardness,
	int resolution, const float* depthMap
)
{
	if( !editable() || !m_sourceMesh )
	{
		return;
	}

	const V3fVectorData *pVarData = m_sourceMesh->variableData<V3fVectorData>( "P", IECoreScene::PrimitiveVariable::Vertex );
	if( !pVarData )
	{
		throw IECore::Exception( "Vertex P prim var required for painting" );
	}

	IECore::MurmurHash pHash;
	pVarData->hash( pHash );
	if( m_kdTreeHash != pHash )
	{
		m_kdTreePointsData = pVarData;

		const auto &kdTreePoints = m_kdTreePointsData->readable();
		m_kdTree.init( kdTreePoints.begin(), kdTreePoints.end(), 100 );
		m_kdTreeHash = pHash;
	}

	size_t numVerts = m_sourceMesh->variableSize( IECoreScene::PrimitiveVariable::Interpolation::Vertex );

	M44f localPaintMatrix = objectTransform * paintMatrix;

	if( !m_currentStroke )
	{
		m_currentStroke = new PrimitiveVariablePaint::PaintOperation();
	}

	IECore::TypeId valueTypeId = std::holds_alternative<float>( value ) ? FloatVectorDataTypeId : Color3fVectorDataTypeId;
	ensurePaintOperationAllocated( *m_currentStroke, valueTypeId, numVerts, true );

	float frustumWidthAtUnitDist = frustumWidthFromProjectionMatrix( localPaintMatrix );


	// Compute a depth tolerance that gives us a similar amount of error in depth to the amount of
	// error in X/Y coming from the current resolution.
	float depthToleranceMult = 1.0f * frustumWidthAtUnitDist / resolution;

	std::vector<V3f> frustumPlaneOrigins;
	std::vector<V3f> frustumPlaneNormals;

	frustumPlanes( localPaintMatrix, frustumPlaneNormals, frustumPlaneOrigins );

	const std::vector<V3f> &pVar = m_kdTreePointsData->readable();
	std::vector<float> &opacity = m_currentStroke->m_opacityData->writable();
	opacity.resize( pVar.size(), 0.0f );
	if( std::holds_alternative<float>( value ) )
	{
		FloatVectorData* valueData = IECore::runTimeCast<FloatVectorData>( m_currentStroke->m_valueData.get() );
		std::vector<float> &valueBuffer = valueData->writable();
		valueBuffer.resize( pVar.size(), float( 0.0f ) );

		bool dirty = false;

		m_kdTree.enclosedPoints(
			frustumPlaneNormals, frustumPlaneOrigins,
			[&pVar, &valueBuffer, &opacity, &value, &hardness, &localPaintMatrix, &resolution, &depthMap, &depthToleranceMult, &dirty]( V3fTree::Iterator pi )
			{
				size_t i = pi - pVar.begin();
				dirty |= applyPaint<float>( valueBuffer[i], opacity[i], std::get<float>( value ), hardness, pVar[i], localPaintMatrix, resolution, depthMap, depthToleranceMult );

			}
		);

		m_valueBufferDirty |= dirty;
	}
	else
	{
		Color3fVectorData* valueData = IECore::runTimeCast<Color3fVectorData>( m_currentStroke->m_valueData.get() );
		std::vector<Color3f> &valueBuffer = valueData->writable();
		valueBuffer.resize( pVar.size(), Color3f( 0.0f ) );

		bool dirty = false;

		m_kdTree.enclosedPoints(
			frustumPlaneNormals, frustumPlaneOrigins,
			[&pVar, &valueBuffer, &opacity, &value, &hardness, &localPaintMatrix, &resolution, &depthMap, &depthToleranceMult, &dirty]( V3fTree::Iterator pi )
			{
				size_t i = pi - pVar.begin();
				dirty |= applyPaint<Color3f>( valueBuffer[i], opacity[i], std::get<Color3f>( value ), hardness, pVar[i], localPaintMatrix, resolution, depthMap, depthToleranceMult );

			}
		);

		m_valueBufferDirty |= dirty;
	}
}

void PaintTool::LocationCache::applyCurrentStroke( EditScope *editScope, const std::string &variableName, PaintMode paintMode, float opacity )
{
	if( !m_currentStroke )
	{
		return;
	}

	// Bake the current stroke together with the current edit value, then apply it as the new edit
	PrimitiveVariablePaint::PaintOperationPtr newVal = new PrimitiveVariablePaint::PaintOperation;
	composePaintOperations( *m_initialEditValue, *m_currentStroke, paintMode, opacity, *newVal, true );

	// Use indices to avoid storing zeros in PaintOperation
	IECore::dispatch(
		newVal->m_valueData.get(),
		[&newVal]( auto *typedData )
		{
			using DataType = std::remove_pointer_t<decltype( typedData )>;
			if constexpr ( std::is_same_v< DataType, FloatVectorData > || std::is_same_v< DataType, Color3fVectorData > )
			{
				makeSparsePaintOperation<DataType>( *newVal );
			}
			else
			{
				throw IECore::Exception( std::string( "Unsupported type " ) + typedData->typeName() );
			}
		}
	);

	edit( editScope, variableName, newVal.get() );

	// Everything from the current stroke is now applied in the edit, and should no longer be layered
	// on top
	m_currentStroke.reset();
}

void PaintTool::LocationCache::edit( EditScope *editScope, const std::string &variableName, const GafferScene::PrimitiveVariablePaint::PaintOperation* value )
{
	if( !editable() )
	{
		throw IECore::Exception( "Selection is not editable" );
	}

	if( !m_paintEdit )
	{
		assert( editScope );

		// If there's no paint edit yet, try creating one
		m_paintEdit = EditScopeAlgo::acquirePaintEdit( editScope, variableName, true );
	}

	if( !m_paintEdit )
	{
		throw IECore::Exception( "Paint Tool : Could not acquire edit." );
	}

	IECore::InternedString pathString( ScenePlug::pathToString( m_path ) );
	m_paintEdit->setEntry( pathString, value );
}

void PaintTool::LocationCache::updateGLValueBuffer( const Data *valueData )
{
	if( const Color3fVectorData *valueColorData = IECore::runTimeCast< const Color3fVectorData >( valueData ) )
	{
		const std::vector<Color3f> &valueColor = valueColorData->readable();

		if( !m_valueBuffer || m_valueBufferComponents != 3 || m_valueBufferSize != valueColor.size() )
		{
			m_valueBufferComponents = 3;
			m_valueBufferSize = valueColor.size();
			m_valueBuffer = new IECoreGL::Buffer( nullptr, valueColor.size() * sizeof( float ) * 3 );
		}

		glBindBuffer( GL_ARRAY_BUFFER, m_valueBuffer->buffer() );
		glBufferSubData( GL_ARRAY_BUFFER, 0, valueColor.size() * sizeof( float ) * 3, &(valueColor[0]) );
	}
	else if( const FloatVectorData *valueFloatData = IECore::runTimeCast< const FloatVectorData >( valueData ) )
	{
		const std::vector<float> &valueFloat = valueFloatData->readable();

		if( !m_valueBuffer || m_valueBufferComponents != 1 || m_valueBufferSize != valueFloat.size() )
		{
			m_valueBufferComponents = 1;
			m_valueBufferSize = valueFloat.size();
			m_valueBuffer = new IECoreGL::Buffer( nullptr, valueFloat.size() * sizeof( float ) );
		}

		glBindBuffer( GL_ARRAY_BUFFER, m_valueBuffer->buffer() );
		glBufferSubData( GL_ARRAY_BUFFER, 0, valueFloat.size() * sizeof( float ), &(valueFloat[0]) );
	}
	else
	{
		m_valueBufferComponents = 0;
		m_valueBufferSize = 0;
		m_valueBuffer = nullptr;
	}
}

//////////////////////////////////////////////////////////////////////////
// The gadget that does the actual opengl drawing of the shaded primitive
//////////////////////////////////////////////////////////////////////////
class PaintTool::PaintGadget : public Gadget
{

	public :

		explicit PaintGadget( const PaintTool &tool, const std::string &name = defaultName<PaintGadget>() ) :
			Gadget( name ),
			m_tool( &tool )
		{
		}

		void resetTool()
		{
			m_tool = nullptr;
		}

		void renderLayer( Gadget::Layer layer, const Style *style, Gadget::RenderReason reason ) const override
		{
			if(
				( layer != Gadget::Layer::MidFront )
				|| Gadget::isSelectionRender( reason )
			)
			{
				return;
			}

			// Check tool reference valid
			if( m_tool == nullptr )
			{
				return;
			}

			if( layer == Gadget::Layer::MidFront )
			{
				renderPaintVisualiser();
			}
		}

	protected:

		Box3f renderBound() const override
		{
			// NOTE : for now just return an infinite box

			Box3f b;
			b.makeInfinite();
			return b;
		}

		unsigned layerMask() const override
		{
			return m_tool ? static_cast< unsigned >( Gadget::Layer::MidFront ) : static_cast< unsigned >( 0 );
		}

	private:

		friend PaintTool;

		void buildShader( IECoreGL::ConstShaderPtr &shader, const std::string &vertSource, const std::string &fragSource ) const
		{
			if( !shader )
			{
				shader = IECoreGL::ShaderLoader::defaultShaderLoader()->create(
					vertSource, std::string(), fragSource
				);
				if( shader )
				{
					const GLuint program = shader->program();
					const GLuint blockIndex = glGetUniformBlockIndex( program, "UniformBlock" );
					if( blockIndex != GL_INVALID_INDEX )
					{
						glUniformBlockBinding( program, blockIndex, g_uniformBlockBindingIndex );
					}
				}
			}
		}

		/// Renders the color visualiser for the given `ViewportGadget`. In general, each visualiser
		/// vary per-object.
		void renderPaintVisualiser() const
		{
			// Get the name of the primitive variable to visualise
			const std::string variableName = m_tool->variableNamePlug()->getValue();
			if( variableName.empty() )
			{
				return;
			}

			const IECore::TypeId variableType = (IECore::TypeId)m_tool->variableTypePlug()->getValue();

			const PaintMode paintMode = (PaintMode)m_tool->modePlug()->getValue();
			float toolOpacity = m_tool->opacityPlug()->getValue();

			buildShader( m_colorShader, g_colorShaderVertSource, g_colorShaderFragSource );

			if( !m_colorShader )
			{
				return;
			}

			GLint uniformBinding;
			glGetIntegerv( GL_UNIFORM_BUFFER_BINDING, &uniformBinding );

			if( !m_colorUniformBuffer )
			{
				GLuint buffer = 0u;
				glGenBuffers( 1, &buffer );
				glBindBuffer( GL_UNIFORM_BUFFER, buffer );
				glBufferData( GL_UNIFORM_BUFFER, sizeof( UniformBlockColorShader ), nullptr, GL_DYNAMIC_DRAW );
				m_colorUniformBuffer.reset( new IECoreGL::Buffer( buffer ) );
			}

			glBindBufferBase( GL_UNIFORM_BUFFER, g_uniformBlockBindingIndex, m_colorUniformBuffer->buffer() );

			UniformBlockColorShader uniforms;

			// Get the world to clip space matrix
			M44f v2c;
			glGetFloatv( GL_PROJECTION_MATRIX, v2c.getValue() );
			M44f modelView;
			glGetFloatv( GL_MODELVIEW_MATRIX, modelView.getValue() );

			const M44f w2c = modelView * v2c;

			const GLboolean depthEnabled = glIsEnabled( GL_DEPTH_TEST );
			if( !depthEnabled )
			{
				glEnable( GL_DEPTH_TEST );
			}

			const GLboolean blendEnabled = glIsEnabled( GL_BLEND );
			if( !blendEnabled )
			{
				glEnable( GL_BLEND );
			}

			// Enable shader program

			GLint shaderProgram;
			glGetIntegerv( GL_CURRENT_PROGRAM, &shaderProgram );
			glUseProgram( m_colorShader->program() );

			// Set opengl vertex attribute array state

			GLint arrayBinding;
			glGetIntegerv( GL_ARRAY_BUFFER_BINDING, &arrayBinding );

			glPushClientAttrib( GL_CLIENT_VERTEX_ARRAY_BIT );

			glVertexAttribDivisor( ATTRIB_GLSL_LOCATION_PS, 0 );
			glEnableVertexAttribArray( ATTRIB_GLSL_LOCATION_PS );

			// Loop through current selection

			const ScenePlug* scene = m_tool->scenePlug();


			Context::Scope scope( m_tool->view()->context() );

			try
			{
				for( auto &l : m_tool->locationCaches() )
				{
					if( !l->hasMesh() )
					{
						continue;
					}

					// Get the object to world transform
					M44f o2w = scene->fullTransform( l->path() );

					// Find opengl named buffer data
					//
					// NOTE : conversion to IECoreGL mesh may generate vertex attributes (eg. "N")
					//        so check named primitive variable exists on IECore mesh primitive.

					auto [ meshIndicesGL, meshIndicesSize, meshPosGL, valueBuffer, valueBufferSize, valueBufferComponents ]
						= l->glBuffers( variableName, variableType, paintMode, toolOpacity );

					// Compute object to clip matrix
					uniforms.o2c = o2w * w2c;

					// Upload opengl uniform block data

					glBufferData( GL_UNIFORM_BUFFER, sizeof( UniformBlockColorShader ), &uniforms, GL_DYNAMIC_DRAW );

					// Draw primitive
					glBindBuffer( GL_ARRAY_BUFFER, meshPosGL->buffer() );
					glVertexAttribPointer( ATTRIB_GLSL_LOCATION_PS, 3, GL_FLOAT, GL_FALSE, 0, nullptr );


					if( valueBuffer )
					{
						glBindBuffer( GL_ARRAY_BUFFER, valueBuffer->buffer() );
					}

					setVertexArrayAttribsForTypeAndComponents( GL_FLOAT, valueBufferComponents );

					IECoreGL::Buffer::ScopedBinding binding( *meshIndicesGL, GL_ELEMENT_ARRAY_BUFFER );
					glDrawElements( GL_TRIANGLES, meshIndicesSize, GL_UNSIGNED_INT, 0 );
				}
			}
			catch( const std::exception &e )
			{
				/// \todo Ideally the GL state would be handled by `IECoreGL::State` and related classes
				/// which would restore the GL state via RAII in the case of exceptions.
				/// But those don't handle everything we need like shader attribute block alignment,
				/// `GL_POLYGON_OFFSET` and more, so we use try / catch blocks throughout this tool.
				IECore::msg( IECore::Msg::Warning, "PaintTool", std::string( "Exception during rendering : " ) + e.what() );
			}

			// Restore opengl state

			glPopClientAttrib();
			glBindBuffer( GL_ARRAY_BUFFER, arrayBinding );
			glBindBuffer( GL_UNIFORM_BUFFER, uniformBinding );

			if( !depthEnabled )
			{
				glDisable( GL_DEPTH_TEST );
			}
			glUseProgram( shaderProgram );
		}

		const PaintTool *m_tool;
		mutable IECoreGL::ConstShaderPtr m_colorShader;
		mutable IECoreGL::ConstBufferPtr m_colorUniformBuffer;
};

class PaintTool::BrushOutline : public GafferUI::Gadget
{

	public :

		BrushOutline()
			: Gadget(), m_pos( 0.0f ), m_radius( 100.0f ), m_hardness( 0.5f ), m_opacity( 1.0f )
		{
		}

		Imath::Box3f bound() const override
		{
			// We draw in raster space so don't have a sensible bound
			return Box3f();
		}

		void setPos( const Imath::V2f &pos )
		{
			m_pos = pos;
			dirty( DirtyType::Render );
		}

		void setBrush( float radius, float hardness )
		{
			m_radius = radius;
			m_hardness = hardness;
			dirty( DirtyType::Render );
		}

		void setOpacity( float opacity )
		{
			m_opacity = opacity;
			dirty( DirtyType::Render );
		}

	protected :

		void renderLayer( Layer layer, const Style *style, RenderReason reason ) const override
		{
			if( layer != Layer::Front )
			{
				return;
			}

			/// \todo Would it make sense for the ViewportGadget to have a way
			/// of adding a child as an overlay, so we didn't have to do the
			/// raster scope bit manually? Maybe that would let us write more reusable
			/// gadgets, which could be used in any space, and we wouldn't need
			/// eventPosition().
			std::optional<ViewportGadget::RasterScope> rasterScope;
			rasterScope.emplace( ancestor<ViewportGadget>() );

			glPushAttrib( GL_CURRENT_BIT | GL_LINE_BIT | GL_ENABLE_BIT );

				if( !isSelectionRender( reason ) )
				{
					glEnable( GL_LINE_SMOOTH );
					glLineWidth( 1.5f );

					glColor4f( 0.0f, 0.0f, 0.0, 1.0f );

					// \todo : We currently need to nender a zero sized rectangle in order to put the
					// style's shader in a default drawing state ( control of this state isn't exposed,
					// since I guess the intention is that functions like renderCircle should be part of
					// the style ).
					style->renderSolidRectangle( Box2f( m_pos, m_pos ) );

					renderCircle( m_pos, std::max( 0.01f, m_hardness ) * m_radius );

					glColor4f( 0.8f, 0.8f, 0.8f, m_opacity );
					renderCircle( m_pos, m_radius );
				}

			glPopAttrib();

		}

		unsigned layerMask() const override
		{
			return (unsigned)Layer::Front;
		}

		Imath::Box3f renderBound() const override
		{
			// We don't have a sensible bound when we're drawing
			// in raster space
			Box3f b;
			b.makeInfinite();
			return b;
		}

	private :

		V2f m_pos;
		float m_radius;
		float m_hardness;
		float m_opacity;

};

//////////////////////////////////////////////////////////////////////////
// PaintTool
//////////////////////////////////////////////////////////////////////////

GAFFER_NODE_DEFINE_TYPE( PaintTool );

PaintTool::ToolDescription<PaintTool, SceneView> PaintTool::g_toolDescription;

size_t PaintTool::g_firstPlugIndex = 0;

PaintTool::PaintTool( SceneView *view, const std::string &name )
	:	SelectionTool( view, name ),
		m_gadget( new PaintGadget( *this ) ),
		m_selectionDirty( true ),
		m_locationCachesDirty( true ),
		m_buttonPressIsOurs( false ),
		m_mergeGroupId( 0 ),
		m_depthRender( std::make_unique<DepthRender>( Imath::V2i( 32, 32 ) ) ),
		m_mouseIn( false ),
		m_mouseMoveMode( MouseMoveMode::Default )
{
	view->viewportGadget()->addChild( m_gadget );
	m_gadget->setVisible( false );

	storeIndexOfNextChild( g_firstPlugIndex );

	addChild( new ScenePlug( "__scene", Plug::In ) );
	addChild( new StringPlug( "variableName", Plug::In, "Cs" ) );
	addChild( new IntPlug( "variableType", Plug::In, Color3fVectorData::staticTypeId() ) );

	addChild( new IntPlug( "mode", Plug::In, (int)PaintMode::Over ) );

	addChild( new FloatPlug( "size", Plug::In, 30.0f, 0.0f ) );
	addChild( new FloatPlug( "floatValue", Plug::In, 1.0f ) );
	addChild( new Color3fPlug( "colorValue", Plug::In, Imath::Color3f( 1.0f ) ) );
	addChild( new Color3fPlug( "colorBackground", Plug::In, Imath::Color3f( 0.0f ) ) );
	addChild( new FloatPlug( "opacity", Plug::In, 1.0f, 0.0f, 1.0f ) );
	addChild( new FloatPlug( "hardness", Plug::In, 0.0f, 0.0f, 1.0f ) );

	scenePlug()->setInput( view->inPlug<ScenePlug>() );

	view->viewportGadget()->keyPressSignal().connect( boost::bind( &PaintTool::keyPress, this, ::_2 ) );
	view->viewportGadget()->keyReleaseSignal().connect( boost::bind( &PaintTool::keyRelease, this, ::_2 ) );
	view->viewportGadget()->enterSignal().connectFront( boost::bind( &PaintTool::enter, this, ::_2 ) );
	view->viewportGadget()->leaveSignal().connectFront( boost::bind( &PaintTool::leave, this, ::_2 ) );
	view->viewportGadget()->mouseMoveSignal().connect( boost::bind( &PaintTool::mouseMove, this, ::_2 ) );
	view->viewportGadget()->buttonPressSignal().connectFront( boost::bind( &PaintTool::buttonPress, this, ::_2 ) );
	view->viewportGadget()->buttonReleaseSignal().connectFront( boost::bind( &PaintTool::buttonRelease, this, ::_2 ) );


	view->viewportGadget()->dragBeginSignal().connect( boost::bind( &PaintTool::dragBegin, this, ::_1, ::_2 ) );
	view->viewportGadget()->dragEnterSignal().connect( boost::bind( &PaintTool::dragEnter, this, ::_1, ::_2 ) );
	view->viewportGadget()->dragMoveSignal().connect( boost::bind( &PaintTool::dragMove, this, ::_2 ) );

	// We connectFront() to dragEndSignal so that we can update the modifier state after a drag that
	// we're not handling ( we return false when it's not our drag, so the correct handler will still run )
	view->viewportGadget()->dragEndSignal().connectFront( boost::bind( &PaintTool::dragEnd, this, ::_2 ) );

	plugDirtiedSignal().connect( boost::bind( &PaintTool::plugDirtied, this, ::_1 ) );
	view->contextChangedSignal().connect( boost::bind( &PaintTool::contextChanged, this ) );

	ScriptNodeAlgo::selectedPathsChangedSignal( view->scriptNode() ).connect( boost::bind( &PaintTool::selectedPathsChanged, this ) );

	Metadata::plugValueChangedSignal().connect( boost::bind( &PaintTool::metadataChanged, this, ::_3 ) );
	Metadata::nodeValueChangedSignal().connect( boost::bind( &PaintTool::metadataChanged, this, ::_2 ) );

	m_brushOutline = new BrushOutline();
	m_brushOutline->setVisible( false );
	view->viewportGadget()->setChild( "__paintBrushOutline", m_brushOutline );

	// Init the brush gadget
	plugDirtied( sizePlug() );

	// Init the inpector
	plugDirtied( variableNamePlug() );
}

PaintTool::~PaintTool()
{
	// NOTE : ensure that the gadget's reference to the tool is reset
	paintGadget()->resetTool();
}

GafferScene::ScenePlug *PaintTool::scenePlug()
{
	return getChild<ScenePlug>( g_firstPlugIndex );
}

const GafferScene::ScenePlug *PaintTool::scenePlug() const
{
	return getChild<ScenePlug>( g_firstPlugIndex );
}

Gaffer::StringPlug *PaintTool::variableNamePlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::StringPlug *PaintTool::variableNamePlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

Gaffer::IntPlug *PaintTool::variableTypePlug()
{
	return getChild<IntPlug>( g_firstPlugIndex + 2 );
}

const Gaffer::IntPlug *PaintTool::variableTypePlug() const
{
	return getChild<IntPlug>( g_firstPlugIndex + 2 );
}

Gaffer::IntPlug *PaintTool::modePlug()
{
	return getChild<IntPlug>( g_firstPlugIndex + 3 );
}

const Gaffer::IntPlug *PaintTool::modePlug() const
{
	return getChild<IntPlug>( g_firstPlugIndex + 3 );
}

Gaffer::FloatPlug *PaintTool::sizePlug()
{
	return getChild<FloatPlug>( g_firstPlugIndex + 4 );
}

const Gaffer::FloatPlug *PaintTool::sizePlug() const
{
	return getChild<FloatPlug>( g_firstPlugIndex + 4 );
}

Gaffer::FloatPlug *PaintTool::floatValuePlug()
{
	return getChild<FloatPlug>( g_firstPlugIndex + 5 );
}

const Gaffer::FloatPlug *PaintTool::floatValuePlug() const
{
	return getChild<FloatPlug>( g_firstPlugIndex + 5 );
}

Gaffer::Color3fPlug *PaintTool::colorValuePlug()
{
	return getChild<Color3fPlug>( g_firstPlugIndex + 6 );
}

const Gaffer::Color3fPlug *PaintTool::colorValuePlug() const
{
	return getChild<Color3fPlug>( g_firstPlugIndex + 6 );
}

Gaffer::Color3fPlug *PaintTool::colorBackgroundPlug()
{
	return getChild<Color3fPlug>( g_firstPlugIndex + 7 );
}

const Gaffer::Color3fPlug *PaintTool::colorBackgroundPlug() const
{
	return getChild<Color3fPlug>( g_firstPlugIndex + 7 );
}

Gaffer::FloatPlug *PaintTool::opacityPlug()
{
	return getChild<FloatPlug>( g_firstPlugIndex + 8 );
}

const Gaffer::FloatPlug *PaintTool::opacityPlug() const
{
	return getChild<FloatPlug>( g_firstPlugIndex + 8 );
}

Gaffer::FloatPlug *PaintTool::hardnessPlug()
{
	return getChild<FloatPlug>( g_firstPlugIndex + 9 );
}

const Gaffer::FloatPlug *PaintTool::hardnessPlug() const
{
	return getChild<FloatPlug>( g_firstPlugIndex + 9 );
}

const std::unordered_set< std::string > &PaintTool::warnings() const
{
	return m_warnings;
}

std::unordered_set< const Gaffer::GraphComponent* > PaintTool::editTargets()
{
	std::unordered_set< const Gaffer::GraphComponent* > result;

	for( const auto &l : locationCaches() )
	{
		if( l->paintEdit() )
		{
			result.insert( l->paintEdit()->parent() );
		}
		else if( view()->editScope() )
		{
			result.insert( view()->editScope() );
		}
	}

	return result;
}

std::map< std::string, const Gaffer::GraphComponent* > PaintTool::editTargetPerPath()
{
    std::map< std::string, const Gaffer::GraphComponent* > result;

    for( const auto &l : locationCaches() )
    {
        const Gaffer::GraphComponent* target = nullptr;
        if( l->paintEdit() )
        {
            target = l->paintEdit()->parent();
        }
        else if( view()->editScope() )
        {
            target = view()->editScope();
        }

        result[ ScenePlug::pathToString( l->path() ) ] = target;
    }

    return result;
}

bool PaintTool::selectionEditable()
{
	LocationCacheVector &locations = locationCaches();

	if( locations.empty() )
	{
		return false;
	}

	for( const auto &e : locations )
	{
		if( !e->editable() )
		{
			return false;
		}
	}
	return true;
}

PaintTool::StatusChangedSignal &PaintTool::statusChangedSignal()
{
	return m_statusChangedSignal;
}

void PaintTool::paint( const IECore::InternedString &variableName, const M44f &paintMatrix, const std::variant<float, Color3f> &value, float opacity, float hardness, PaintMode paintMode )
{
	// \todo : This is currently reliant on the near/far clip set by the user in the viewer in
	// order to get decent depth. If this doesn't prove good enough, we could build a matrix here
	// with a new near/far based the actual depth range of the meshes we're targeting.
	int resolution = 32;
	const M44f paintMatrixPadded = paintMatrix * M44f(
		( resolution - 1.0f ) / resolution, 0.0f, 0.0f, 0.0f,
		0.0f, ( resolution - 1.0f ) / resolution, 0.0f, 0.0f,
		0.0f, 0.0f, 1.0f, 0.0f,
		0.0f, 0.0f, 0.0f, 1.0f
	);

	Context::Scope scope( view()->context() );
	const ScenePlug* scene = scenePlug();

	m_depthRender->startRendering( paintMatrixPadded );

	m_gadget->renderLayer( Gadget::Layer::MidFront, nullptr, Gadget::RenderReason::Draw );

	const float* depthMap = m_depthRender->finishRendering();

	for( auto &l : locationCaches() )
	{
		if( l->hasMesh() )
		{
			l->paintToCurrentStroke(
				paintMatrix, scene->fullTransform( l->path() ),
				value, hardness, resolution, depthMap
			);
		}
	}
}

void PaintTool::applyCurrentStroke()
{
	IECore::InternedString variableName = variableNamePlug()->getValue();
	const PaintMode paintMode = (PaintMode)modePlug()->getValue();
	float opacity = opacityPlug()->getValue();

	UndoScope undoScope( view()->scriptNode(), UndoScope::Enabled, undoMergeGroup() );
	DirtyPropagationScope dirtyPropagationScope;

	for( auto &l : locationCaches() )
	{
		l->applyCurrentStroke( view()->editScope(), variableName, paintMode, opacity );
	}
}


CompoundDataPtr PaintTool::targetVariableTypes()
{
	CompoundDataPtr resultData = new CompoundData;
	auto &result = resultData->writable();

	result["Cs"] = new IntData( Color3fVectorData::staticTypeId() );

	Context::Scope scope( view()->context() );
	for( const auto &l : locationCaches() )
	{
		if( !scenePlug()->exists( l->path() ) )
		{
			continue;
		}

		IECoreScene::ConstPrimitivePtr prim = IECore::runTimeCast< const IECoreScene::Primitive>( scenePlug()->object( l->path() ) );
		if( !prim )
		{
			continue;
		}

		for( const auto &v : prim->variables )
		{
			IECore::TypeId typeId = v.second.data->typeId();

			if( !( typeId == FloatVectorData::staticTypeId() || typeId == Color3fVectorData::staticTypeId() ) )
			{
				// \todo: should we support any more types?
				continue;
			}

			auto existingIt = result.find( v.first );
			if( existingIt == result.end() )
			{
				result[v.first] = new IntData( typeId );
			}
			else
			{
				int &oldTypeId = IECore::runTimeCast<IntData>( existingIt->second )->writable();
				if( oldTypeId != typeId )
				{
					oldTypeId = 0;
				}
			}
		}
	}
	return resultData;
}

void PaintTool::registerColorChooserFunction( ColorChooserFunction f )
{
	colorChooserFunction() = f;
}

std::string PaintTool::undoMergeGroup() const
{
	return fmt::format( "PaintTool{}{}", fmt::ptr( this ), m_mergeGroupId );
}

PaintTool::PaintGadget* PaintTool::paintGadget()
{
	return static_cast<PaintGadget *>( m_gadget.get() );
}

PaintTool::LocationCacheVector &PaintTool::locationCaches()
{
	// We should only be doing scene queries when we're active
	assert( activePlug()->getValue() );

	Context::Scope scope( view()->context() );
	if( m_selectionDirty )
	{
		// Clear the locationCaches.
		m_locationCaches.clear();

		const PathMatcher selectedPaths = ScriptNodeAlgo::getSelectedPaths( view()->scriptNode() );

		std::mutex locationMutex;
		auto locationAddFunctor = [this, &selectedPaths, &locationMutex]( const ScenePlug *scene, const ScenePlug::ScenePath &path )
		{
			const unsigned match = selectedPaths.match( path );
			if( ( match & IECore::PathMatcher::ExactMatch ) || ( match & IECore::PathMatcher::AncestorMatch ) )
			{
				std::unique_lock<std::mutex> locationLock( locationMutex );
				m_locationCaches.push_back( std::make_unique<LocationCache>( path ) );
			}
			return ( match & IECore::PathMatcher::DescendantMatch ) || ( match & IECore::PathMatcher::ExactMatch );
		};

		SceneAlgo::parallelTraverse( scenePlug(), locationAddFunctor );

		m_locationCachesDirty = true;
		m_selectionDirty = false;
	}

	if( m_locationCachesDirty )
	{

		const std::string variableName = variableNamePlug()->getValue();
		const IECore::TypeId variableType = (IECore::TypeId)variableTypePlug()->getValue();

		std::unordered_set<std::string> warnings;

		for( auto &l : m_locationCaches )
		{
			std::string warning = l->update( m_inspector.get(), view()->context(), variableName, variableType, scenePlug() );

			if( !warning.empty() )
			{
				warnings.insert( warning );
			}
		}

		if( warnings != m_warnings )
		{
			m_warnings = warnings;
			statusChangedSignal()( *this );
		}

		m_locationCachesDirty = false;
	}

	return m_locationCaches;
}

const PaintTool::LocationCacheVector &PaintTool::locationCaches() const
{
	if( m_selectionDirty || m_locationCachesDirty )
	{
		throw IECore::Exception( "`locationCaches() const` must not be called unless `locationCaches()` was previously called" );
	}

	return m_locationCaches;
}

void PaintTool::inspectorDirtied()
{
	m_locationCachesDirty = true;
	statusChangedSignal()( *this );
}

void PaintTool::contextChanged()
{
	// Context changes may change the scene hierarchy or transform,
	// which impacts on the selection and handles.
	selectedPathsChanged();
}

void PaintTool::selectedPathsChanged()
{
	if( !m_selectionDirty )
	{
		m_selectionDirty = true;
		statusChangedSignal()( *this );
		updateCursor();
	}
}

void PaintTool::plugDirtied( const Gaffer::Plug *plug )
{
	if( plug == activePlug() )
	{
		bool active = activePlug()->getValue();

		view()->getChild<Plug>( "drawingMode" )->getChild<BoolPlug>( "hideSelected" )->setValue( active );
		if( active )
		{
			m_preRenderConnection = view()->viewportGadget()->preRenderSignal().connect( boost::bind( &PaintTool::preRender, this ) );
			selectedPathsChanged();
			m_gadget->setVisible( true );
		}
		else
		{
			m_preRenderConnection.disconnect();
			m_gadget->setVisible( false );
			m_brushOutline->setVisible( false );
			m_locationCaches.clear();
		}
	}
	else if( plug == scenePlug()->childNamesPlug() )
	{
		selectedPathsChanged();
	}
	else if( plug == variableNamePlug() || plug == variableTypePlug() )
	{
		m_locationCachesDirty = true;

		// \todo : Once we have a framework for non-plug-based editing in inspectors, this should probably be
		// a special PrimitiveVariablePaintInspector that can handle the actual editing, instead of calling
		// EditScopeAlgo directly.
		m_inspector = new Private::PrimitiveVariableInspector( scenePlug(), view()->editScopePlug(), variableNamePlug()->getValue(), Private::PrimitiveVariableInspector::Property::Data );
		m_inspector->dirtiedSignal().connect( boost::bind( &PaintTool::inspectorDirtied, this ) );

		view()->viewportGadget()->renderRequestSignal()(
			view()->viewportGadget()
		);
	}
	else if( plug == sizePlug() || plug == hardnessPlug() )
	{
		m_brushOutline->setBrush( sizePlug()->getValue(), hardnessPlug()->getValue() );
	}
	else if( plug == opacityPlug() )
	{
		m_brushOutline->setOpacity( opacityPlug()->getValue() );
	}
}

void PaintTool::metadataChanged( IECore::InternedString key )
{
	if( !MetadataAlgo::readOnlyAffectedByChange( key ) )
	{
		return;
	}

	// This could effect whether locations are editable
	m_locationCachesDirty = true;
}

void PaintTool::preRender()
{
	// Call the non-const version of locationCaches() to ensure it will be safe to call
	// the const version during rendering.
	// \todo - this is pretty ugly, should we just make the whole of m_locationCaches mutable
	// instead of worrying about tracking any sort of const-ness?
	locationCaches();
}

bool PaintTool::enter( const ButtonEvent &event )
{
	m_mouseIn = true;
	updateCursor();
	return false;
}

bool PaintTool::leave( const ButtonEvent &event )
{
	m_mouseMoveMode = MouseMoveMode::Default;
	m_mouseIn = false;
	updateCursor();
	return false;
}

bool PaintTool::mouseMove( const ButtonEvent &event )
{
	V2f cursorPos( event.line.p1.x, event.line.p1.y );
	if( m_mouseMoveMode == MouseMoveMode::Size )
	{
		float brushCurSize = pow( 2, ( cursorPos.x - m_cursorPos.x ) * 0.03f ) * m_mouseMoveStartValue;
		sizePlug()->setValue( brushCurSize );
	}
	else if( m_mouseMoveMode == MouseMoveMode::Opacity )
	{
		float curOpacity = std::max( 0.0f, std::min( 1.0f, ( cursorPos.x - m_cursorPos.x ) * 0.01f + m_mouseMoveStartValue ) );
		opacityPlug()->setValue( curOpacity );
	}
	else if( m_mouseMoveMode == MouseMoveMode::Hardness )
	{
		float curHardness = std::max( 0.0f, std::min( 1.0f, ( cursorPos.x - m_cursorPos.x ) * 0.03f + m_mouseMoveStartValue ) );
		hardnessPlug()->setValue( curHardness );
	}
	else
	{
		m_cursorPos = cursorPos;
	}

	// \todo - it shouldn't be necessary to update cursor here - we should be tracking
	// any state change that should trigger a cursor update. But this does help get
	// things back in sync if something changes the cursor underneath us without us
	// realizing ( ie. the mouseWheel handler in ViewportGadget ), or the
	// buttons/modifiers gets out of sync ( there is some way this can happen when
	// doing drags inside the overlay ... maybe I should be trying to fix that instead
	// of just hacking around it? )
	m_eventModifiers = event.modifiers;
	m_eventButtons = event.buttons;
	updateCursor();

	m_brushOutline->setPos( m_cursorPos );
	return false;
}

bool PaintTool::buttonPress( const GafferUI::ButtonEvent &event )
{
	m_eventButtons = event.buttons;
	updateCursor();

	if( event.buttons != ButtonEvent::Left || event.modifiers )
	{
		return false;
	}

	if( !activePlug()->getValue() )
	{
		return false;
	}

	if( !selectionEditable() )
	{
		// We're not editable, but we should still consume the event
		return true;
	}

	// If the button press is ours, then subsequent drag events should be treated
	// as painting ( rather than drag-select or panning )
	m_buttonPressIsOurs = true;

	IECore::InternedString variableName = variableNamePlug()->getValue();
	IECore::TypeId variableType = (IECore::TypeId)variableTypePlug()->getValue();
	const PaintMode paintMode = (PaintMode)modePlug()->getValue();

	float opacity = opacityPlug()->getValue();
	float hardness = hardnessPlug()->getValue();
	float toolSize = sizePlug()->getValue();

	V2f rasterPos( event.line.p0.x, event.line.p0.y );
	m_dragPosition = rasterPos;


	std::variant<float, Color3f> value;
	if( variableType == FloatVectorData::staticTypeId() )
	{
		value = floatValuePlug()->getValue();
	}
	else if( variableType == Color3fVectorData::staticTypeId() )
	{
		value = colorValuePlug()->getValue();
	}
	else
	{
		throw IECore::Exception( fmt::format( "PaintTool unsupported type {}", variableType ) );
	}

	M44f paintMatrix = paintMatrixFromViewport( view()->viewportGadget(), rasterPos, toolSize );
	paint( variableName, paintMatrix, value, opacity, hardness, paintMode );

	view()->viewportGadget()->renderRequestSignal()(
		view()->viewportGadget()
	);

	return true;
}

bool PaintTool::buttonRelease( const GafferUI::ButtonEvent &event )
{
	bool ours = m_buttonPressIsOurs;
	if( m_buttonPressIsOurs )
	{
		m_buttonPressIsOurs = false;
		applyCurrentStroke();
		m_mergeGroupId++;
	}

	m_eventButtons = event.buttons;
	updateCursor();

	return ours;
}

bool PaintTool::keyPress( const GafferUI::KeyEvent &event )
{
	m_eventModifiers = event.modifiers;
	updateCursor();
	if( !activePlug()->getValue() )
	{
		return false;
	}

	if( event.key == "Plus" || event.key == "Equal" )
	{
		sizePlug()->setValue( sizePlug()->getValue() + 0.2 );
	}
	else if( event.key == "Minus" || event.key == "Underscore" )
	{
		sizePlug()->setValue( max( sizePlug()->getValue() - 0.2, 0.2 ) );
	}
	else if( event.key == "J" )
	{
		const IECore::TypeId variableType = (IECore::TypeId)variableTypePlug()->getValue();
		if( variableType == FloatVectorData::staticTypeId() )
		{
			colorChooserFunction()( floatValuePlug() );
		}
		else if( variableType == Color3fVectorData::staticTypeId() )
		{
			colorChooserFunction()( colorValuePlug() );
		}
	}
	else if( event.key == "B" )
	{
		if( m_mouseMoveMode != MouseMoveMode::Size )
		{
			m_mouseMoveMode = MouseMoveMode::Size;
			m_mouseMoveStartValue = sizePlug()->getValue();
		}
		return true;
	}
	else if( event.key == "H" )
	{
		if( m_mouseMoveMode != MouseMoveMode::Hardness )
		{
			m_mouseMoveMode = MouseMoveMode::Hardness;
			m_mouseMoveStartValue = hardnessPlug()->getValue();
		}
		return true;
	}
	else if( event.key == "O" )
	{
		if( m_mouseMoveMode != MouseMoveMode::Opacity )
		{
			m_mouseMoveMode = MouseMoveMode::Opacity;
			m_mouseMoveStartValue = opacityPlug()->getValue();
		}
		return true;
	}
	else if( event.key == "G" )
	{
		Color3f temp = colorValuePlug()->getValue();
		colorValuePlug()->setValue( colorBackgroundPlug()->getValue() );
		colorBackgroundPlug()->setValue( temp );
		return true;
	}

	return false;
}

bool PaintTool::keyRelease( const GafferUI::KeyEvent &event )
{
	m_eventModifiers = event.modifiers;
	updateCursor();

	if( event.key == "B" || event.key == "H" || event.key == "O" )
	{
		m_mouseMoveMode = MouseMoveMode::Default;
	}

	return false;
}


IECore::RunTimeTypedPtr PaintTool::dragBegin( GafferUI::Gadget *gadget, const GafferUI::DragDropEvent &event )
{
	if( !m_buttonPressIsOurs )
	{
		return nullptr;
	}

	return gadget;
}

bool PaintTool::dragEnter( const GafferUI::Gadget *gadget, const GafferUI::DragDropEvent &event )
{
	return event.data == gadget;
}

bool PaintTool::dragMove( const GafferUI::DragDropEvent &event )
{
	if( !m_buttonPressIsOurs )
	{
		return false;
	}

	if( event.buttons != ButtonEvent::Left || event.modifiers )
	{
		return false;
	}

	if( !activePlug()->getValue() )
	{
		return false;
	}

	m_brushOutline->setPos( V2f( event.line.p1.x, event.line.p1.y ) );


	V2f end( event.line.p0.x, event.line.p0.y );
	V2f drag = end - m_dragPosition;


	const float toolSize = sizePlug()->getValue();
	const float targetSpacing = std::max( 1.0f, toolSize * 0.333f );

	float dragLength = drag.length();

	int numSamples = std::max( 1, int( ceilf( dragLength / targetSpacing ) ) );

	float opacity = opacityPlug()->getValue();
	float hardness = hardnessPlug()->getValue();
	const PaintMode paintMode = (PaintMode)modePlug()->getValue();

	IECore::InternedString variableName = variableNamePlug()->getValue();

	std::variant<float, Color3f> value;
	int variableType = variableTypePlug()->getValue();
	if( variableType == FloatVectorData::staticTypeId() )
	{
		value = floatValuePlug()->getValue();
	}
	else if( variableType == Color3fVectorData::staticTypeId() )
	{
		value = colorValuePlug()->getValue();
	}
	else
	{
		throw IECore::Exception( fmt::format( "PaintTool unsupported type {}", variableType ) );
	}

	for( int i = 0; i < numSamples; i++ )
	{
		V2f rasterPos = m_dragPosition + drag * float( i + 1 ) / numSamples;
		M44f paintMatrix = paintMatrixFromViewport( view()->viewportGadget(), rasterPos, toolSize );
		paint( variableName, paintMatrix, value, opacity, hardness, paintMode );
	}

	m_dragPosition = end;

	view()->viewportGadget()->renderRequestSignal()(
		view()->viewportGadget()
	);

	return true;
}

bool PaintTool::dragEnd( const GafferUI::DragDropEvent &event )
{
	if( m_buttonPressIsOurs )
	{
		applyCurrentStroke();
		m_buttonPressIsOurs = false;
		m_mergeGroupId++;
	}

	// We don't receive keyPress/keyRelease/mouseMove events during a drag, so we could
	// need to update several things now.
	m_eventModifiers = event.modifiers;
	m_brushOutline->setPos( V2f( event.line.p1.x, event.line.p1.y ) );

	// Buttons in a dragEnd is a special case - the event doesn't tell us the current state
	// of which mouse buttons are held down, the event holds the mouse button state from the start
	// of the drag. All we know is that whichever button started the drag is now released.
	// A reasonable guess is that no buttons are now held down - this works in simple cases at least,
	// where the user doesn't try to trick us with sequences like "Hold middle mouse button, start
	// dragging, begin holding left mouse button, release middle button".

	m_eventButtons = ButtonEvent::Buttons( 0 );
	updateCursor();

	return m_buttonPressIsOurs;
}

void PaintTool::updateCursor()
{
	if( m_mouseIn && activePlug()->getValue() && !m_eventModifiers && !( m_eventButtons & ButtonEvent::Middle || m_eventButtons & ButtonEvent::Right ) )
	{
		if( !selectionEditable() )
		{
			m_brushOutline->setVisible( false );
			Pointer::setCurrent( "notEditable" );
		}
		else if( m_mouseMoveMode != MouseMoveMode::Default )
		{
			m_brushOutline->setVisible( true );
			Pointer::setCurrent( "" );
		}
		else
		{
			m_brushOutline->setVisible( true );
			Pointer::setCurrent( "invisible" );
		}
	}
	else
	{
		m_brushOutline->setVisible( false );
		Pointer::setCurrent( "" );
	}
}
