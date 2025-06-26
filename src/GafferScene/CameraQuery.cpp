//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2025, Cinesite VFX Ltd. All rights reserved.
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

#include "GafferScene/CameraQuery.h"

#include "GafferScene/Filter.h"
#include "GafferScene/SceneAlgo.h"
#include "GafferScene/ScenePlug.h"

#include "Gaffer/Metadata.h"
#include "Gaffer/PlugAlgo.h"

#include "IECoreScene/Camera.h"

using namespace std;
using namespace IECore;
using namespace Gaffer;
using namespace GafferScene;

namespace
{

const size_t g_sourcePlugIndex = 0;
const size_t g_valuePlugIndex = 1;
const InternedString g_renderCameraOption( "option:render:camera" );
const InternedString g_renderShutterOption( "option:render:shutter" );
const InternedString g_defaultValue( "defaultValue" );
const InternedString g_source( "source" );
const InternedString g_value( "value" );
const InternedString g_shutter( "shutter" );
const InternedString g_fStop( "fStop" );
const StringDataPtr g_sourceCamera = new StringData( "camera" );
const StringDataPtr g_sourceGlobals = new StringData( "globals" );
const StringDataPtr g_sourceFallback = new StringData( "fallback" );
const StringDataPtr g_sourceNone = new StringData( "none" );

void addChildPlugsToAffectedOutputs( const Gaffer::Plug *plug, Gaffer::DependencyNode::AffectedPlugsContainer &outputs )
{
	if( plug->children().empty() )
	{
		outputs.push_back( plug );
	}
	else
	{
		for( const Gaffer::PlugPtr &child : Gaffer::Plug::OutputRange( *plug ) )
		{
			addChildPlugsToAffectedOutputs( child.get(), outputs );
		}
	}
}

/// Returns the index into the child vector of `parentPlug` that is
/// either the `childPlug` itself or an ancestor of childPlug.
/// Throws an Exception if the `childPlug` is not a descendant of `parentPlug`.
size_t getChildIndex( const Gaffer::Plug *parentPlug, const Gaffer::ValuePlug *descendantPlug )
{
	const GraphComponent *p = descendantPlug;
	while( p )
	{
		if( p->parent() == parentPlug )
		{
			for( size_t i = 0, eI = parentPlug->children().size(); i < eI; ++i )
			{
				if( parentPlug->getChild( i ) == p )
				{
					return i;
				}
			}
		}
		p = p->parent();
	}

	throw IECore::Exception( "CameraQuery : Plug not in hierarchy." );
}

} // namespace

GAFFER_NODE_DEFINE_TYPE( CameraQuery )

size_t CameraQuery::g_firstPlugIndex = 0;

CameraQuery::CameraQuery( const std::string &name )
	:	ComputeNode( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );

	addChild( new ScenePlug( "scene" ) );
	addChild( new IntPlug( "cameraMode", Plug::In, (int)CameraMode::Location, (int)CameraMode::Location, (int)CameraMode::RenderCamera ) );
	addChild( new StringPlug( "location" ) );
	/// \todo See notes in `ShaderQuery::ShaderQuery`.
	addChild( new ArrayPlug( "queries", Plug::In, nullptr, 0, std::numeric_limits<size_t>::max(), Plug::Default, false ) );
	addChild( new ArrayPlug( "out", Plug::Out, nullptr, 0, std::numeric_limits<size_t>::max(), Plug::Default, false ) );
	addChild( new AtomicCompoundDataPlug( "__internalParameters", Plug::Out, new IECore::CompoundData ) );
}

CameraQuery::~CameraQuery()
{
}

GafferScene::ScenePlug *CameraQuery::scenePlug()
{
	return getChild<ScenePlug>( g_firstPlugIndex );
}

const GafferScene::ScenePlug *CameraQuery::scenePlug() const
{
	return getChild<ScenePlug>( g_firstPlugIndex );
}

Gaffer::IntPlug *CameraQuery::cameraModePlug()
{
	return getChild<IntPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::IntPlug *CameraQuery::cameraModePlug() const
{
	return getChild<IntPlug>( g_firstPlugIndex + 1 );
}

Gaffer::StringPlug *CameraQuery::locationPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 2 );
}

const Gaffer::StringPlug *CameraQuery::locationPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 2 );
}

Gaffer::ArrayPlug *CameraQuery::queriesPlug()
{
	return getChild<ArrayPlug>( g_firstPlugIndex + 3 );
}

const Gaffer::ArrayPlug *CameraQuery::queriesPlug() const
{
	return getChild<ArrayPlug>( g_firstPlugIndex + 3 );
}

Gaffer::ArrayPlug *CameraQuery::outPlug()
{
	return getChild<ArrayPlug>( g_firstPlugIndex + 4 );
}

const Gaffer::ArrayPlug *CameraQuery::outPlug() const
{
	return getChild<ArrayPlug>( g_firstPlugIndex + 4 );
}

Gaffer::AtomicCompoundDataPlug *CameraQuery::internalParametersPlug()
{
	return getChild<AtomicCompoundDataPlug>( g_firstPlugIndex + 5 );
}

const Gaffer::AtomicCompoundDataPlug *CameraQuery::internalParametersPlug() const
{
	return getChild<AtomicCompoundDataPlug>( g_firstPlugIndex + 5 );
}

Gaffer::StringPlug *CameraQuery::addQuery( const Gaffer::ValuePlug *plug, const std::string &parameter )
{
	StringPlugPtr childQueryPlug = new StringPlug( "query0" );
	childQueryPlug->setValue( parameter );

	ValuePlugPtr newOutPlug = new ValuePlug( "out0", Plug::Out );
	newOutPlug->addChild( new StringPlug( "source", Plug::Out ) );
	newOutPlug->addChild( plug->createCounterpart( "value", Plug::Out ) );

	outPlug()->addChild( newOutPlug );
	queriesPlug()->addChild( childQueryPlug );

	return childQueryPlug.get();
}

void CameraQuery::removeQuery( Gaffer::StringPlug *plug )
{
	const ValuePlug *oPlug = outPlugFromQuery( plug );

	queriesPlug()->removeChild( plug );
	outPlug()->removeChild( const_cast<ValuePlug *>( oPlug ) );
}

void CameraQuery::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	ComputeNode::affects( input, outputs );

	if( input == cameraModePlug() ||
		( input == locationPlug() && cameraModePlug()->isSetToDefault() ) ||
		input == scenePlug()->existsPlug() ||
		input == scenePlug()->objectPlug() ||
		input == scenePlug()->globalsPlug()
	)
	{
		outputs.push_back( internalParametersPlug() );
	}
	else if( input == internalParametersPlug() )
	{
		addChildPlugsToAffectedOutputs( outPlug(), outputs );
	}
	else if( queriesPlug()->isAncestorOf( input ) )
	{
		const StringPlug *queryPlug = runTimeCast<const StringPlug>( input );
		if( queryPlug == nullptr )
		{
			throw IECore::Exception( "CameraQuery::affects : Query plugs must be \"StringPlug\"" );
		}

		const ValuePlug *valuePlug = valuePlugFromQuery( queryPlug );

		addChildPlugsToAffectedOutputs( valuePlug, outputs );

		outputs.push_back( sourcePlugFromQuery( queryPlug ) );
	}
}

void CameraQuery::hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	if( output == internalParametersPlug() )
	{
		std::string location = "";
		// The globals affect the camera parameters via SceneAlgo::applyCameraGlobals()
		h.append( scenePlug()->globalsHash() );

		h.append( cameraModePlug()->getValue() );
		if( cameraModePlug()->getValue() == (int)CameraMode::RenderCamera )
		{
			if( const auto renderCameraData = scenePlug()->globals()->member<StringData>( g_renderCameraOption ) )
			{
				location = renderCameraData->readable();
			}
		}
		else
		{
			location = locationPlug()->getValue();
		}

		if( !location.empty() )
		{
			const ScenePlug::ScenePath locationPath = ScenePlug::stringToPath( location );
			ScenePlug::PathScope scope( context, &locationPath );
			if( scenePlug()->existsPlug()->getValue() )
			{
				h.append( scenePlug()->objectHash( locationPath ) );
			}
		}
	}
	else if( outPlug()->isAncestorOf( output ) )
	{
		const ValuePlug *oPlug = outPlug( output );

		if( output == oPlug->getChild( g_sourcePlugIndex ) )
		{
			internalParametersPlug()->hash( h );
			const StringPlug *childQueryPlug = queryPlug( output );
			childQueryPlug->hash( h );
		}
		else if(
			oPlug->getChild( g_valuePlugIndex )->isAncestorOf( output ) ||
			output == oPlug->getChild( g_valuePlugIndex )
		)
		{
			internalParametersPlug()->hash( h );
			const StringPlug *childQueryPlug = queryPlug( output );
			childQueryPlug->hash( h );
		}
	}

	ComputeNode::hash( output, context, h );
}

void CameraQuery::compute( Gaffer::ValuePlug *output, const Gaffer::Context *context ) const
{
	if( output == internalParametersPlug() )
	{
		IECore::CompoundDataPtr parameters = new IECore::CompoundData;

		std::string location = "";
		if( cameraModePlug()->getValue() == (int)CameraMode::RenderCamera )
		{
			if( const auto cameraData = scenePlug()->globals()->member<StringData>( g_renderCameraOption ) )
			{
				location = cameraData->readable();
			}
		}
		else
		{
			location = locationPlug()->getValue();
		}

		if( !location.empty() )
		{
			const ScenePlug::ScenePath locationPath = ScenePlug::stringToPath( location );
			ScenePlug::PathScope scope( context, &locationPath );
			if( scenePlug()->existsPlug()->getValue() )
			{
				if( const auto camera = runTimeCast<const IECoreScene::Camera>( scenePlug()->objectPlug()->getValue() ) )
				{
					auto cameraWithGlobals = camera->copy();
					SceneAlgo::applyCameraGlobals( cameraWithGlobals.get(), scenePlug()->globals().get(), scenePlug() );
					for( const auto &p : cameraWithGlobals->parameters() )
					{
						if( p.first == g_fStop || p.first == g_shutter )
						{
							// We handle these specially below.
							continue;
						}

						parameters->writable()[p.first] = new CompoundData( {
							{ g_source, camera->parameters().count( p.first ) ? g_sourceCamera : g_sourceGlobals },
							{ g_value, p.second }
						} );
					}

					// SceneAlgo::applyCameraGlobals overrides fStop to 0.0 if `depthOfField` is False,
					// so we always return the original camera fStop instead.
					parameters->writable()[g_fStop] = new CompoundData( {
						{ g_source, camera->parameters().count( g_fStop ) ? g_sourceCamera : g_sourceFallback },
						{ g_value, new FloatData( camera->getFStop() ) }
					} );

					// SceneAlgo::applyCameraGlobals outputs an absolute shutter value that is dependent on
					// the render:transformBlur and render:deformationBlur options, so we instead
					// perform our own manual fallback through the relative shutter values.
					V2fDataPtr shutterValue;
					StringDataPtr shutterSource;
					if( camera->hasShutter() )
					{
						shutterSource = g_sourceCamera;
						shutterValue = new V2fData( camera->getShutter() );
					}
					else if( auto s = scenePlug()->globals()->member<V2fData>( g_renderShutterOption ) )
					{
						shutterSource = g_sourceGlobals;
						shutterValue = s->copy();
					}
					else
					{
						shutterSource = g_sourceFallback;
						shutterValue = new V2fData( camera->getShutter() );
					}
					parameters->writable()[g_shutter] = new CompoundData( {
						{ g_source, shutterSource },
						{ g_value, shutterValue }
					} );

					// Fall back to default values for all other registered camera parameters.
					for( const auto &target : Metadata::targetsWithMetadata( "parameter:camera:*", g_defaultValue ) )
					{
						const std::string name = target.string().substr( 17 );
						if( !parameters->readable().count( name ) )
						{
							parameters->writable()[name] = new CompoundData( {
								{ g_source, g_sourceFallback },
								{ g_value, Metadata::value( target, g_defaultValue )->copy() }
							} );
						}
					}

					// Create virtual parameters, for convenience these are pre-computed
					// from the camera so they can be later accessed like a regular parameter.
					const Imath::V2f aperture = cameraWithGlobals->getAperture();
					parameters->writable()["apertureAspectRatio"] = new CompoundData( {
						{ g_source, g_sourceCamera },
						{ g_value, new FloatData( aperture[0] / aperture[1] ) }
					} );
					parameters->writable()["fieldOfView"] = new CompoundData( {
						{ g_source, g_sourceCamera },
						{ g_value, new V2fData( cameraWithGlobals->calculateFieldOfView() ) }
					} );
					parameters->writable()["frustum"] = new CompoundData( {
						{ g_source, g_sourceCamera },
						{ g_value, new Box2fData( cameraWithGlobals->frustum() ) }
					} );
				}
			}
		}

		static_cast<AtomicCompoundDataPlug *>( output )->setValue( parameters );
		return;
	}
	else if( outPlug()->isAncestorOf( output ) )
	{
		const ValuePlug *oPlug = outPlug( output );

		const IECore::ConstCompoundDataPtr parameters = internalParametersPlug()->getValue();
		assert( parameters );

		if( output == oPlug->getChild( g_sourcePlugIndex ) )
		{
			const std::string parameterName = queryPlug( output )->getValue();
			std::string source = g_sourceNone->readable();
			if( parameterName.size() )
			{
				CompoundDataMap::const_iterator it = parameters->readable().find( parameterName );
				if( it != parameters->readable().end() )
				{
					if( const auto c = runTimeCast<CompoundData>( it->second.get() ) )
					{
						if( const auto s = runTimeCast<StringData>( c->member( g_source ) ) )
						{
							source = s->readable();
						}
					}
				}
			}

			static_cast<StringPlug *>( output )->setValue( source );
			return;
		}

		const ValuePlug *valuePlug = oPlug->getChild<ValuePlug>( g_valuePlugIndex );
		if( output == valuePlug || valuePlug->isAncestorOf( output ) )
		{
			const StringPlug *childQueryPlug = queryPlug( output );

			const std::string parameterName = childQueryPlug->getValue();
			ConstObjectPtr object;
			if( parameterName.size() )
			{
				CompoundDataMap::const_iterator it = parameters->readable().find( parameterName );
				if( it != parameters->readable().end() )
				{
					if( const auto c = runTimeCast<CompoundData>( it->second.get() ) )
					{
						object = runTimeCast<Object>( c->member( g_value ) );
					}
				}
			}

			if( object )
			{
				if( auto objectPlug = runTimeCast<ObjectPlug>( output ) )
				{
					objectPlug->setValue( object );
					return;
				}
				else if( auto data = runTimeCast<const Data>( object.get() ) )
				{
					if( PlugAlgo::setValueFromData( valuePlug, output, data ) )
					{
						return;
					}
				}
			}

			output->setToDefault();
			return;
		}
	}

	ComputeNode::compute( output, context );
}

const Gaffer::StringPlug *CameraQuery::sourcePlugFromQuery( const Gaffer::StringPlug *queryPlug ) const
{
	if( const ValuePlug *oPlug = outPlugFromQuery( queryPlug ) )
	{
		return oPlug->getChild<StringPlug>( g_sourcePlugIndex );
	}

	throw IECore::Exception( "CameraQuery : \"source\" plug is missing or of the wrong type." );
}

const Gaffer::ValuePlug *CameraQuery::valuePlugFromQuery( const Gaffer::StringPlug *queryPlug ) const
{
	if( const ValuePlug *oPlug = outPlugFromQuery( queryPlug ) )
	{
		return oPlug->getChild<const ValuePlug>( g_valuePlugIndex );
	}

	throw IECore::Exception( "CameraQuery : \"value\" plug is missing." );
}

const Gaffer::ValuePlug *CameraQuery::outPlugFromQuery( const Gaffer::StringPlug *queryPlug ) const
{
	size_t childIndex = getChildIndex( queriesPlug(), queryPlug );

	if( childIndex < outPlug()->children().size() )
	{
		const ValuePlug *oPlug = outPlug()->getChild<const ValuePlug>( childIndex );
		if( oPlug != nullptr && oPlug->typeId() != Gaffer::ValuePlug::staticTypeId() )
		{
			throw IECore::Exception( "CameraQuery : \"outPlug\" must be a `ValuePlug`." );
		}
		return outPlug()->getChild<ValuePlug>( childIndex );
	}

	throw IECore::Exception( "CameraQuery : \"outPlug\" is missing." );
}

const Gaffer::StringPlug *CameraQuery::queryPlug( const Gaffer::ValuePlug *outputPlug ) const
{
	const size_t childIndex = getChildIndex( outPlug(), outputPlug );

	if( childIndex >= queriesPlug()->children().size() )
	{
		throw IECore::Exception( "CameraQuery : \"query\" plug is missing." );
	}

	if( const StringPlug *childQueryPlug = queriesPlug()->getChild<StringPlug>( childIndex ) )
	{
		return childQueryPlug;
	}

	throw IECore::Exception( "CameraQuery::queryPlug : Queries must be a \"StringPlug\"." );
}

const Gaffer::ValuePlug *CameraQuery::outPlug( const Gaffer::ValuePlug *outputPlug ) const
{
	size_t childIndex = getChildIndex( outPlug(), outputPlug );

	if( const ValuePlug *result = outPlug()->getChild<const ValuePlug>( childIndex ) )
	{
		return result;
	}

	throw IECore::Exception( "CameraQuery : \"out\" plug is missing or of the wrong type." );
}
