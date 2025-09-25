//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2024, Cinesite VFX Ltd. All rights reserved.
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

#include "GafferSceneUI/Private/InspectorColumn.h"
#include "GafferSceneUI/Private/ParameterInspector.h"

#include "GafferUI/PathColumn.h"

#include "Gaffer/ScriptNode.h"

#include "IECoreScene/ShaderNetwork.h"

#include "IECore/CamelCase.h"
#include "IECore/SimpleTypedData.h"

using namespace Gaffer;
using namespace GafferUI;
using namespace GafferScene;
using namespace GafferSceneUI::Private;

namespace
{

const boost::container::flat_map<int, ConstColor4fDataPtr> g_sourceTypeColors = {
{ (int)Inspector::Result::SourceType::Upstream, nullptr },
{ (int)Inspector::Result::SourceType::EditScope, new Color4fData( Imath::Color4f( 48, 100, 153, 150 ) / 255.0f ) },
{ (int)Inspector::Result::SourceType::Downstream, new Color4fData( Imath::Color4f( 239, 198, 24, 104 ) / 255.0f ) },
{ (int)Inspector::Result::SourceType::Other, nullptr },
};
const Color4fDataPtr g_fallbackValueForegroundColor = new Color4fData( Imath::Color4f( 163, 163, 163, 255 ) / 255.0f );
const ConstStringDataPtr g_missingOutputShader = new StringData( "Missing output shader" );
const StringDataPtr g_shaderConnectionIcon = new StringData( "sceneInspectorShaderConnection.png" );

}  // namespace

//////////////////////////////////////////////////////////////////////////
// InspectorColumn
//////////////////////////////////////////////////////////////////////////

InspectorColumn::InspectorColumn( GafferSceneUI::Private::InspectorPtr inspector, const std::string &columnName, const std::string &columnToolTip, PathColumn::SizeMode sizeMode )
	:	InspectorColumn( inspector, PathColumn::CellData( headerValue( columnName != "" ? columnName : inspector->name() ), nullptr, nullptr, new IECore::StringData( columnToolTip ) ), sizeMode )
{
}

InspectorColumn::InspectorColumn( GafferSceneUI::Private::InspectorPtr inspector, const CellData &headerData, PathColumn::SizeMode sizeMode )
	:	PathColumn( sizeMode ), m_inspector( inspector ), m_headerData( headerData ), m_contextProperty( "inspector:context" )
{
	inspector->dirtiedSignal().connect( boost::bind( &InspectorColumn::inspectorDirtied, this ) );
}

InspectorColumn::InspectorColumn( IECore::InternedString inspectorProperty, const CellData &headerData, IECore::InternedString contextProperty, PathColumn::SizeMode sizeMode )
	:	PathColumn( sizeMode ), m_inspector( inspectorProperty ), m_headerData( headerData ), m_contextProperty( contextProperty )
{
}

GafferSceneUI::Private::ConstInspectorPtr InspectorColumn::inspector( const Gaffer::Path &path, const IECore::Canceller *canceller ) const
{
	if( auto i = std::get_if<InspectorPtr>( &m_inspector ) )
	{
		return *i;
	}

	return IECore::runTimeCast<const Inspector>( path.property( std::get<InternedString>( m_inspector ), canceller ) );
}

GafferSceneUI::Private::Inspector::ResultPtr InspectorColumn::inspect( const Gaffer::Path &path, const IECore::Canceller *canceller ) const
{
	ConstInspectorPtr i = inspector( path, canceller );
	if( !i )
	{
		return nullptr;
	}

	ConstContextPtr context = inspectorContext( path, canceller );
	if( !context )
	{
		return nullptr;
	}

	std::variant<std::monostate, Context::Scope, Context::EditableScope> scopedContext;
	if( canceller )
	{
		scopedContext.emplace<Context::EditableScope>( context.get() ).setCanceller( canceller );
	}
	else
	{
		scopedContext.emplace<Context::Scope>( context.get() );
	}

	return i->inspect();
}

Gaffer::PathPtr InspectorColumn::historyPath( const Gaffer::Path &path, const IECore::Canceller *canceller ) const
{
	ConstInspectorPtr i = inspector( path, canceller );
	if( !i )
	{
		return nullptr;
	}

	ConstContextPtr context = inspectorContext( path, canceller );
	if( !context )
	{
		return nullptr;
	}

	std::variant<std::monostate, Context::Scope, Context::EditableScope> scopedContext;
	if( canceller )
	{
		scopedContext.emplace<Context::EditableScope>( context.get() ).setCanceller( canceller );
	}
	else
	{
		scopedContext.emplace<Context::Scope>( context.get() );
	}

	return i->historyPath();
}

Gaffer::ConstContextPtr InspectorColumn::inspectorContext( const Gaffer::Path &path, const IECore::Canceller *canceller ) const
{
	return path.contextProperty( m_contextProperty, canceller );
}

PathColumn::CellData InspectorColumn::cellData( const Gaffer::Path &path, const IECore::Canceller *canceller ) const
{
	Inspector::ConstResultPtr inspectorResult = inspect( path, canceller );
	return cellDataFromInspection( inspectorResult.get() );
}

PathColumn::CellData InspectorColumn::headerData( const IECore::Canceller *canceller ) const
{
	return m_headerData;
}

void InspectorColumn::inspectorDirtied()
{
	changedSignal()( this );
}

IECore::ConstStringDataPtr InspectorColumn::headerValue( const std::string &columnName )
{
	if( columnName.find( ' ' ) != std::string::npos )
	{
		// Names already containing spaces are considered
		// to be already formatted and are left as-is.
		return new StringData( columnName );
	}

	std::string name = columnName;
	// Convert from snake case and/or camel case to UI case.
	if( name.find( '_' ) != std::string::npos )
	{
		std::replace( name.begin(), name.end(), '_', ' ' );
		name = CamelCase::fromSpaced( name );
	}
	return new StringData( CamelCase::toSpaced( name ) );
}

PathColumn::CellData InspectorColumn::cellDataFromValue( const IECore::Object *value )
{
	if( auto connectionSource = ParameterInspector::connectionSource( value ) )
	{
		return CellData(
			new StringData( connectionSource.shader.string() + "." + connectionSource.name.string() ),
			g_shaderConnectionIcon
		);
	}
	else if( const auto shaderNetwork = runTimeCast<const IECoreScene::ShaderNetwork>( value ) )
	{
		/// \todo We don't really want InspectorColumn to know about scene
		/// types. At some point we should probably add a registry of converters
		/// somewhere. Or perhaps if InspectorColumn moves to GafferUI, we would
		/// just derive a specialisation from it in GafferSceneUI.
		const IECoreScene::Shader *shader = shaderNetwork->outputShader();
		return CellData( shader ? new StringData( shader->getName() ) : g_missingOutputShader );
	}
	else if( const auto shader = runTimeCast<const IECoreScene::Shader>( value ) )
	{
		return CellData( new StringData( shader->getName() ) );
	}
	else if( const auto data = runTimeCast<const IECore::Data>( value ) )
	{
		CellData result( data );
		/// \todo Should PathModel create a decoration automatically when we
		/// return a colour for `Role::Value`?
		result.icon = runTimeCast<const Color3fData>( data );
		if( !result.icon )
		{
			result.icon = runTimeCast<const Color4fData>( data );
		}
		return result;
	}

	return CellData();
}

PathColumn::CellData InspectorColumn::cellDataFromInspection( const GafferSceneUI::Private::Inspector::Result *inspection ) const
{
	CellData result;
	if( !inspection )
	{
		return result;
	}

	result = cellDataFromValue( inspection->value() );

	result.background = g_sourceTypeColors.at( (int)inspection->sourceType() );
	std::string toolTip;
	if( inspection->fallbackDescription().size() )
	{
		toolTip = "Source : " + inspection->fallbackDescription();
		result.foreground = g_fallbackValueForegroundColor;
	}
	else if( const auto source = inspection->source() )
	{
		toolTip = "Source : " + source->relativeName( source->ancestor<ScriptNode>() );
	}

	/// \todo Should we have the ability to create read-only columns?
	if( inspection->editable() )
	{
		toolTip += !toolTip.empty() ? "\n\n" : "";
		if( runTimeCast<const IECore::BoolData>( result.value ) )
		{
			toolTip += "Double-click to toggle";
		}
		else
		{
			toolTip += "Double-click to edit";
		}
	}

	if( !toolTip.empty() )
	{
		result.toolTip = new StringData( toolTip );
	}

	return result;
}
