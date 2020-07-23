//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2014, John Haddon. All rights reserved.
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

#include "GafferScene/Grid.h"

#include "Gaffer/StringPlug.h"

#include "IECoreScene/CurvesPrimitive.h"
#include "IECoreScene/Shader.h"

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace IECoreScene;
using namespace Gaffer;
using namespace GafferScene;

GAFFER_GRAPHCOMPONENT_DEFINE_TYPE( Grid );

size_t Grid::g_firstPlugIndex = 0;
static InternedString g_gridLinesName( "gridLines" );
static InternedString g_centerLinesName( "centerLines" );
static InternedString g_borderLinesName( "borderLines" );

Grid::Grid( const std::string &name )
	:	SceneNode( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );

	addChild( new StringPlug( "name", Plug::In, "grid" ) );
	addChild( new Gaffer::TransformPlug( "transform" ) );

	addChild( new V2fPlug( "dimensions", Plug::In, V2f( 10.0f ), V2f( 0.0f ) ) );
	addChild( new FloatPlug( "spacing", Plug::In, 1.0f, 0.0f ) );

	addChild( new Color3fPlug( "gridColor", Plug::In, Color3f( 0.1 ) ) );
	addChild( new Color3fPlug( "centerColor", Plug::In, Color3f( 0.5 ) ) );
	addChild( new Color3fPlug( "borderColor", Plug::In, Color3f( 0.15 ) ) );

	addChild( new FloatPlug( "gridPixelWidth", Plug::In, 0.25f, 0.01f ) );
	addChild( new FloatPlug( "centerPixelWidth", Plug::In, 1.0f, 0.01f ) );
	addChild( new FloatPlug( "borderPixelWidth", Plug::In, 1.0f, 0.01f ) );

}

Grid::~Grid()
{
}

Gaffer::StringPlug *Grid::namePlug()
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

const Gaffer::StringPlug *Grid::namePlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

Gaffer::TransformPlug *Grid::transformPlug()
{
	return getChild<TransformPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::TransformPlug *Grid::transformPlug() const
{
	return getChild<TransformPlug>( g_firstPlugIndex + 1 );
}

Gaffer::V2fPlug *Grid::dimensionsPlug()
{
	return getChild<V2fPlug>( g_firstPlugIndex + 2 );
}

const Gaffer::V2fPlug *Grid::dimensionsPlug() const
{
	return getChild<V2fPlug>( g_firstPlugIndex + 2 );
}

Gaffer::FloatPlug *Grid::spacingPlug()
{
	return getChild<FloatPlug>( g_firstPlugIndex + 3 );
}

const Gaffer::FloatPlug *Grid::spacingPlug() const
{
	return getChild<FloatPlug>( g_firstPlugIndex + 3 );
}

Gaffer::Color3fPlug *Grid::gridColorPlug()
{
	return getChild<Color3fPlug>( g_firstPlugIndex + 4 );
}

const Gaffer::Color3fPlug *Grid::gridColorPlug() const
{
	return getChild<Color3fPlug>( g_firstPlugIndex + 4 );
}

Gaffer::Color3fPlug *Grid::centerColorPlug()
{
	return getChild<Color3fPlug>( g_firstPlugIndex + 5 );
}

const Gaffer::Color3fPlug *Grid::centerColorPlug() const
{
	return getChild<Color3fPlug>( g_firstPlugIndex + 5 );
}

Gaffer::Color3fPlug *Grid::borderColorPlug()
{
	return getChild<Color3fPlug>( g_firstPlugIndex + 6 );
}

const Gaffer::Color3fPlug *Grid::borderColorPlug() const
{
	return getChild<Color3fPlug>( g_firstPlugIndex + 6 );
}

Gaffer::FloatPlug *Grid::gridPixelWidthPlug()
{
	return getChild<FloatPlug>( g_firstPlugIndex + 7 );
}

const Gaffer::FloatPlug *Grid::gridPixelWidthPlug() const
{
	return getChild<FloatPlug>( g_firstPlugIndex + 7 );
}

Gaffer::FloatPlug *Grid::centerPixelWidthPlug()
{
	return getChild<FloatPlug>( g_firstPlugIndex + 8 );
}

const Gaffer::FloatPlug *Grid::centerPixelWidthPlug() const
{
	return getChild<FloatPlug>( g_firstPlugIndex + 8 );
}

Gaffer::FloatPlug *Grid::borderPixelWidthPlug()
{
	return getChild<FloatPlug>( g_firstPlugIndex + 9 );
}

const Gaffer::FloatPlug *Grid::borderPixelWidthPlug() const
{
	return getChild<FloatPlug>( g_firstPlugIndex + 9 );
}

void Grid::affects( const Plug *input, AffectedPlugsContainer &outputs ) const
{
	SceneNode::affects( input, outputs );

	if( input == namePlug() )
	{
		outputs.push_back( outPlug()->childNamesPlug() );
	}
	else if( transformPlug()->isAncestorOf( input ) )
	{
		outputs.push_back( outPlug()->transformPlug() );
	}
	else if( dimensionsPlug()->isAncestorOf( input ) )
	{
		outputs.push_back( outPlug()->boundPlug() );
		outputs.push_back( outPlug()->objectPlug() );
	}
	else if(
		input == spacingPlug() ||
		input->parent<Plug>() == gridColorPlug() ||
		input->parent<Plug>() == centerColorPlug() ||
		input->parent<Plug>() == borderColorPlug()
	)
	{
		outputs.push_back( outPlug()->objectPlug() );
	}
	else if(
		input == gridPixelWidthPlug() ||
		input == centerPixelWidthPlug() ||
		input == borderPixelWidthPlug()
	)
	{
		outputs.push_back( outPlug()->attributesPlug() );
	}
}

void Grid::hashBound( const SceneNode::ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	if( path.size() == 0 )
	{
		h = parent->childBoundsPlug()->hash();
	}
	else
	{
		SceneNode::hashBound( path, context, parent, h );
		dimensionsPlug()->hash( h );
	}
}

Imath::Box3f Grid::computeBound( const SceneNode::ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	if( path.size() == 0 )
	{
		return parent->childBoundsPlug()->getValue();
	}
	else
	{
		const V2f halfDimensions = dimensionsPlug()->getValue() / 2.0f;
		const V3f d( halfDimensions.x, halfDimensions.y, 0 );
		return Box3f( -d, d );
	}
}

void Grid::hashTransform( const SceneNode::ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	SceneNode::hashTransform( path, context, parent, h );

	if( path.size() == 1 )
	{
		transformPlug()->hash( h );
	}
}

Imath::M44f Grid::computeTransform( const SceneNode::ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	if( path.size() == 1 )
	{
		return transformPlug()->matrix();
	}
	return outPlug()->transformPlug()->defaultValue();
}

void Grid::hashAttributes( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	if( path.size() == 1 )
	{
		SceneNode::hashAttributes( path, context, parent, h );
		return;
	}
	else if( path.size() == 2 )
	{
		SceneNode::hashAttributes( path, context, parent, h );
		if( path.back() == g_gridLinesName )
		{
			gridPixelWidthPlug()->hash( h );
		}
		else if( path.back() == g_centerLinesName )
		{
			centerPixelWidthPlug()->hash( h );
		}
		else if( path.back() == g_borderLinesName )
		{
			borderPixelWidthPlug()->hash( h );
		}
		return;
	}
	h = outPlug()->attributesPlug()->defaultValue()->Object::hash();
}

IECore::ConstCompoundObjectPtr Grid::computeAttributes( const SceneNode::ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	if( path.size() == 1 )
	{
		CompoundObjectPtr result = new CompoundObject;

		/// \todo Remove hardcoded GL-specific attributes,
		/// and consider removing GL line width plugs too.

		result->members()["gl:curvesPrimitive:useGLLines"] = new BoolData( true );

		ShaderPtr shader = new Shader( "Constant", "gl:surface" );
		shader->parameters()["Cs"] = new Color3fData( Color3f( 1 ) );
		result->members()["gl:surface"] = shader;

		return result;
	}
	else if( path.size() == 2 )
	{
		float pixelWidth = 1.0f;
		if( path.back() == g_gridLinesName )
		{
			pixelWidth = gridPixelWidthPlug()->getValue();
		}
		else if( path.back() == g_centerLinesName )
		{
			pixelWidth = centerPixelWidthPlug()->getValue();
		}
		else if( path.back() == g_borderLinesName )
		{
			pixelWidth = borderPixelWidthPlug()->getValue();
		}

		CompoundObjectPtr result = new CompoundObject;
		result->members()["gl:curvesPrimitive:glLineWidth"] = new FloatData( pixelWidth );

		return result;
	}
	return outPlug()->attributesPlug()->defaultValue();
}

void Grid::hashObject( const SceneNode::ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	if( path.size() == 2 )
	{
		SceneNode::hashObject( path, context, parent, h );
		h.append( path.back() );
		dimensionsPlug()->hash( h );
		if( path.back() == g_gridLinesName )
		{
			spacingPlug()->hash( h );
			gridColorPlug()->hash( h );
		}
		else if( path.back() == g_centerLinesName )
		{
			centerColorPlug()->hash( h );
		}
		else if( path.back() == g_borderLinesName )
		{
			borderColorPlug()->hash( h );
		}
	}
	else
	{
		h = outPlug()->objectPlug()->defaultValue()->hash();
	}
}

IECore::ConstObjectPtr Grid::computeObject( const SceneNode::ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	if( path.size() == 2 )
	{
		IntVectorDataPtr vertsPerCurveData = new IntVectorData;
		vector<int> &vertsPerCurve = vertsPerCurveData->writable();

		V3fVectorDataPtr pData = new V3fVectorData;
		pData->setInterpretation( GeometricData::Point );
		vector<V3f> &p = pData->writable();

		bool periodic = false;
		Color3f cs( 1 );

		const V2f halfDimensions = dimensionsPlug()->getValue() / 2.0f;
		if( path.back() == g_gridLinesName )
		{
			const float spacing = spacingPlug()->getValue();
			const V2i n = V2f( halfDimensions / spacing ) - V2f( 0.01 );
			for( int d = 0; d < 2; ++d )
			{
				const int d0 = d;
				const int d1 = d == 0 ? 1 : 0;
				for( int i = -n[d]; i <= n[d]; ++i )
				{
					if( i == 0 )
					{
						continue;
					}
					vertsPerCurve.push_back( 2 );
					V3f e( 0 );
					e[d0] = i * spacing;
					e[d1] = -halfDimensions[d1];
					p.push_back( e );
					e[d1] = halfDimensions[d1];
					p.push_back( e );
				}
			}
			cs = gridColorPlug()->getValue();
		}
		else if( path.back() == g_centerLinesName )
		{
			vertsPerCurve.push_back( 2 );
			p.push_back( V3f( halfDimensions.x, 0, 0 ) );
			p.push_back( V3f( -halfDimensions.x, 0, 0 ) );
			vertsPerCurve.push_back( 2 );
			p.push_back( V3f( 0, halfDimensions.y, 0 ) );
			p.push_back( V3f( 0, -halfDimensions.y, 0 ) );
			cs = centerColorPlug()->getValue();
		}
		else if( path.back() == g_borderLinesName )
		{
			vertsPerCurve.push_back( 4 );
			p.push_back( V3f( -halfDimensions.x, -halfDimensions.y, 0 ) );
			p.push_back( V3f( halfDimensions.x, -halfDimensions.y, 0 ) );
			p.push_back( V3f( halfDimensions.x, halfDimensions.y, 0 ) );
			p.push_back( V3f( -halfDimensions.x, halfDimensions.y, 0 ) );
			periodic = true;
			cs = borderColorPlug()->getValue();
		}

		CurvesPrimitivePtr result = new CurvesPrimitive( vertsPerCurveData, CubicBasisf::linear(), periodic, pData );
		result->variables["Cs"] = PrimitiveVariable( PrimitiveVariable::Constant, new Color3fData( cs ) );
		return result;
	}
	return outPlug()->objectPlug()->defaultValue();
}

void Grid::hashChildNames( const SceneNode::ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	SceneNode::hashChildNames( path, context, parent, h );
	h.append( (uint64_t)path.size() );

	if( path.size() == 0 )
	{
		namePlug()->hash( h );
	}
}

IECore::ConstInternedStringVectorDataPtr Grid::computeChildNames( const SceneNode::ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	if( path.size() <= 1 )
	{
		InternedStringVectorDataPtr resultData = new InternedStringVectorData;
		std::vector<InternedString> &result = resultData->writable();
		if( path.size() == 0 )
		{
			result.push_back( namePlug()->getValue() );
		}
		else
		{
			result.push_back( g_gridLinesName );
			result.push_back( g_centerLinesName );
			result.push_back( g_borderLinesName );
		}
		return resultData;
	}

	return outPlug()->childNamesPlug()->defaultValue();
}

void Grid::hashGlobals( const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	h = outPlug()->globalsPlug()->defaultValue()->Object::hash();
}

IECore::ConstCompoundObjectPtr Grid::computeGlobals( const Gaffer::Context *context, const ScenePlug *parent ) const
{
	return outPlug()->globalsPlug()->defaultValue();
}

void Grid::hashSetNames( const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	h = outPlug()->setNamesPlug()->defaultValue()->Object::hash();

}

IECore::ConstInternedStringVectorDataPtr Grid::computeSetNames( const Gaffer::Context *context, const ScenePlug *parent ) const
{
	return outPlug()->setNamesPlug()->defaultValue();
}

void Grid::hashSet( const IECore::InternedString &setName, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	h = outPlug()->setPlug()->defaultValue()->Object::hash();
}

IECore::ConstPathMatcherDataPtr Grid::computeSet( const IECore::InternedString &setName, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	return outPlug()->setPlug()->defaultValue();
}
