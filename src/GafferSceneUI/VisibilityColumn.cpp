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

#include "GafferSceneUI/Private/VisibilityColumn.h"

#include "GafferSceneUI/Private/AttributeInspector.h"

#include "GafferScene/SceneAlgo.h"
#include "GafferScene/ScenePath.h"

#include "IECore/SimpleTypedData.h"

using namespace Gaffer;
using namespace GafferUI;
using namespace GafferScene;
using namespace GafferSceneUI::Private;

namespace
{

ConstStringDataPtr g_locationVisibleIcon = new StringData( "locationVisible.png" );
ConstStringDataPtr g_locationInvisibleIcon = new StringData( "locationInvisible.png" );
ConstStringDataPtr g_locationVisibleTransparentIcon = new StringData( "locationVisibleTransparent.png" );
ConstStringDataPtr g_locationInvisibleTransparentIcon = new StringData( "locationInvisibleTransparent.png" );
ConstStringDataPtr g_locationInvisibleConflictIcon = new StringData( "locationInvisibleConflict.png" );

}

//////////////////////////////////////////////////////////////////////////
// VisibilityColumn
//////////////////////////////////////////////////////////////////////////

VisibilityColumn::VisibilityColumn( const GafferScene::ScenePlugPtr &scene, const Gaffer::PlugPtr &editScope )
	:	InspectorColumn(
			new GafferSceneUI::Private::AttributeInspector( scene, editScope, "scene:visible" ),
			CellData( /* value = */ nullptr, /* icon = */ g_locationVisibleIcon, /* background = */ nullptr, /* tooltip = */ new StringData( "Scene Visibility" ) )
		), m_scene( scene )
{
}

InspectorColumn::CellData VisibilityColumn::cellData( const Gaffer::Path &path, const IECore::Canceller *canceller ) const
{
	CellData result = InspectorColumn::cellData( path, canceller );

	Inspector::ConstResultPtr inspectorResult = inspect( path, canceller );
	if( !inspectorResult )
	{
		return result;
	}

	ConstContextPtr context = inspectorContext( path, canceller );
	if( !context )
	{
		return result;
	}

	Context::Scope scopedContext( context.get() );
	const bool visible = GafferScene::SceneAlgo::visible( m_scene.get(), path.names() );
	const auto visibilityValue = runTimeCast<const BoolData>( inspectorResult->value() );

	std::string toolTip;
	if( inspectorResult->sourceType() == Inspector::Result::SourceType::Fallback )
	{
		result.icon = visible ? g_locationVisibleTransparentIcon : g_locationInvisibleTransparentIcon;
		toolTip = visible ? "Location visible by inheritance." : "Location invisible by inheritance. It will not be rendered, and neither will its descendants.";
	}
	else if( !visible && visibilityValue && visibilityValue->readable() )
	{
		result.icon = g_locationInvisibleConflictIcon;
		toolTip = "Location invisible by inheritance. It will not be rendered, and neither will its descendants.\n\n" \
			"A local scene:visible attribute exists, but is ignored as one or more ancestors are invisible.";
	}
	else
	{
		result.icon = visible ? g_locationVisibleIcon : g_locationInvisibleIcon;
		toolTip = visible ? "Location visible." : "Location invisible. It will not be rendered, and neither will its descendants.";
	}

	result.value = nullptr;

	if( !toolTip.empty() )
	{
		if( auto t = runTimeCast<const StringData>( result.toolTip ) )
		{
			toolTip += "\n\n" + t->readable();
		}
		result.toolTip = new StringData( toolTip );
	}

	return result;
}
