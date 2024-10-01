//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2023,  Cinesite VFX Ltd. All rights reserved.
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

#include "GafferImage/OpenColorIOAlgo.h"

#include "Gaffer/Context.h"

#include "Gaffer/Private/IECorePreview/LRUCache.h"

#include "OpenColorIO/OpenColorIO.h"

#include "boost/algorithm/string/predicate.hpp"

#include "fmt/format.h"

using namespace std;

namespace
{

const IECore::InternedString g_ocioConfigContextName( "ocio:config" );
const IECore::InternedString g_ocioWorkingSpaceContextName( "ocio:workingSpace" );
const string g_ocioStringVarPrefix( "ocio:stringVar:" );
const string g_emptyString;
const string g_sceneLinearString( OCIO_NAMESPACE::ROLE_SCENE_LINEAR );

IECorePreview::LRUCache<std::string, OCIO_NAMESPACE::ConstConfigRcPtr> g_configCache(
	[] ( const std::string &fileName, size_t &cost, const IECore::Canceller *canceller ) {
		cost = 1;
		OCIO_NAMESPACE::ConstConfigRcPtr config;
		if( fileName.empty() )
		{
			config = OCIO_NAMESPACE::Config::CreateFromEnv();
		}
		else
		{
			config = OCIO_NAMESPACE::Config::CreateFromFile( fileName.c_str() );
		}
		// Various config queries such as `getDefaultDisplay()` are not
		// threadsafe, because they do an unguarded lazy-initialisation of a
		// data structure within the config. Force that initialisation now
		// while it's protected by our LRUCache mutex, freeing OpenColorIOTransform
		// nodes from worrying about it later.
		config->getDefaultDisplay();
		return config;
	},
	1000
);

IECore::InternedString variableName( const std::string &name )
{
	return g_ocioStringVarPrefix + name;
}

} // namespace

void GafferImage::OpenColorIOAlgo::setConfig( Gaffer::Context *context, const std::string &configFileName )
{
	context->set( g_ocioConfigContextName, configFileName );
}

void GafferImage::OpenColorIOAlgo::setConfig( Gaffer::Context::EditableScope &context, const std::string *configFileName )
{
	context.set( g_ocioConfigContextName, configFileName );
}

const std::string &GafferImage::OpenColorIOAlgo::getConfig( const Gaffer::Context *context )
{
	return context->get<string>( g_ocioConfigContextName, g_emptyString );
}

void GafferImage::OpenColorIOAlgo::setWorkingSpace( Gaffer::Context *context, const std::string &colorSpace )
{
	context->set( g_ocioWorkingSpaceContextName, colorSpace );
}

void GafferImage::OpenColorIOAlgo::setWorkingSpace( Gaffer::Context::EditableScope &context, const std::string *colorSpace )
{
	context.set( g_ocioWorkingSpaceContextName, colorSpace );
}

const std::string &GafferImage::OpenColorIOAlgo::getWorkingSpace( const Gaffer::Context *context )
{
	return context->get<string>( g_ocioWorkingSpaceContextName, g_sceneLinearString );
}

void GafferImage::OpenColorIOAlgo::addVariable( Gaffer::Context *context, const std::string &name, const std::string &value )
{
	context->set( variableName( name ), value );
}

void GafferImage::OpenColorIOAlgo::addVariable( Gaffer::Context::EditableScope &context, const std::string &name, const std::string *value )
{
	context.set( variableName( name ), value );
}

const std::string &GafferImage::OpenColorIOAlgo::getVariable( const Gaffer::Context *context, const std::string &name )
{
	return context->get<string>( variableName( name ), g_emptyString );
}

void GafferImage::OpenColorIOAlgo::removeVariable( Gaffer::Context *context, const std::string &name )
{
	context->remove( variableName( name ) );
}

void GafferImage::OpenColorIOAlgo::removeVariable( Gaffer::Context::EditableScope &context, const std::string &name )
{
	context.remove( variableName( name ) );
}

std::vector<std::string> GafferImage::OpenColorIOAlgo::variables( const Gaffer::Context *context )
{
	vector<IECore::InternedString> contextVariables;
	context->names( contextVariables );

	vector<string> result;
	for( const auto &contextVariable : contextVariables )
	{
		if( boost::starts_with( contextVariable.string(), g_ocioStringVarPrefix ) )
		{
			result.push_back( contextVariable.string().substr( g_ocioStringVarPrefix.size() ) );
		}
	}
	return result;
}

OCIO_NAMESPACE::ConstConfigRcPtr GafferImage::OpenColorIOAlgo::currentConfig()
{
	const Gaffer::Context *context = Gaffer::Context::current();
	return g_configCache.get( context->substitute( getConfig( context ) ) );
}

IECore::MurmurHash GafferImage::OpenColorIOAlgo::currentConfigHash()
{
	const Gaffer::Context *context = Gaffer::Context::current();
	IECore::MurmurHash result;
	result.append( context->substitute( getConfig( context ) ) );
	return result;
}

GafferImage::OpenColorIOAlgo::ConfigAndContext GafferImage::OpenColorIOAlgo::currentConfigAndContext()
{
	const Gaffer::Context *gafferContext = Gaffer::Context::current();
	OCIO_NAMESPACE::ConstConfigRcPtr config = g_configCache.get( gafferContext->substitute( getConfig( gafferContext ) ) );

	OCIO_NAMESPACE::ConstContextRcPtr context = config->getCurrentContext();
	OCIO_NAMESPACE::ContextRcPtr mutableContext;

	/// \todo Consider possible optimisations :
	///
	/// - If `config->getEnvironmentMode() == ENV_ENVIRONMENT_LOAD_PREDEFINED`
	///   then we could avoid iterating over all Gaffer context variables, and
	///   instead just do lookups on the specific variables declared by the config.
	/// - We could cache ConstContextRcPtrs so we don't recreate them each time.
	vector<IECore::InternedString> names;
	gafferContext->names( names );
	for( const auto &n : names )
	{
		if( !boost::starts_with( n.string(), g_ocioStringVarPrefix ) )
		{
			continue;
		}

		if( !mutableContext )
		{
			mutableContext = context->createEditableCopy();
			context = mutableContext;
		}

		const string value = gafferContext->substitute( gafferContext->get<string>( n ) );
		mutableContext->setStringVar(
			n.c_str() + g_ocioStringVarPrefix.size(),
			value.c_str()
		);
	}

	return { config, context };
}

IECore::MurmurHash GafferImage::OpenColorIOAlgo::currentConfigAndContextHash()
{
	const Gaffer::Context *context = Gaffer::Context::current();

	vector<IECore::InternedString> names;
	context->names( names );
	IECore::MurmurHash result;

	for( const auto &n : names )
	{
		if( n == g_ocioConfigContextName || boost::starts_with( n.string(), g_ocioStringVarPrefix ) )
		{
			result.append( context->substitute( context->get<string>( n ) ) );
		}
	}
	return result;
}
