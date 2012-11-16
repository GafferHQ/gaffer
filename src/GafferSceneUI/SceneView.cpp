//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2012, John Haddon. All rights reserved.
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

#include "Gaffer/Context.h"
#include "GafferScene/SceneProcedural.h"
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
		m_renderableGadget( new RenderableGadget ),
		m_expandedPaths( new PathMatcherData() )
{
	View3D::inPlug<ScenePlug>()->setInput( inPlug );
	viewportGadget()->setChild( m_renderableGadget );

	viewportGadget()->keyPressSignal().connect( boost::bind( &SceneView::keyPress, this, ::_1, ::_2 ) );
}

SceneView::~SceneView()
{
}

void SceneView::updateFromPlug()
{
	SceneProceduralPtr p = new SceneProcedural( inPlug<ScenePlug>(), getContext(), "/", m_expandedPaths );
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
	PathMatcher &expandedPaths = m_expandedPaths->writable();
	
	bool needUpdate = false;
	for( RenderableGadget::Selection::const_iterator it = selection.begin(), eIt = selection.end(); it != eIt; it++ )
	{
		if( expandedPaths.addPath( *it ) )
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
		updateRequestSignal()( this );
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
	PathMatcher &expandedPaths = m_expandedPaths->writable();
	
	for( RenderableGadget::Selection::const_iterator it = selection.begin(), eIt = selection.end(); it != eIt; it++ )
	{
		if( !expandedPaths.removePath( *it ) )
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
			expandedPaths.removePath( parentPath );
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

	updateRequestSignal()( this );
}
