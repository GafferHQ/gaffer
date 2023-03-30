//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2012, John Haddon. All rights reserved.
//  Copyright (c) 2013, Image Engine Design Inc. All rights reserved.
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

#include "GafferScene/Group.h"

#include "GafferScene/Private/ChildNamesMap.h"

#include "Gaffer/ArrayPlug.h"
#include "Gaffer/Context.h"
#include "Gaffer/StringPlug.h"
#include "Gaffer/TransformPlug.h"

#include "IECore/NullObject.h"

#include "OpenEXR/OpenEXRConfig.h"
#if OPENEXR_VERSION_MAJOR < 3
#include "OpenEXR/ImathBoxAlgo.h"
#else
#include "Imath/ImathBoxAlgo.h"
#endif

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace Gaffer;
using namespace GafferScene;

namespace
{

const ScenePlug::ScenePath g_root;

} // namespace

GAFFER_NODE_DEFINE_TYPE( Group );

size_t Group::g_firstPlugIndex = 0;

Group::Group( const std::string &name )
	:	SceneProcessor( name, 1 )
{
	storeIndexOfNextChild( g_firstPlugIndex );

	addChild( new StringPlug( "name", Plug::In, "group" ) );
	addChild( new TransformPlug( "transform" ) );

	addChild( new Gaffer::ObjectPlug( "__mapping", Gaffer::Plug::Out, NullObject::defaultNullObject() ) );

	outPlug()->globalsPlug()->setInput( inPlug()->globalsPlug() );
}

Group::~Group()
{
}

ScenePlug *Group::nextInPlug()
{
	return runTimeCast<ScenePlug>( inPlugs()->children().back().get() );
}

const ScenePlug *Group::nextInPlug() const
{
	return runTimeCast<const ScenePlug>( inPlugs()->children().back().get() );
}

Gaffer::StringPlug *Group::namePlug()
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

const Gaffer::StringPlug *Group::namePlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

Gaffer::TransformPlug *Group::transformPlug()
{
	return getChild<TransformPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::TransformPlug *Group::transformPlug() const
{
	return getChild<TransformPlug>( g_firstPlugIndex + 1 );
}

Gaffer::ObjectPlug *Group::mappingPlug()
{
	return getChild<Gaffer::ObjectPlug>( g_firstPlugIndex + 2 );
}

const Gaffer::ObjectPlug *Group::mappingPlug() const
{
	return getChild<Gaffer::ObjectPlug>( g_firstPlugIndex + 2 );
}

void Group::affects( const Plug *input, AffectedPlugsContainer &outputs ) const
{
	SceneProcessor::affects( input, outputs );

	if( input == namePlug() )
	{
		for( ValuePlug::Iterator it( outPlug() ); !it.done(); ++it )
		{
			outputs.push_back( it->get() );
		}
	}
	else if( transformPlug()->isAncestorOf( input ) )
	{
		outputs.push_back( outPlug()->transformPlug() );
		outputs.push_back( outPlug()->boundPlug() );
	}
	else if( const ScenePlug *s = input->parent<ScenePlug>() )
	{
		if( s->parent<ArrayPlug>() == inPlugs() )
		{
			// all input scene plugs children affect the corresponding output child
			outputs.push_back( outPlug()->getChild<ValuePlug>( input->getName() ) );
			// and the names also affect the mapping
			if( input == s->childNamesPlug() )
			{
				outputs.push_back( mappingPlug() );
			}
		}
	}
	else if( input == mappingPlug() )
	{
		// the mapping affects everything about the output
		for( ValuePlug::Iterator it( outPlug() ); !it.done(); ++it )
		{
			outputs.push_back( it->get() );
		}
	}

}

void Group::hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	SceneProcessor::hash( output, context, h );

	if( output == mappingPlug() )
	{
		ScenePlug::PathScope scope( context, &g_root );
		for( const auto &p : ScenePlug::Range( *inPlugs() ) )
		{
			p->childNamesPlug()->hash( h );
		}
	}
}

void Group::compute( Gaffer::ValuePlug *output, const Gaffer::Context *context ) const
{
	if( output == mappingPlug() )
	{
		vector<ConstInternedStringVectorDataPtr> inputChildNames; inputChildNames.reserve( inPlugs()->children().size() );
		ScenePlug::PathScope scope( context, &g_root );
		for( const auto &p : ScenePlug::Range( *inPlugs() ) )
		{
			inputChildNames.push_back( p->childNamesPlug()->getValue() );
		}
		static_cast<Gaffer::ObjectPlug *>( output )->setValue( new Private::ChildNamesMap( inputChildNames ) );
		return;
	}

	return SceneProcessor::compute( output, context );
}

void Group::hashBound( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	if( path.size() == 0 ) // "/"
	{
		SceneProcessor::hashBound( path, context, parent, h );
		for( ScenePlug::Iterator it( inPlugs() ); !it.done(); ++it )
		{
			(*it)->boundPlug()->hash( h );
		}
		transformPlug()->hash( h );
	}
	else if( path.size() == 1 ) // "/group"
	{
		SceneProcessor::hashBound( path, context, parent, h );
		ScenePlug::PathScope scope( context, &g_root );
		for( ScenePlug::Iterator it( inPlugs() ); !it.done(); ++it )
		{
			(*it)->boundPlug()->hash( h );
		}
	}
	else // "/group/..."
	{
		// pass through
		const ScenePlug *sourcePlug = nullptr;
		ScenePath source = sourcePath( path, &sourcePlug );
		h = sourcePlug->boundHash( source );
	}
}

Imath::Box3f Group::computeBound( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	if( path.size() <= 1 )
	{
		// either / or /groupName
		Box3f combinedBound;
		for( ScenePlug::Iterator it( inPlugs() ); !it.done(); ++it )
		{
			// we don't need to transform these bounds, because the SceneNode
			// guarantees that the transform for root nodes is always identity.
			Box3f bound = (*it)->bound( ScenePath() );
			combinedBound.extendBy( bound );
		}
		if( path.size() == 0 )
		{
			combinedBound = transform( combinedBound, transformPlug()->matrix() );
		}
		return combinedBound;
	}
	else
	{
		const ScenePlug *sourcePlug = nullptr;
		ScenePath source = sourcePath( path, &sourcePlug );
		return sourcePlug->bound( source );
	}
}

void Group::hashTransform( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	if( path.size() == 0 ) // "/"
	{
		SceneProcessor::hashTransform( path, context, parent, h );
	}
	else if( path.size() == 1 ) // "/group"
	{
		SceneProcessor::hashTransform( path, context, parent, h );
		transformPlug()->hash( h );
	}
	else if( path.size() > 1 ) // "/group/..."
	{
		// pass through
		const ScenePlug *sourcePlug = nullptr;
		ScenePath source = sourcePath( path, &sourcePlug );
		h = sourcePlug->transformHash( source );
	}
}

Imath::M44f Group::computeTransform( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	if( path.size() == 0 )
	{
		return Imath::M44f();
	}
	else if( path.size() == 1 )
	{
		return transformPlug()->matrix();
	}
	else
	{
		const ScenePlug *sourcePlug = nullptr;
		ScenePath source = sourcePath( path, &sourcePlug );
		return sourcePlug->transform( source );
	}
}

void Group::hashAttributes( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	if( path.size() <= 1 ) // "/" or "/group"
	{
		SceneProcessor::hashAttributes( path, context, parent, h );
	}
	else // "/group/..."
	{
		// pass through
		const ScenePlug *sourcePlug = nullptr;
		ScenePath source = sourcePath( path, &sourcePlug );
		h = sourcePlug->attributesHash( source );
	}
}

IECore::ConstCompoundObjectPtr Group::computeAttributes( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	if( path.size() <= 1 )
	{
		return parent->attributesPlug()->defaultValue();
	}
	else
	{
		const ScenePlug *sourcePlug = nullptr;
		ScenePath source = sourcePath( path, &sourcePlug );
		return sourcePlug->attributes( source );
	}
}

void Group::hashObject( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	if( path.size() <= 1 ) // "/" or "/group"
	{
		SceneProcessor::hashObject( path, context, parent, h );
	}
	else // "/group/..."
	{
		// pass through
		const ScenePlug *sourcePlug = nullptr;
		ScenePath source = sourcePath( path, &sourcePlug );
		h = sourcePlug->objectHash( source );
	}
}

IECore::ConstObjectPtr Group::computeObject( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	if( path.size() <= 1 )
	{
		return parent->objectPlug()->defaultValue();
	}
	else
	{
		const ScenePlug *sourcePlug = nullptr;
		ScenePath source = sourcePath( path, &sourcePlug );
		return sourcePlug->object( source );
	}
}

void Group::hashChildNames( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	if( path.size() == 0 ) // "/"
	{
		SceneProcessor::hashChildNames( path, context, parent, h );
		namePlug()->hash( h );
	}
	else if( path.size() == 1 ) // "/group"
	{
		SceneProcessor::hashChildNames( path, context, parent, h );
		mappingPlug()->hash( h );
	}
	else // "/group/..."
	{
		// pass through
		const ScenePlug *sourcePlug = nullptr;
		ScenePath source = sourcePath( path, &sourcePlug );
		h = sourcePlug->childNamesHash( source );
	}
}

IECore::ConstInternedStringVectorDataPtr Group::computeChildNames( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	if( path.size() == 0 )
	{
		InternedStringVectorDataPtr result = new InternedStringVectorData();
		result->writable().push_back( namePlug()->getValue() );
		return result;
	}
	else if( path.size() == 1 )
	{
		ScenePlug::GlobalScope s( context );
		Private::ConstChildNamesMapPtr mapping = boost::static_pointer_cast<const Private::ChildNamesMap>( mappingPlug()->getValue() );
		return mapping->outputChildNames();
	}
	else
	{
		const ScenePlug *sourcePlug = nullptr;
		ScenePath source = sourcePath( path, &sourcePlug );
		return sourcePlug->childNames( source );
	}
}

void Group::hashSetNames( const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	SceneProcessor::hashSetNames( context, parent, h );
	for( ScenePlug::Iterator it( inPlugs() ); !it.done(); ++it )
	{
		(*it)->setNamesPlug()->hash( h );
	}
}

IECore::ConstInternedStringVectorDataPtr Group::computeSetNames( const Gaffer::Context *context, const ScenePlug *parent ) const
{
	InternedStringVectorDataPtr resultData = new InternedStringVectorData;
	vector<InternedString> &result = resultData->writable();
	for( ScenePlug::Iterator it( inPlugs() ); !it.done(); ++it )
	{
		// This naive approach to merging set names preserves the order of the incoming names,
		// but at the expense of using linear search. We assume that the number of sets is small
		// enough and the InternedString comparison fast enough that this is OK.
		ConstInternedStringVectorDataPtr inputSetNamesData = (*it)->setNamesPlug()->getValue();
		const vector<InternedString> &inputSetNames = inputSetNamesData->readable();
		for( vector<InternedString>::const_iterator it = inputSetNames.begin(), eIt = inputSetNames.end(); it != eIt; ++it )
		{
			if( std::find( result.begin(), result.end(), *it ) == result.end() )
			{
				result.push_back( *it );
			}
		}
	}

	return resultData;
}

void Group::hashSet( const IECore::InternedString &setName, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	SceneProcessor::hashSet( setName, context, parent, h );
	for( const auto &p : ScenePlug::Range( *inPlugs() ) )
	{
		p->setPlug()->hash( h );
	}

	ScenePlug::GlobalScope s( context );
	mappingPlug()->hash( h );
	namePlug()->hash( h );
}

IECore::ConstPathMatcherDataPtr Group::computeSet( const IECore::InternedString &setName, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	vector<ConstPathMatcherDataPtr> inputSets; inputSets.reserve( inPlugs()->children().size() );
	for( const auto &p : ScenePlug::Range( *inPlugs() ) )
	{
		inputSets.push_back( p->setPlug()->getValue() );
	}

	ScenePlug::GlobalScope s( context );
	Private::ConstChildNamesMapPtr mapping = boost::static_pointer_cast<const Private::ChildNamesMap>( mappingPlug()->getValue() );
	const InternedString name = namePlug()->getValue();

	PathMatcherDataPtr resultData = new PathMatcherData;
	resultData->writable().addPaths( mapping->set( inputSets ), { name } );

	return resultData;
}

SceneNode::ScenePath Group::sourcePath( const ScenePath &outputPath, const ScenePlug **source ) const
{
	ScenePlug::GlobalScope s( Context::current() );
	Private::ConstChildNamesMapPtr mapping = boost::static_pointer_cast<const Private::ChildNamesMap>( mappingPlug()->getValue() );

	const Private::ChildNamesMap::Input &input = mapping->input( outputPath[1] );
	*source = inPlugs()->getChild<ScenePlug>( input.index );

	ScenePath result;
	result.reserve( outputPath.size() - 1 );
	result.push_back( input.name );
	result.insert( result.end(), outputPath.begin() + 2, outputPath.end() );
	return result;
}
