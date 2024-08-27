//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2022, Cinesite VFX Ltd. All rights reserved.
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

#include "GafferScene/ShaderQuery.h"

#include "Gaffer/PlugAlgo.h"
#include "Gaffer/TypedObjectPlug.h"

#include "GafferScene/AttributeQuery.h"

#include "IECore/NullObject.h"

#include "IECoreScene/ShaderNetwork.h"

using namespace Imath;
using namespace IECore;
using namespace IECoreScene;
using namespace Gaffer;

namespace
{

const size_t g_existsPlugIndex = 0;
const size_t g_valuePlugIndex = 1;

/// \todo: Can the next function be move to somewhere to be shared with `AttributeQuery`?

const Gaffer::ValuePlug *correspondingPlug(
	const Gaffer::ValuePlug *parent,
	const Gaffer::ValuePlug *child,
	const Gaffer::ValuePlug *other
)
{
	boost::container::small_vector< const Gaffer::ValuePlug*, 4 > path;

	const Gaffer::ValuePlug *plug = child;

	while( plug != parent )
	{
		path.push_back( plug );
		plug = plug->parent< Gaffer::ValuePlug >();
	}

	plug = other;

	while( ! path.empty() )
	{
		plug = plug->getChild< Gaffer::ValuePlug >( path.back()->getName() );
		path.pop_back();
	}

	return plug;
}

void addChildPlugsToAffectedOutputs( const Gaffer::Plug* plug, Gaffer::DependencyNode::AffectedPlugsContainer& outputs )
{
	if( plug->children().empty() )
	{
		outputs.push_back( plug );
	}
	else
	{
		for( const Gaffer::PlugPtr& child : Gaffer::Plug::OutputRange( *plug ) )
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

	throw IECore::Exception( "ShaderQuery : Plug not in hierarchy." );
}

}  // namespace

namespace GafferScene
{

GAFFER_NODE_DEFINE_TYPE( ShaderQuery );

size_t ShaderQuery::g_firstPlugIndex = 0;

ShaderQuery::ShaderQuery( const std::string &name ) : Gaffer::ComputeNode( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );

	addChild( new ScenePlug( "scene" ) );
	addChild( new StringPlug( "location" ) );
	addChild( new StringPlug( "shader" ) );
	addChild( new BoolPlug( "inherit", Plug::In, false ) );
	/// \todo This is violating the ArrayPlug requirements by not providing an `elementPrototype`
	/// at construction. And we later violate it further by creating non-homogeneous elements in
	/// `addQuery()`. We're only using an ArrayPlug because we want the serialisation to use numeric
	/// indexing for the children of `queries` and `out` - since the serialisation uses `addQuery()`
	/// to recreate the children, and that doesn't maintain names. So perhaps we can just use a
	/// ValuePlug instead of an ArrayPlug, and add a separate mechanism for requesting that children use
	/// numeric indices separately (see `keyedByIndex()` in `Serialisation.cpp`).
	///
	/// The same applies to OptionQuery, PrimitiveVariableQuery and ContextQuery.
	addChild( new ArrayPlug( "queries", Plug::Direction::In, nullptr, 1, std::numeric_limits<size_t>::max(), Plug::Flags::Default, false ) );
	addChild( new ArrayPlug( "out", Plug::Direction::Out, nullptr, 1, std::numeric_limits<size_t>::max(), Plug::Flags::Default, false ) );

	AttributeQueryPtr attributeQuery = new AttributeQuery( "__attributeQuery" );
	addChild( attributeQuery );

	ObjectPlugPtr intermediateObjectPlug = new ObjectPlug(
		"__intermediateObjectPlug",
		Plug::In,
		IECore::NullObject::defaultNullObject(),
		Plug::Default & ~Plug::Serialisable
	);
	addChild( intermediateObjectPlug );

	attributeQuery->scenePlug()->setInput( scenePlug() );
	attributeQuery->locationPlug()->setInput( locationPlug() );
	attributeQuery->attributePlug()->setInput( shaderPlug() );
	attributeQuery->inheritPlug()->setInput( inheritPlug() );

	attributeQuery->setup( intermediateObjectPlug.get() );
	intermediateObjectPlug->setInput( attributeQuery->valuePlug() );
}

ShaderQuery::~ShaderQuery()
{
}

ScenePlug *ShaderQuery::scenePlug()
{
	return getChild<ScenePlug>( g_firstPlugIndex );
}

const ScenePlug *ShaderQuery::scenePlug() const
{
	return getChild<ScenePlug>( g_firstPlugIndex );
}

StringPlug *ShaderQuery::locationPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

const StringPlug *ShaderQuery::locationPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

StringPlug *ShaderQuery::shaderPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 2 );
}

const StringPlug *ShaderQuery::shaderPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 2 );
}

BoolPlug *ShaderQuery::inheritPlug()
{
	return getChild<BoolPlug>( g_firstPlugIndex + 3 );
}

const BoolPlug *ShaderQuery::inheritPlug() const
{
	return getChild<BoolPlug>( g_firstPlugIndex + 3 );
}

Gaffer::ArrayPlug *ShaderQuery::queriesPlug()
{
	return getChild<ArrayPlug>( g_firstPlugIndex + 4 );
}

const Gaffer::ArrayPlug *ShaderQuery::queriesPlug() const
{
	return getChild<ArrayPlug>( g_firstPlugIndex + 4 );
}

Gaffer::ArrayPlug *ShaderQuery::outPlug()
{
	return getChild<ArrayPlug>( g_firstPlugIndex + 5 );
}

const Gaffer::ArrayPlug *ShaderQuery::outPlug() const
{
	return getChild<ArrayPlug>( g_firstPlugIndex + 5 );
}

AttributeQuery *ShaderQuery::attributeQuery()
{
	return getChild<AttributeQuery>( g_firstPlugIndex + 6 );
}

const AttributeQuery *ShaderQuery::attributeQuery() const
{
	return getChild<AttributeQuery>( g_firstPlugIndex + 6 );
}

ObjectPlug *ShaderQuery::intermediateObjectPlug()
{
	return getChild<ObjectPlug>( g_firstPlugIndex + 7 );
}

const ObjectPlug *ShaderQuery::intermediateObjectPlug() const
{
	return getChild<ObjectPlug>( g_firstPlugIndex + 7 );
}

Gaffer::NameValuePlug *ShaderQuery::addQuery(
	const Gaffer::ValuePlug *plug,
	const std::string &parameter
)
{
	NameValuePlugPtr childQueryPlug = new NameValuePlug(
		"",
		plug->createCounterpart( "query0", Gaffer::Plug::Direction::In ),
		"query0",
		Gaffer::Plug::Flags::Default
	);
	childQueryPlug->namePlug()->setValue( parameter );

	ValuePlugPtr newOutPlug = new ValuePlug( "out0", Gaffer::Plug::Direction::Out );
	newOutPlug->addChild(
		new BoolPlug(
			"exists",
			Gaffer::Plug::Direction::Out,
			false
		)
	);
	newOutPlug->addChild( plug->createCounterpart( "value", Gaffer::Plug::Direction::Out ) );

	outPlug()->addChild( newOutPlug );

	queriesPlug()->addChild( childQueryPlug );

	return childQueryPlug.get();
}

void ShaderQuery::removeQuery( Gaffer::NameValuePlug *plug )
{
	const ValuePlug *oPlug = outPlugFromQuery( plug );

	queriesPlug()->removeChild( plug );
	outPlug()->removeChild( const_cast<ValuePlug *>( oPlug ) );
}

void ShaderQuery::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs) const
{
	ComputeNode::affects( input, outputs );

	if(
		input == intermediateObjectPlug()
	)
	{
		addChildPlugsToAffectedOutputs( outPlug(), outputs );
	}

	else if( queriesPlug()->isAncestorOf( input ) )
	{
		const NameValuePlug *childQueryPlug = input->ancestor<NameValuePlug>();
		if( childQueryPlug == nullptr )
		{
			throw IECore::Exception( "ShaderQuery::affects : Query plugs must be \"NameValuePlug\"" );
		}

		const ValuePlug *vPlug = valuePlugFromQuery( childQueryPlug );

		if( input == childQueryPlug->namePlug() )
		{
			addChildPlugsToAffectedOutputs( vPlug, outputs );

			outputs.push_back( existsPlugFromQuery( childQueryPlug ) );
		}
		else if( childQueryPlug->valuePlug() == input || childQueryPlug->valuePlug()->isAncestorOf( input ) )
		{
			outputs.push_back(
				correspondingPlug(
					static_cast<const ValuePlug *>( childQueryPlug->valuePlug<ValuePlug>() ),
					runTimeCast<const ValuePlug>( input ),
					vPlug
				)
			);
		}
	}
}

void ShaderQuery::hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ComputeNode::hash( output, context, h );

	if( outPlug()->isAncestorOf( output ) )
	{
		const ValuePlug *oPlug = outPlug( output );

		if( output == oPlug->getChild( g_existsPlugIndex ) )
		{
			const NameValuePlug *childQueryPlug = queryPlug( output );
			childQueryPlug->namePlug()->hash( h );
			intermediateObjectPlug()->hash( h );
		}

		else if(
			oPlug->getChild( g_valuePlugIndex )->isAncestorOf( output ) ||
			output == oPlug->getChild( g_valuePlugIndex )
		)
		{
			const NameValuePlug *childQueryPlug = queryPlug( output );
			childQueryPlug->namePlug()->hash( h );
			intermediateObjectPlug()->hash( h );

			correspondingPlug(
				valuePlugFromQuery( childQueryPlug ),
				output,
				static_cast<const ValuePlug *>( childQueryPlug->valuePlug() )
			)->hash( h );
		}
	}
}

void ShaderQuery::compute( Gaffer::ValuePlug *output, const Gaffer::Context *context ) const
{
	if( outPlug()->isAncestorOf( output ) )
	{
		const ValuePlug *oPlug = outPlug( output );

		if( output == oPlug->getChild( g_existsPlugIndex ) )
		{
			const NameValuePlug *childQueryPlug = queryPlug( output );

			const std::string parameterName = childQueryPlug->namePlug()->getValue();
			const IECore::ConstObjectPtr object = intermediateObjectPlug()->getValue();

			const Data *resultData = parameterData( object.get(), parameterName );

			static_cast<BoolPlug *>( output )->setValue( resultData != nullptr );

			return;
		}

		else if(
			oPlug->getChild( g_valuePlugIndex )->isAncestorOf( output ) ||
			output == oPlug->getChild( g_valuePlugIndex )
		)
		{
			const NameValuePlug *childQueryPlug = queryPlug( output );

			const std::string parameterName = childQueryPlug->namePlug()->getValue();
			const IECore::ConstObjectPtr object = intermediateObjectPlug()->getValue();
			const ValuePlug *vPlug = valuePlugFromQuery( childQueryPlug );

			const Data *resultData = parameterData( object.get(), parameterName );

			if( resultData != nullptr )
			{
				if( PlugAlgo::setValueFromData( vPlug, output, resultData ) )
				{
					return;
				}
			}

			output->setFrom(
				static_cast<const Gaffer::ValuePlug *>(
					correspondingPlug(
						vPlug,
						output,
						static_cast<const ValuePlug *>( childQueryPlug->valuePlug() )
					)
				)
			);

			return;
		}
	}

	ComputeNode::compute( output, context );

}

const Data *ShaderQuery::parameterData( const IECore::Object *object, const std::string &parameterName ) const
{
	if( parameterName.empty() )
	{
		return nullptr;
	}

	if( const ShaderNetwork *shaderNetwork = runTimeCast<const ShaderNetwork>( object ) )
	{
		ShaderNetwork::Parameter parameter;
		size_t dotPos = parameterName.find_last_of( '.' );
		if( dotPos == std::string::npos )
		{
			parameter.shader = shaderNetwork->getOutput().shader;
			parameter.name = parameterName;
		}
		else
		{
			parameter.shader = InternedString( parameterName.c_str(), dotPos );
			parameter.name = InternedString( parameterName.c_str() + dotPos + 1 );
		}

		const IECoreScene::Shader *shader = shaderNetwork->getShader( parameter.shader );
		if( shader == nullptr )
		{
			return nullptr;
		}

		if( auto input = shaderNetwork->input( parameter ) )
		{
			return nullptr;
		}

		return shader->parametersData()->member( parameter.name );
	}

	return nullptr;
}

const Gaffer::BoolPlug *ShaderQuery::existsPlugFromQuery( const Gaffer::NameValuePlug *queryPlug ) const
{
	if( const ValuePlug *oPlug = outPlugFromQuery( queryPlug ) )
	{
		return oPlug->getChild<BoolPlug>( g_existsPlugIndex );
	}

	throw IECore::Exception( "ShaderQuery : \"exists\" plug is missing or of the wrong type." );
}

const Gaffer::ValuePlug *ShaderQuery::valuePlugFromQuery( const Gaffer::NameValuePlug *queryPlug ) const
{
	if( const ValuePlug *oPlug = outPlugFromQuery( queryPlug ) )
	{
		return oPlug->getChild<const ValuePlug>( g_valuePlugIndex );
	}

	throw IECore::Exception( "ShaderQuery : \"value\" plug is missing." );
}

const Gaffer::ValuePlug *ShaderQuery::outPlugFromQuery( const Gaffer::NameValuePlug *queryPlug ) const
{
	size_t childIndex = getChildIndex( queriesPlug(), queryPlug );

	if( childIndex < outPlug()->children().size() )
	{
		const ValuePlug *oPlug = outPlug()->getChild<const ValuePlug>( childIndex );
		if( oPlug != nullptr && oPlug->typeId() != Gaffer::ValuePlug::staticTypeId() )
		{
			throw IECore::Exception( "ShaderQuery : \"outPlug\" must be a `ValuePlug`."  );
		}
		return outPlug()->getChild<ValuePlug>( childIndex );
	}

	throw IECore::Exception( "ShaderQuery : \"outPlug\" is missing." );
}

const Gaffer::NameValuePlug *ShaderQuery::queryPlug( const Gaffer::ValuePlug *outputPlug ) const
{
	const size_t childIndex = getChildIndex( outPlug(), outputPlug );

	if( childIndex >= queriesPlug()->children().size() )
	{
		throw IECore::Exception( "ShaderQuery : \"query\" plug is missing." );
	}

	if( const NameValuePlug *childQueryPlug = queriesPlug()->getChild<NameValuePlug>( childIndex ) )
	{
		return childQueryPlug;
	}

	throw IECore::Exception( "ShaderQuery::queryPlug : Queries must be a \"NameValuePlug\".");

}

const Gaffer::ValuePlug *ShaderQuery::outPlug( const Gaffer::ValuePlug *outputPlug ) const
{
	size_t childIndex = getChildIndex( outPlug(), outputPlug );

	if( const ValuePlug *result = outPlug()->getChild<const ValuePlug>( childIndex ) )
	{
		return result;
	}

	throw IECore::Exception( "ShaderQuery : \"out\" plug is missing or of the wrong type.");
}

}  // namespace GafferScene
