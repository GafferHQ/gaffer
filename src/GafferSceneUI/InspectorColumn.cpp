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

#include "GafferUI/PathColumn.h"

#include "Gaffer/ScriptNode.h"

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
{ (int)Inspector::Result::SourceType::Fallback, nullptr },
};
const Color4fDataPtr g_fallbackValueForegroundColor = new Color4fData( Imath::Color4f( 163, 163, 163, 255 ) / 255.0f );

}  // namespace

//////////////////////////////////////////////////////////////////////////
// InspectorColumn
//////////////////////////////////////////////////////////////////////////

InspectorColumn::InspectorColumn( GafferSceneUI::Private::InspectorPtr inspector, const std::string &columnName, const std::string &columnToolTip, PathColumn::SizeMode sizeMode )
	:	InspectorColumn( inspector, PathColumn::CellData( headerValue( columnName != "" ? columnName : inspector->name() ), nullptr, nullptr, new IECore::StringData( columnToolTip ) ), sizeMode )
{
}

InspectorColumn::InspectorColumn( GafferSceneUI::Private::InspectorPtr inspector, const CellData &headerData, PathColumn::SizeMode sizeMode )
	:	PathColumn( sizeMode ), m_inspector( inspector ), m_headerData( headerData )
{
	m_inspector->dirtiedSignal().connect( boost::bind( &InspectorColumn::inspectorDirtied, this ) );
}

GafferSceneUI::Private::Inspector *InspectorColumn::inspector() const
{
	return m_inspector.get();
}

PathColumn::CellData InspectorColumn::cellData( const Gaffer::Path &path, const IECore::Canceller *canceller ) const
{
	CellData result;

	const ContextPtr inspectionContext = path.inspectionContext( canceller );
	if( !inspectionContext )
	{
		return result;
	}

	Context::Scope scope( inspectionContext.get() );
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
	std::string toolTip;
	if( inspectorResult->sourceType() == Inspector::Result::SourceType::Fallback )
	{
		toolTip = "Source : " + inspectorResult->fallbackDescription();
		result.foreground = g_fallbackValueForegroundColor;
	}
	else if( const auto source = inspectorResult->source() )
	{
		toolTip = "Source : " + source->relativeName( source->ancestor<ScriptNode>() );
	}

	/// \todo Should we have the ability to create read-only columns?
	if( inspectorResult->editable() )
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
