//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2021, Cinesite VFX Ltd. All rights reserved.
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

#include "boost/python.hpp"

#include "LightEditorBinding.h"

#include "GafferSceneUI/Private/Inspector.h"

#include "GafferScene/ScenePath.h"
#include "GafferScene/ScenePlug.h"

#include "GafferUI/PathColumn.h"

#include "Gaffer/Context.h"
#include "Gaffer/Metadata.h"
#include "Gaffer/ScriptNode.h"

#include "IECoreScene/ShaderNetwork.h"

#include "IECorePython/RefCountedBinding.h"

#include "IECore/CamelCase.h"

#include "boost/algorithm/string/predicate.hpp"

using namespace std;
using namespace boost::python;
using namespace IECore;
using namespace IECoreScene;
using namespace Gaffer;
using namespace GafferUI;
using namespace GafferScene;
using namespace GafferSceneUI::Private;

//////////////////////////////////////////////////////////////////////////
// Custom column types. We define these privately here because they're
// not useful from C++, and keeping them private allows us to change
// implementation without worrying about ABI breaks.
//////////////////////////////////////////////////////////////////////////

namespace
{

ConstStringDataPtr g_emptyLocation = new StringData( "emptyLocation.png" );

class LocationNameColumn : public StandardPathColumn
{

	public :

		IE_CORE_DECLAREMEMBERPTR( LocationNameColumn )

		LocationNameColumn()
			:	StandardPathColumn( "Name", "name" )
		{
		}

		CellData cellData( const Gaffer::Path &path, const IECore::Canceller *canceller ) const override
		{
			CellData result = StandardPathColumn::cellData( path, canceller );

			auto scenePath = IECore::runTimeCast<const ScenePath>( &path );
			if( !scenePath )
			{
				return result;
			}

			Context::EditableScope scope( scenePath->getContext() );
			scope.setCanceller( canceller );

			ConstCompoundObjectPtr attributes;
			try
			{
				attributes = scenePath->getScene()->fullAttributes( scenePath->names() );
			}
			catch( const std::exception &e )
			{
				result.icon = new IECore::StringData( "errorSmall.png" );
				result.toolTip = new IECore::StringData( e.what() );
				return result;
			}

			for( const auto &attribute : attributes->members() )
			{
				if( attribute.first != "light" && !boost::ends_with( attribute.first.c_str(), ":light" ) )
				{
					continue;
				}
				const auto *shaderNetwork = IECore::runTimeCast<const ShaderNetwork>( attribute.second.get() );
				if( !shaderNetwork )
				{
					continue;
				}

				const IECoreScene::Shader *lightShader = shaderNetwork->outputShader();
				const string metadataTarget = lightShader->getType() + ":" + lightShader->getName();
				ConstStringDataPtr lightType = Metadata::value<StringData>( metadataTarget, "type" );
				if( !lightType )
				{
					continue;
				}

				result.icon = new StringData( lightType->readable() + "Light.png" );
			}

			/// \todo Add support for icons based on object type. We don't want to have
			/// to compute the object itself for that though, so maybe we need to add
			/// `ScenePlug::objectTypePlug()`?

			return result;
		}

};

const boost::container::flat_map<int, ConstColor4fDataPtr> g_sourceTypeColors = {
	{ (int)Inspector::Result::SourceType::Upstream, nullptr },
	{ (int)Inspector::Result::SourceType::EditScope, new Color4fData( Imath::Color4f( 48, 100, 153, 150 ) / 255.0f ) },
	{ (int)Inspector::Result::SourceType::Downstream, new Color4fData( Imath::Color4f( 239, 198, 24, 104 ) / 255.0f ) },
	{ (int)Inspector::Result::SourceType::Other, nullptr },
};

class InspectorColumn : public PathColumn
{

	public :

		IE_CORE_DECLAREMEMBERPTR( InspectorColumn )

		InspectorColumn( GafferSceneUI::Private::InspectorPtr inspector, const std::string &columnName )
			:	m_inspector( inspector ), m_headerValue( headerValue( columnName != "" ? columnName : inspector->name() ) )
		{
			m_inspector->dirtiedSignal().connect( boost::bind( &InspectorColumn::inspectorDirtied, this ) );
		}

		GafferSceneUI::Private::Inspector *inspector()
		{
			return m_inspector.get();
		}

		CellData cellData( const Gaffer::Path &path, const IECore::Canceller *canceller ) const override
		{
			CellData result;

			auto scenePath = runTimeCast<const ScenePath>( &path );
			if( !scenePath )
			{
				return result;
			}

			ScenePlug::PathScope scope( scenePath->getContext(), &scenePath->names() );
			scope.setCanceller( canceller );

			Inspector::ConstResultPtr inspectorResult = m_inspector->inspect();
			if( !inspectorResult )
			{
				return result;
			}

			result.value = runTimeCast<const IECore::Data>( inspectorResult->value() );
			/// \todo Should PathModel create a decoration automatically when we
			/// return a colour for `Role::Value`?
			result.icon = runTimeCast<const Color3fData>( inspectorResult->value() );
			result.background = g_sourceTypeColors.at( (int)inspectorResult->sourceType() );
			if( auto source = inspectorResult->source() )
			{
				result.toolTip = new StringData( "Source : " + source->relativeName( source->ancestor<ScriptNode>() ) );
			}

			return result;
		}

		CellData headerData( const IECore::Canceller *canceller ) const override
		{
			return CellData( m_headerValue );
		}

	private :

		void inspectorDirtied()
		{
			changedSignal()( this );
		}

		static IECore::ConstStringDataPtr headerValue( const std::string &inspectorName )
		{
			std::string name = inspectorName;
			// Convert from snake case and/or camel case to UI case.
			if( name.find( '_' ) != std::string::npos )
			{
				std::replace( name.begin(), name.end(), '_', ' ' );
				name = CamelCase::fromSpaced( name );
			}
			return new StringData( CamelCase::toSpaced( name ) );
		}

		const InspectorPtr m_inspector;
		const ConstStringDataPtr m_headerValue;

};

PathColumn::CellData headerDataWrapper( PathColumn &pathColumn, const Canceller *canceller )
{
	IECorePython::ScopedGILRelease gilRelease;
	return pathColumn.headerData( canceller );
}

} // namespace

//////////////////////////////////////////////////////////////////////////
// Bindings
//////////////////////////////////////////////////////////////////////////

void GafferSceneUIModule::bindLightEditor()
{

	IECorePython::RefCountedClass<LocationNameColumn, GafferUI::PathColumn>( "_LightEditorLocationNameColumn" )
		.def( init<>() )
	;

	IECorePython::RefCountedClass<InspectorColumn, GafferUI::PathColumn>( "_LightEditorInspectorColumn" )
		.def( init<GafferSceneUI::Private::InspectorPtr, const std::string &>(
			(
				arg_( "inspector" ),
				arg_( "columName" ) = ""
			)
		) )
		.def( "inspector", &InspectorColumn::inspector, return_value_policy<IECorePython::CastToIntrusivePtr>() )
		.def( "headerData", &headerDataWrapper, ( arg_( "canceller" ) = object() ) )
	;

}
