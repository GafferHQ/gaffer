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

#include "GafferSceneUI/Private/AttributeInspector.h"
#include "GafferSceneUI/Private/Inspector.h"
#include "GafferSceneUI/Private/InspectorColumn.h"
#include "GafferSceneUI/Private/SetMembershipInspector.h"

#include "GafferScene/ScenePath.h"
#include "GafferScene/ScenePlug.h"

#include "GafferUI/PathColumn.h"

#include "Gaffer/Context.h"
#include "Gaffer/Metadata.h"
#include "Gaffer/ScriptNode.h"
#include "Gaffer/TweakPlug.h"

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
const InternedString g_lightFilterSetName( "__lightFilters" );

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
				std::vector<InternedString> tokens;
				StringAlgo::tokenize( attribute.first, ':', tokens );
				if(
					attribute.first != "light" &&
					tokens.back() != "light" &&
					attribute.first != "lightFilter" &&
					( tokens.size() < 2 || tokens[1] != "lightFilter" )
				)
				{
					continue;
				}
				const auto *shaderNetwork = IECore::runTimeCast<const ShaderNetwork>( attribute.second.get() );
				if( !shaderNetwork )
				{
					continue;
				}

				const IECoreScene::Shader *shader = shaderNetwork->outputShader();
				const string metadataTarget = attribute.first.string() + ":" + shader->getName();
				ConstStringDataPtr type = Metadata::value<StringData>( metadataTarget, "type" );
				if( !type )
				{
					continue;
				}

				if( type->readable() == "lightBlocker" )
				{
					if( ConstStringDataPtr blockerTypeParameter = Metadata::value<StringData>( metadataTarget, "typeParameter" ) )
					{
						if( ConstStringDataPtr blockerType = shader->parametersData()->member<StringData>( blockerTypeParameter->readable() ) )
						{
							result.icon = new StringData( blockerType->readable() + "Blocker.png" );
						}
					}
				}
				else
				{
					result.icon = new StringData( type->readable() + "Light.png" );
				}
			}

			/// \todo Add support for icons based on object type. We don't want to have
			/// to compute the object itself for that though, so maybe we need to add
			/// `ScenePlug::objectTypePlug()`?

			return result;
		}

};

class MuteColumn : public InspectorColumn
{

	public :
		IE_CORE_DECLAREMEMBERPTR( MuteColumn )

		MuteColumn( const GafferScene::ScenePlugPtr &scene, const Gaffer::PlugPtr &editScope )
			: InspectorColumn( new GafferSceneUI::Private::AttributeInspector( scene, editScope, "light:mute" ), "Mute" )
		{

		}

		CellData cellData( const Gaffer::Path &path, const IECore::Canceller *canceller ) const override
		{
			CellData result = InspectorColumn::cellData( path, canceller );

			auto scenePath = runTimeCast<const ScenePath>( &path );
			if( !scenePath )
			{
				return result;
			}

			if( auto value = runTimeCast<const BoolData>( result.value ) )
			{
				ScenePlug::PathScope pathScope( scenePath->getContext(), &scenePath->names() );
				pathScope.setCanceller( canceller );

				Inspector::ConstResultPtr inspectorResult = inspector()->inspect();
				if( inspectorResult->sourceType() != Inspector::Result::SourceType::Fallback )
				{
					result.icon = value->readable() ? m_muteIconData : m_unMuteIconData;
				}
				else
				{
					result.icon = value->readable() ? m_muteFadedIconData : m_unMuteFadedIconData;
				}
			}
			if( !result.icon )
			{
				// Use a transparent icon to reserve space in the UI. Without this,
				// the top row will resize when setting the mute value, causing a full
				// table resize.
				if( path.isEmpty() )
				{
					result.icon = m_muteBlankIconName;
				}
				else
				{
					result.icon = m_muteUndefinedIconData;
				}
			}

			result.value = nullptr;

			return result;
		}

	private :

		static IECore::CompoundDataPtr m_muteIconData;
		static IECore::CompoundDataPtr m_unMuteIconData;
		static IECore::CompoundDataPtr m_muteFadedIconData;
		static IECore::CompoundDataPtr m_unMuteFadedIconData;
		static IECore::CompoundDataPtr m_muteUndefinedIconData;
		static IECore::StringDataPtr m_muteBlankIconName;
};

CompoundDataPtr MuteColumn::m_muteIconData = new CompoundData(
	{
		{ InternedString( "state:normal" ), new StringData( "muteLight.png" ) },
		{ InternedString( "state:highlighted" ), new StringData( "muteLightHighlighted.png" ) }
	}
);
CompoundDataPtr MuteColumn::m_unMuteIconData = new CompoundData(
	{
		{ InternedString( "state:normal" ), new StringData( "unMuteLight.png" ) },
		{ InternedString( "state:highlighted" ), new StringData( "unMuteLightHighlighted.png" ) }
	}
);
CompoundDataPtr MuteColumn::m_muteFadedIconData = new CompoundData(
	{
		{ InternedString( "state:normal" ), new StringData( "muteLightFaded.png" ) },
		{ InternedString( "state:highlighted" ), new StringData( "muteLightFadedHighlighted.png" ) }
	}
);
CompoundDataPtr MuteColumn::m_unMuteFadedIconData = new CompoundData(
	{
		{ InternedString( "state:normal" ), new StringData( "unMuteLightFaded.png" ) },
		{ InternedString( "state:highlighted" ), new StringData( "unMuteLightFadedHighlighted.png" ) }
	}
);
CompoundDataPtr MuteColumn::m_muteUndefinedIconData = new CompoundData(
	{
		{ InternedString( "state:normal" ), new StringData( "muteLightUndefined.png" ) },
		{ InternedString( "state:highlighted" ), new StringData( "muteLightFadedHighlighted.png" ) }
	}
);

StringDataPtr MuteColumn::m_muteBlankIconName = new StringData( "muteLightUndefined.png" );

class SetMembershipColumn : public InspectorColumn
{

	public :
		IE_CORE_DECLAREMEMBERPTR( SetMembershipColumn )

		SetMembershipColumn( const GafferScene::ScenePlugPtr &scene, const Gaffer::PlugPtr editScope, const IECore::InternedString &setName, const std::string &columnName )
			: InspectorColumn( new GafferSceneUI::Private::SetMembershipInspector( scene, editScope, setName ), columnName ), m_setName( setName ), m_scene( scene )
		{

		}

		CellData cellData( const Gaffer::Path &path, const IECore::Canceller *canceller ) const override
		{
			CellData result = InspectorColumn::cellData( path, canceller );

			auto scenePath = runTimeCast<const ScenePath>( &path );
			if( !scenePath )
			{
				return result;
			}

			if( auto value = runTimeCast<const BoolData>( result.value ) )
			{
				if( value->readable() )
				{
					ScenePlug::PathScope pathScope( scenePath->getContext(), &scenePath->names() );
					pathScope.setCanceller( canceller );

					Inspector::ConstResultPtr inspectorResult = inspector()->inspect();
					if( inspectorResult->sourceType() != Inspector::Result::SourceType::Fallback )
					{
						result.icon = m_setMemberIconData;
					}
					else
					{
						result.icon = m_setMemberIconFadedData;
					}
				}
			}
			if( !result.icon )
			{
				result.icon = m_setMemberUndefinedIconData;
			}

			result.value = nullptr;

			return result;
		}

		CellData headerData( const IECore::Canceller *canceller ) const override
		{
			CellData result = InspectorColumn::headerData( canceller );

			if( auto sceneInput = m_scene->getInput() )
			{
				auto scriptNode = sceneInput->ancestor<ScriptNode>();

				Context::EditableScope contextScope( scriptNode->context() );
				contextScope.setCanceller( canceller );

				ConstPathMatcherDataPtr setMembersData = m_scene->set( m_setName );
				result.icon = setMembersData->readable().isEmpty() ? m_setEmpty : m_setHasMembers;
			}

			return result;
		}

	private :
		const IECore::InternedString m_setName;
		const GafferScene::ScenePlugPtr m_scene;

		static IECore::CompoundDataPtr m_setMemberIconData;
		static IECore::CompoundDataPtr m_setMemberIconFadedData;
		static IECore::CompoundDataPtr m_setMemberUndefinedIconData;
		static IECore::StringDataPtr m_setHasMembers;
		static IECore::StringDataPtr m_setEmpty;
};

CompoundDataPtr SetMembershipColumn::m_setMemberIconData = new CompoundData(
	{
		{ InternedString( "state:normal" ), new StringData( "setMember.png" ) },
		{ InternedString( "state:highlighted" ), new StringData( "setMemberHighlighted.png" ) }
	}
);

CompoundDataPtr SetMembershipColumn::m_setMemberIconFadedData = new CompoundData(
	{
		{ InternedString( "state:normal" ), new StringData( "setMemberFaded.png" ) },
		{ InternedString( "state:highlighted" ), new StringData( "setMemberFadedHighlighted.png" ) }
	}
);

CompoundDataPtr SetMembershipColumn::m_setMemberUndefinedIconData = new CompoundData(
	{
		{ InternedString( "state:normal" ), new StringData( "muteLightUndefined.png" ) },
		{ InternedString( "state:highlighted" ), new StringData( "setMemberFadedHighlighted.png" ) }
	}
);

StringDataPtr SetMembershipColumn::m_setHasMembers = new StringData( "setMember.png" );
StringDataPtr SetMembershipColumn::m_setEmpty = new StringData( "muteLightUndefined.png" );

} // namespace

//////////////////////////////////////////////////////////////////////////
// Bindings
//////////////////////////////////////////////////////////////////////////

void GafferSceneUIModule::bindLightEditor()
{

	IECorePython::RefCountedClass<LocationNameColumn, GafferUI::PathColumn>( "_LightEditorLocationNameColumn" )
		.def( init<>() )
	;

	IECorePython::RefCountedClass<MuteColumn, GafferSceneUI::Private::InspectorColumn>( "_LightEditorMuteColumn" )
		.def( init<const GafferScene::ScenePlugPtr &, const Gaffer::PlugPtr &>(
			(
				arg_( "scene" ),
				arg_( "editScope" )
			)
		) )
	;

	IECorePython::RefCountedClass<SetMembershipColumn, GafferSceneUI::Private::InspectorColumn>( "_LightEditorSetMembershipColumn" )
		.def( init<const GafferScene::ScenePlugPtr &, const Gaffer::PlugPtr &, const IECore::InternedString &, const std::string &>(
			(
				arg_( "scene" ),
				arg_( "editScope" ),
				arg_( "setName" ),
				arg_( "columnName" )
			)
		) )
	;

}
