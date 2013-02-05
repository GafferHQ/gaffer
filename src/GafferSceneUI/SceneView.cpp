//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2012-2013, John Haddon. All rights reserved.
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

#include "boost/bind.hpp"
#include "boost/bind/placeholders.hpp"

#include "IECore/ParameterisedProcedural.h"
#include "IECore/VectorTypedData.h"

#include "Gaffer/Context.h"
#include "Gaffer/BlockedConnection.h"

#include "GafferScene/SceneProcedural.h"
#include "GafferScene/PathMatcherData.h"

#include "GafferSceneUI/SceneView.h"

using namespace std;
using namespace IECore;
using namespace Gaffer;
using namespace GafferUI;
using namespace GafferScene;
using namespace GafferSceneUI;

//////////////////////////////////////////////////////////////////////////
// Implementation of a ParameterisedProcedural wrapping a SceneProcedural.
// We need this to allow us to use the RenderableGadget for doing our
// display.
/// \todo Build our own scene representation.
//////////////////////////////////////////////////////////////////////////

class WrappingProcedural : public IECore::ParameterisedProcedural
{

	public :

		WrappingProcedural( SceneProceduralPtr sceneProcedural )
			:	ParameterisedProcedural( "" ), m_sceneProcedural( sceneProcedural )
		{
		}

	protected :
	
		virtual Imath::Box3f doBound( ConstCompoundObjectPtr args ) const
		{
			return m_sceneProcedural->bound();
		}

		virtual void doRender( RendererPtr renderer, ConstCompoundObjectPtr args ) const
		{
			m_sceneProcedural->render( renderer );
		}

	private :
	
		SceneProceduralPtr m_sceneProcedural;

};

IE_CORE_DECLAREPTR( WrappingProcedural );

//////////////////////////////////////////////////////////////////////////
// SceneView implementation
//////////////////////////////////////////////////////////////////////////

IE_CORE_DEFINERUNTIMETYPED( SceneView );

SceneView::ViewDescription<SceneView> SceneView::g_viewDescription( GafferScene::ScenePlug::staticTypeId() );

SceneView::SceneView( GafferScene::ScenePlugPtr inPlug )
	:	View3D( staticTypeName(), new GafferScene::ScenePlug() ),
		m_renderableGadget( new RenderableGadget )
{
	View3D::inPlug<ScenePlug>()->setInput( inPlug );
	viewportGadget()->setChild( m_renderableGadget );

	m_selectionChangedConnection = m_renderableGadget->selectionChangedSignal().connect( boost::bind( &SceneView::selectionChanged, this, ::_1 ) );
	viewportGadget()->keyPressSignal().connect( boost::bind( &SceneView::keyPress, this, ::_1, ::_2 ) );
}

SceneView::~SceneView()
{
}

void SceneView::contextChanged( const IECore::InternedString &name )
{
	if( name.value() == "ui:scene:selectedPaths" )
	{
		// if only the selection has changed then we can just update the selection
		// on our existing scene representation.
		const StringVectorData *sc = getContext()->get<StringVectorData>( "ui:scene:selectedPaths" );
		RenderableGadget::Selection sr;
		sr.insert( sc->readable().begin(), sc->readable().end() );

		BlockedConnection blockedConnection( m_selectionChangedConnection );
		m_renderableGadget->setSelection( sr );
		return;
	}
	
	if(
		name.value().compare( 0, 3, "ui:" ) == 0 &&
		name.value() != "ui:scene:expandedPaths"
	)
	{
		// if it's just a ui context entry that has changed, and it doesn't
		// affect our expansion, then early out.
		return;
	}
	
	// the context change might affect the scene itself, so we must
	// schedule an update.
	updateRequestSignal()( this );
}

void SceneView::update()
{	
	std::cerr << "SCENEVIEW UPDATE" << std::endl;
	SceneProceduralPtr p = new SceneProcedural( inPlug<ScenePlug>(), getContext(), "/", expandedPaths() );
	WrappingProceduralPtr wp = new WrappingProcedural( p );
	
	bool hadRenderable = m_renderableGadget->getRenderable();
	m_renderableGadget->setRenderable( wp );
	if( !hadRenderable )
	{
		viewportGadget()->frame( m_renderableGadget->bound() );
	}
}

Imath::Box3f SceneView::framingBound() const
{
	Imath::Box3f b = m_renderableGadget->selectionBound();
	if( !b.isEmpty() )
	{
		return b;
	}
	return View3D::framingBound();
}

void SceneView::selectionChanged( GafferUI::RenderableGadgetPtr renderableGadget )
{
	BlockedConnection blockedConnection( contextChangedConnection() );
	transferSelectionToContext();
}

bool SceneView::keyPress( GafferUI::GadgetPtr gadget, const GafferUI::KeyEvent &event )
{
	if( event.key == "Down" )
	{
		expandSelection();
		return true;
	}
	else if( event.key == "Up" )
	{
		collapseSelection();	
		return true;
	}
	
	return false;
}

void SceneView::expandSelection()
{
	RenderableGadget::Selection &selection = m_renderableGadget->getSelection();
	
	vector<string> pathsToSelect;
	vector<const string *> pathsToDeselect;
	IECore::PathMatcherData *expandedData = expandedPaths();
	PathMatcher &expanded = expandedData->writable();
	
	bool needUpdate = false;
	for( RenderableGadget::Selection::const_iterator it = selection.begin(), eIt = selection.end(); it != eIt; it++ )
	{
		if( expanded.addPath( *it ) )
		{
			needUpdate = true;
			ConstStringVectorDataPtr childNamesData = inPlug<ScenePlug>()->childNames( *it );
			const vector<string> &childNames = childNamesData->readable();
			if( childNames.size() )
			{
				pathsToDeselect.push_back( &(*it) );
				for( vector<string>::const_iterator cIt = childNames.begin(), ceIt = childNames.end(); cIt != ceIt; cIt++ )
				{
					if( *(*it).rbegin() != '/' )
					{
						pathsToSelect.push_back( *it + "/" + *cIt );
					}
					else
					{
						pathsToSelect.push_back( *it + *cIt );
					}
				}
			}
		}
	}
	
	for( vector<string>::const_iterator it = pathsToSelect.begin(), eIt = pathsToSelect.end(); it != eIt; it++ )
	{
		selection.insert( *it );
	}
	for( vector<const string *>::const_iterator it = pathsToDeselect.begin(), eIt = pathsToDeselect.end(); it != eIt; it++ )
	{
		selection.erase( **it );
	}
	
	if( needUpdate )
	{
		// this will trigger update() via contextChanged().
		
		//THIS ISN'T TRIGGERING BECAUSE WE JUST MODIFIED THE INTERNAL CONTEXT
		//VALUE IN PLACE SO CONTEXT::SET DOESN'T DETECT A CHANGE
		
		getContext()->set( "ui:scene:expandedPaths", expandedData );
		// and this will trigger a selection update also via contextChanged().
		transferSelectionToContext();
	}
}

void SceneView::collapseSelection()
{
	RenderableGadget::Selection &selection = m_renderableGadget->getSelection();
	if( !selection.size() )
	{
		return;
	}
	
	set<string> pathsToSelect;
	vector<const string *> pathsToDeselect;
	IECore::PathMatcherData *expandedData = expandedPaths();
	PathMatcher &expanded = expandedData->writable();
	
	for( RenderableGadget::Selection::const_iterator it = selection.begin(), eIt = selection.end(); it != eIt; it++ )
	{
		if( !expanded.removePath( *it ) )
		{
			if( *it == "/" )
			{
				continue;
			}
			pathsToDeselect.push_back( &(*it) );
			std::string parentPath( *it, 0, it->rfind( '/' ) );
			if( parentPath == "" )
			{
				parentPath = "/";
			}
			expanded.removePath( parentPath );
			pathsToSelect.insert( parentPath );
		}
	}
	
	for( set<string>::const_iterator it = pathsToSelect.begin(), eIt = pathsToSelect.end(); it != eIt; it++ )
	{
		selection.insert( *it );
	}
	for( vector<const string *>::const_iterator it = pathsToDeselect.begin(), eIt = pathsToDeselect.end(); it != eIt; it++ )
	{
		selection.erase( **it );
	}

	// this will trigger update() via contextChanged().
	getContext()->set( "ui:scene:expandedPaths", expandedData );
	// and this will trigger a selection update also via contextChanged().
	transferSelectionToContext();
}

void SceneView::transferSelectionToContext()
{
	/// \todo If RenderableGadget used PathMatcherData, then we might not need
	/// to copy data here.
	const RenderableGadget::Selection &selection = m_renderableGadget->getSelection();
	StringVectorDataPtr s = new StringVectorData();
	s->writable().insert( s->writable().end(), selection.begin(), selection.end() );
	getContext()->set( "ui:scene:selectedPaths", s.get() );
}

IECore::PathMatcherData *SceneView::expandedPaths()
{
	const IECore::PathMatcherData *m = getContext()->get<IECore::PathMatcherData>( "ui:scene:expandedPaths", 0 );
	if( !m )
	{
		getContext()->set( "ui:scene:expandedPaths", new IECore::PathMatcherData );
		m = getContext()->get<IECore::PathMatcherData>( "ui:scene:expandedPaths" );
	}
	return const_cast<IECore::PathMatcherData *>( m );
}
