//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2013, John Haddon. All rights reserved.
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

#include "GafferOSL/OSLObject.h"

#include "GafferOSL/ClosurePlug.h"
#include "GafferOSL/OSLCode.h"
#include "GafferOSL/ShadingEngine.h"

#include "GafferScene/ResamplePrimitiveVariables.h"

#include "IECoreScene/Primitive.h"

#include "IECore/MessageHandler.h"

#include "boost/bind.hpp"

using namespace Imath;
using namespace IECore;
using namespace IECoreScene;
using namespace Gaffer;
using namespace GafferScene;
using namespace GafferOSL;

IE_CORE_DEFINERUNTIMETYPED( OSLObject );

size_t OSLObject::g_firstPlugIndex;

namespace
{

CompoundDataPtr prepareShadingPoints( const Primitive *primitive )
{
	CompoundDataPtr shadingPoints = new CompoundData;
	for( PrimitiveVariableMap::const_iterator it = primitive->variables.begin(), eIt = primitive->variables.end(); it != eIt; ++it )
	{
		// cast is ok - we're only using it to be able to reference the data from the shadingPoints,
		// but nothing will modify the data itself.
		shadingPoints->writable()[it->first] = boost::const_pointer_cast<Data>( it->second.data );
	}

	return shadingPoints;
}

IECore::InternedString g_shaderPassthroughParameterName( "passthrough" );

};

OSLObject::OSLObject( const std::string &name )
	:	SceneElementProcessor( name, IECore::PathMatcher::NoMatch )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new GafferScene::ShaderPlug( "__shader", Plug::In, Plug::Default & ~Plug::Serialisable ) );
	addChild( new IntPlug( "interpolation", Plug::In, PrimitiveVariable::Vertex, PrimitiveVariable::Invalid, PrimitiveVariable::FaceVarying ) );
	addChild( new ScenePlug( "__resampledIn", Plug::In, Plug::Default & ~Plug::Serialisable ) );

	addChild( new StringPlug( "__resampleNames", Plug::Out ) );
	addChild( new Plug( "primitiveVariables", Plug::In, Plug::Default & ~Plug::AcceptsInputs ) );
	addChild( new OSLCode( "__outputInternal" ) );

	ClosurePlugPtr codeOut = new ClosurePlug( "out", Plug::Out );
	outputCombineOSLCode()->outPlug()->addChild( codeOut );

	OSLShaderPtr closureToShaderConverter = new OSLShader( "__closureToShaderConverter" );
	addChild( closureToShaderConverter );
	// TODO - come up with a better name for closure-to-shader than calling it both OutImage and OutObject
	closureToShaderConverter->loadShader( "ImageProcessing/OutImage" );

	closureToShaderConverter->parametersPlug()->getChild<GafferOSL::ClosurePlug>(0)->setInput( codeOut );
	shaderPlug()->setInput( closureToShaderConverter->outPlug() );

    primitiveVariablesPlug()->childAddedSignal().connect( boost::bind( &OSLObject::primitiveVariableAdded, this, ::_1, ::_2 ) );
    primitiveVariablesPlug()->childRemovedSignal().connect( boost::bind( &OSLObject::primitiveVariableRemoved, this, ::_1, ::_2 ) );

	GafferScene::ResamplePrimitiveVariablesPtr resample = new ResamplePrimitiveVariables( "__resample" );
	addChild( resample );

	//todo only resample variables which we've read from in the OSL shader
	resample->namesPlug()->setInput( resampledNamesPlug() );
	resample->inPlug()->setInput( inPlug() );
	resample->interpolationPlug()->setInput( interpolationPlug() );
	resample->filterPlug()->setInput( filterPlug() );

	resampledInPlug()->setInput( resample->outPlug() );

	// Pass-throughs for things we don't want to modify
	outPlug()->attributesPlug()->setInput( inPlug()->attributesPlug() );
	outPlug()->transformPlug()->setInput( inPlug()->transformPlug() );
}

OSLObject::~OSLObject()
{
}

GafferScene::ShaderPlug *OSLObject::shaderPlug()
{
	return getChild<GafferScene::ShaderPlug>( g_firstPlugIndex );
}

const GafferScene::ShaderPlug *OSLObject::shaderPlug() const
{
	return getChild<GafferScene::ShaderPlug>( g_firstPlugIndex );
}

Gaffer::IntPlug *OSLObject::interpolationPlug()
{
	return getChild<IntPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::IntPlug *OSLObject::interpolationPlug() const
{
	return getChild<IntPlug>( g_firstPlugIndex + 1 );
}

ScenePlug *OSLObject::resampledInPlug()
{
	return getChild<ScenePlug>( g_firstPlugIndex + 2 );
}

const ScenePlug *OSLObject::resampledInPlug() const
{
	return getChild<ScenePlug>( g_firstPlugIndex + 2 );
}

StringPlug *OSLObject::resampledNamesPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 3 );
}

const StringPlug *OSLObject::resampledNamesPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 3 );
}

Gaffer::Plug *OSLObject::primitiveVariablesPlug()
{
	return getChild<Gaffer::Plug>( g_firstPlugIndex + 4 );
}

const Gaffer::Plug *OSLObject::primitiveVariablesPlug() const
{
	return getChild<Gaffer::Plug>( g_firstPlugIndex + 4 );
}

GafferOSL::OSLCode *OSLObject::outputCombineOSLCode()
{
	return getChild<GafferOSL::OSLCode>( g_firstPlugIndex + 5 );
}

const GafferOSL::OSLCode *OSLObject::outputCombineOSLCode() const
{
	return getChild<GafferOSL::OSLCode>( g_firstPlugIndex + 5 );
}

void OSLObject::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	SceneElementProcessor::affects( input, outputs );

	if( input == shaderPlug() ||
		input == inPlug()->transformPlug() ||
		input == interpolationPlug() ||
		input == resampledInPlug()->objectPlug()
		)
	{
		outputs.push_back( outPlug()->objectPlug() );
	}
	else if( input == inPlug()->objectPlug() )
	{
		outputs.push_back( resampledNamesPlug() );
	}
	else if( input == outPlug()->objectPlug() )
	{
		outputs.push_back( outPlug()->boundPlug() );
	}
}

bool OSLObject::processesBound() const
{
	return runTimeCast<const OSLShader>( shaderPlug()->source()->node() );
}

void OSLObject::hashProcessedBound( const ScenePath &path, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	hashProcessedObject( path, context, h );
}

Imath::Box3f OSLObject::computeProcessedBound( const ScenePath &path, const Gaffer::Context *context, const Imath::Box3f &inputBound ) const
{
	ConstObjectPtr object = outPlug()->objectPlug()->getValue();
	if( const Primitive *primitive = runTimeCast<const Primitive>( object.get() ) )
	{
		return primitive->bound();
	}
	return inputBound;
}

bool OSLObject::processesObject() const
{
	return runTimeCast<const OSLShader>( shaderPlug()->source()->node() );
}

void OSLObject::hashProcessedObject( const ScenePath &path, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	const OSLShader *shader = runTimeCast<const OSLShader>( shaderPlug()->source()->node() );
	if( shader )
	{
		shader->attributesHash( h );
	}

	interpolationPlug()->hash( h );
	h.append( inPlug()->fullTransformHash( path ) );
	h.append( resampledInPlug()->objectPlug()->hash() );
}

static const IECore::InternedString g_world("world");

IECore::ConstObjectPtr OSLObject::computeProcessedObject( const ScenePath &path, const Gaffer::Context *context, IECore::ConstObjectPtr inputObject ) const
{
	const Primitive *inputPrimitive = runTimeCast<const Primitive>( inputObject.get() );
	if( !inputPrimitive )
	{
		return inputObject;
	}

	ConstOSLShaderPtr shader = runTimeCast<const OSLShader>( shaderPlug()->source()->node() );
	ConstShadingEnginePtr shadingEngine = shader ? shader->shadingEngine() : nullptr;

	if( !shadingEngine )
	{
		return inputObject;
	}

	PrimitiveVariable::Interpolation interpolation = static_cast<PrimitiveVariable::Interpolation>( interpolationPlug()->getValue() );

	IECoreScene::ConstPrimitivePtr resampledObject = IECore::runTimeCast<const IECoreScene::Primitive>( resampledInPlug()->objectPlug()->getValue() );
	CompoundDataPtr shadingPoints = prepareShadingPoints( resampledObject.get() );

	PrimitivePtr outputPrimitive = inputPrimitive->copy();

	ShadingEngine::Transforms transforms;

	transforms[ g_world ] = ShadingEngine::Transform( inPlug()->fullTransform( path ));

	CompoundDataPtr shadedPoints = shadingEngine->shade( shadingPoints.get(), transforms );
	for( CompoundDataMap::const_iterator it = shadedPoints->readable().begin(), eIt = shadedPoints->readable().end(); it != eIt; ++it )
	{

		// Ignore the output color closure as the debug closures are used to define what is 'exported' from the shader
		if( it->first != "Ci" )
		{
			outputPrimitive->variables[it->first] = PrimitiveVariable( interpolation, it->second );
		}
	}

	return outputPrimitive;
}

void OSLObject::hash( const ValuePlug *output, const Context *context, IECore::MurmurHash &h ) const
{
	SceneElementProcessor::hash( output, context, h );

	if( output == resampledNamesPlug() )
	{
		inPlug()->objectPlug()->hash( h );
	}
}

void OSLObject::compute( Gaffer::ValuePlug *output, const Gaffer::Context *context ) const
{
	if( output == resampledNamesPlug() )
	{
		ConstPrimitivePtr prim = runTimeCast<const IECoreScene::Primitive>( inPlug()->objectPlug()->getValue() );

		if (!prim)
		{
			static_cast<StringPlug *>( output )->setToDefault();
			return;
		}

		std::string nonConstantPrimitiveVariables;

		for( PrimitiveVariableMap::const_iterator it = prim->variables.begin(); it != prim->variables.end(); ++it )
		{
			if( it->second.interpolation == PrimitiveVariable::Constant )
			{
				continue;
			}

			nonConstantPrimitiveVariables += " " + it->first;
		}

		static_cast<StringPlug *>( output )->setValue( nonConstantPrimitiveVariables );
		return;
	}

	SceneElementProcessor::compute( output, context );
}

void OSLObject::updatePrimitiveVariables()
{
    try
    {
		outputCombineOSLCode()->parametersPlug()->clearChildren();

		std::string code;

		for( PlugIterator rootPlug( primitiveVariablesPlug() ); !rootPlug.done(); ++rootPlug )
		{
			if( (*rootPlug)->typeId() == ClosurePlug::staticTypeId() )
			{
				ClosurePlugPtr codeClosurePlug = new ClosurePlug( "closureIn" );
				outputCombineOSLCode()->parametersPlug()->addChild( codeClosurePlug );
				codeClosurePlug->setInput( *rootPlug );

				code += "out += " + codeClosurePlug->getName().string() + ";\n";
			}
			else
			{
				StringPlug *namePlug = (*rootPlug)->getChild<StringPlug>( "name" );
				Plug *valuePlug = (*rootPlug)->getChild<Plug>( "value" );

				std::string outFunction;
				PlugPtr codeValuePlug;
				if( valuePlug )
				{
					const Gaffer::TypeId valueType = (Gaffer::TypeId)valuePlug->typeId();
					switch( (int)valueType )
					{
						case FloatPlugTypeId :
							codeValuePlug = new FloatPlug( "value" );
							outFunction = "outFloat";
							break;
						case IntPlugTypeId :
							codeValuePlug = new IntPlug( "value" );
							outFunction = "outInt";
							break;
						case Color3fPlugTypeId :
							codeValuePlug = new Color3fPlug( "value" );
							outFunction = "outColor";
							break;
						case V3fPlugTypeId :
							codeValuePlug = new V3fPlug( "value" );
							{
								V3fPlug *v3fPlug = runTimeCast<V3fPlug>( valuePlug );
								if( v3fPlug->interpretation() == GeometricData::Point )
								{
									outFunction = "outVector";
								}
								else if( v3fPlug->interpretation() == GeometricData::Normal )
								{
									outFunction = "outNormal";
								}
								else
								{
									outFunction = "outVector";
								}
							}
							break;
						case M44fPlugTypeId :
							codeValuePlug = new M44fPlug( "value" );
							outFunction = "outMatrix";
							break;
						case StringPlugTypeId :
							codeValuePlug = new StringPlug( "value" );
							outFunction = "outString";
							break;
					}
				}

				if( namePlug && codeValuePlug )
				{
					StringPlugPtr codeNamePlug = new StringPlug( "name" );
					outputCombineOSLCode()->parametersPlug()->addChild( codeNamePlug );
					codeNamePlug->setInput( namePlug );

					outputCombineOSLCode()->parametersPlug()->addChild( codeValuePlug );
					codeValuePlug->setInput( valuePlug );

					code += "out += " + outFunction + "( " + codeNamePlug->getName().string() + ", "
						+ codeValuePlug->getName().string() + ");\n";
				}
				else
				{
					IECore::msg( IECore::Msg::Warning, "OSLObject::updatePrimitiveVariables",
						"Could not create primitive variable from plug: " + (*rootPlug)->fullName() );
				}
			}
		}

		outputCombineOSLCode()->codePlug()->setValue( code );
    }
	catch( const std::exception &e )
	{
		// We call updateShader() from `plugSet()`
		// and `parameterAddedOrRemoved()`, and the
		// client code that set the plug or added
		// the parameter is not designed to deal with
		// such fundamental actions throwing. So we suppress
		// any exceptions here rather than let them
		// percolate back out to the caller.

		IECore::msg( IECore::Msg::Warning, "OSLObject::updatePrimitiveVariables", e.what() );
	}
}

void OSLObject::primitiveVariableAdded( const Gaffer::GraphComponent *parent, Gaffer::GraphComponent *child )
{
	updatePrimitiveVariables();
}

void OSLObject::primitiveVariableRemoved( const Gaffer::GraphComponent *parent, Gaffer::GraphComponent *child )
{
	updatePrimitiveVariables();
}
