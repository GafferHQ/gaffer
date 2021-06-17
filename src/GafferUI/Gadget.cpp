//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2011-2012, John Haddon. All rights reserved.
//  Copyright (c) 2011-2013, Image Engine Design Inc. All rights reserved.
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

#include "GafferUI/Gadget.h"

#include "GafferUI/Style.h"
#include "GafferUI/ViewportGadget.h"

#include "IECoreGL/GL.h"
#include "IECoreGL/NameStateComponent.h"
#include "IECoreGL/Selector.h"

#include "IECore/SimpleTypedData.h"

#include "OpenEXR/ImathBoxAlgo.h"

#include "boost/bind.hpp"
#include "boost/lexical_cast.hpp"

using namespace GafferUI;
using namespace Imath;
using namespace std;

GAFFER_GRAPHCOMPONENT_DEFINE_TYPE( Gadget );

//////////////////////////////////////////////////////////////////////////
// Gadget::Signals
//
// We allocate these lazily because they have a significant overhead
// in both memory and construction time, and for many Gadget
// instances they are never actually used.
//////////////////////////////////////////////////////////////////////////

struct Gadget::Signals : boost::noncopyable
{

	VisibilityChangedSignal visibilityChangedSignal;

	ButtonSignal buttonPressSignal;
	ButtonSignal buttonReleaseSignal;
	ButtonSignal buttonDoubleClickSignal;
	ButtonSignal wheelSignal;

	EnterLeaveSignal enterSignal;
	EnterLeaveSignal leaveSignal;
	ButtonSignal mouseMoveSignal;

	DragBeginSignal dragBeginSignal;
	DragDropSignal dragEnterSignal;
	DragDropSignal dragMoveSignal;
	DragDropSignal dragLeaveSignal;
	DragDropSignal dragEndSignal;
	DragDropSignal dropSignal;

	KeySignal keyPressSignal;
	KeySignal keyReleaseSignal;

	// Utility to emit a signal if it has been created, but do nothing
	// if it hasn't.
	template<typename SignalMemberPointer, typename... Args>
	static void emitLazily( Signals *signals, SignalMemberPointer signalMemberPointer, Args&&... args )
	{
		if( !signals )
		{
			return;
		}
		auto &signal = signals->*signalMemberPointer;
		signal( std::forward<Args>( args )... );
	}

};

Gadget::Gadget( const std::string &name )
	:	GraphComponent( name ), m_style( nullptr ), m_visible( true ), m_enabled( true ), m_highlighted( false ), m_layoutDirty( false ), m_toolTip( "" )
{
	std::string n = "__Gaffer::Gadget::" + boost::lexical_cast<std::string>( (size_t)this );
	m_glName = IECoreGL::NameStateComponent::glNameFromName( n, true );
}

GadgetPtr Gadget::select( GLuint id )
{
	const std::string &name = IECoreGL::NameStateComponent::nameFromGLName( id );
	if( name.compare( 0, 18, "__Gaffer::Gadget::" ) )
	{
		return nullptr;
	}
	std::string address = name.c_str() + 18;
	size_t a = boost::lexical_cast<size_t>( address );
	return reinterpret_cast<Gadget *>( a );
}

Gadget::~Gadget()
{
}

bool Gadget::acceptsChild( const Gaffer::GraphComponent *potentialChild ) const
{
	return potentialChild->isInstanceOf( staticTypeId() );
}

bool Gadget::acceptsParent( const Gaffer::GraphComponent *potentialParent ) const
{
	return potentialParent->isInstanceOf( staticTypeId() );
}

void Gadget::setStyle( ConstStylePtr style )
{
	if( style!=m_style )
	{
		if( m_style )
		{
			const_cast<Style *>( m_style.get() )->changedSignal().disconnect( boost::bind( &Gadget::styleChanged, this ) );
		}
		m_style = style;
		if( m_style )
		{
			const_cast<Style *>( m_style.get() )->changedSignal().connect( boost::bind( &Gadget::styleChanged, this ) );
		}
		// Style affects the bounding box of text,
		// so we need Layout rather than just Render.
		dirty( DirtyType::Layout );
	}
}

const Style *Gadget::getStyle() const
{
	return m_style.get();
}

const Style *Gadget::style() const
{
	const Gadget *g = this;
	while( g )
	{
		if( g->m_style )
		{
			return g->m_style.get();
		}
		g = g->parent<Gadget>();
	}
	return Style::getDefaultStyle().get();
}

void Gadget::setVisible( bool visible )
{
	if( visible == m_visible )
	{
		return;
	}
	m_visible = visible;

	Gadget *p = parent<Gadget>();
	if( !p || p->visible() )
	{
		emitDescendantVisibilityChanged();
		Signals::emitLazily( m_signals.get(), &Signals::visibilityChangedSignal, this );
	}
	if( p )
	{
		p->dirty( DirtyType::Layout );
	}
}

void Gadget::emitDescendantVisibilityChanged()
{
	for( Gadget::Iterator it( this ); !it.done(); ++it )
	{
		if( !(*it)->getVisible() )
		{
			// The overally visibility of hidden children
			// is unaffected by parent visibility.
			continue;
		}
		(*it)->emitDescendantVisibilityChanged();
		Signals::emitLazily( (*it)->m_signals.get(), &Signals::visibilityChangedSignal, it->get() );
	}
}

bool Gadget::visible( Gadget *relativeTo ) const
{
	const Gadget *g = this;
	while( g && g != relativeTo )
	{
		if( !g->getVisible() )
		{
			return false;
		}
		g = g->parent<Gadget>();
	}
	return true;
}

Gadget::VisibilityChangedSignal &Gadget::visibilityChangedSignal()
{
	return signals()->visibilityChangedSignal;
}

void Gadget::setEnabled( bool enabled )
{
	if( enabled == m_enabled )
	{
		return;
	}
	m_enabled = enabled;
	dirty( DirtyType::Render );
}

bool Gadget::getEnabled() const
{
	return m_enabled;
}

bool Gadget::enabled( Gadget *relativeTo ) const
{
	const Gadget *g = this;
	while( g && g != relativeTo )
	{
		if( !g->getEnabled() )
		{
			return false;
		}
		g = g->parent<Gadget>();
	}
	return true;
}

void Gadget::setHighlighted( bool highlighted )
{
	if( highlighted == m_highlighted )
	{
		return;
	}

	m_highlighted = highlighted;
	dirty( DirtyType::Render );
}

bool Gadget::getHighlighted() const
{
	return m_highlighted;
}

void Gadget::setTransform( const Imath::M44f &matrix )
{
	if( matrix!=m_transform )
	{
		m_transform = matrix;
		if( auto p = parent<Gadget>() )
		{
			p->dirty( DirtyType::Layout );
		}
	}
}

const Imath::M44f &Gadget::getTransform() const
{
	return m_transform;
}

Imath::M44f Gadget::fullTransform( const Gadget *ancestor ) const
{
	M44f result;
	const Gadget *g = this;
	do
	{
		result *= g->m_transform;
		g = g->parent<Gadget>();
	} while( g && g!=ancestor );

	return result;
}

void Gadget::dirty( DirtyType dirtyType )
{
	Gadget *g = this;
	while( g )
	{
		if( dirtyType == DirtyType::Layout )
		{
			g->m_layoutDirty = true;
		}
		if( dirtyType == DirtyType::Bound )
		{
			// Bounds changes in children require layout updates in parents.
			dirtyType = DirtyType::Layout;
		}
		Gadget *p = g->parent<Gadget>();
		if( !p )
		{
			// Found top level gadget, maybe it's a ViewportGadget
			ViewportGadget *viewportGadget = IECore::runTimeCast<ViewportGadget>( g );
			if( viewportGadget )
			{
				viewportGadget->renderRequestSignal()( viewportGadget );
			}
		}
		g = p;
	}
}

void Gadget::updateLayout() const
{
}

void Gadget::doRenderLayer( Layer layer, const Style *style ) const
{
}

bool Gadget::hasLayer( Layer layer ) const
{
	return true;
}

Imath::Box3f Gadget::bound() const
{
	if( !m_layoutDirty )
	{
		return m_bound;
	}

	updateLayout();
	m_bound = Box3f();
	for( ChildContainer::const_iterator it=children().begin(); it!=children().end(); it++ )
	{
		// cast is safe because of the guarantees acceptsChild() gives us
		const Gadget *c = static_cast<const Gadget *>( it->get() );
		if( !c->getVisible() )
		{
			continue;
		}
		Imath::Box3f b = c->bound();
		b = Imath::transform( b, c->getTransform() );
		m_bound.extendBy( b );
	}

	m_layoutDirty = false;
	return m_bound;
}

Imath::Box3f Gadget::transformedBound() const
{
	Box3f b = bound();
	return transform( b, getTransform() );
}

Imath::Box3f Gadget::transformedBound( const Gadget *ancestor ) const
{
	Box3f b = bound();
	return transform( b, fullTransform( ancestor ) );
}

std::string Gadget::getToolTip( const IECore::LineSegment3f &position ) const
{
	return m_toolTip;
}

void Gadget::setToolTip( const std::string &toolTip )
{
	m_toolTip = toolTip;
}

Gadget::ButtonSignal &Gadget::buttonPressSignal()
{
	return signals()->buttonPressSignal;
}

Gadget::ButtonSignal &Gadget::buttonReleaseSignal()
{
	return signals()->buttonReleaseSignal;
}

Gadget::ButtonSignal &Gadget::buttonDoubleClickSignal()
{
	return signals()->buttonDoubleClickSignal;
}

Gadget::ButtonSignal &Gadget::wheelSignal()
{
	return signals()->wheelSignal;
}

Gadget::EnterLeaveSignal &Gadget::enterSignal()
{
	return signals()->enterSignal;
}

Gadget::EnterLeaveSignal &Gadget::leaveSignal()
{
	return signals()->leaveSignal;
}

Gadget::ButtonSignal &Gadget::mouseMoveSignal()
{
	return signals()->mouseMoveSignal;
}

Gadget::DragBeginSignal &Gadget::dragBeginSignal()
{
	return signals()->dragBeginSignal;
}

Gadget::DragDropSignal &Gadget::dragMoveSignal()
{
	return signals()->dragMoveSignal;
}

Gadget::DragDropSignal &Gadget::dragEnterSignal()
{
	return signals()->dragEnterSignal;
}

Gadget::DragDropSignal &Gadget::dragLeaveSignal()
{
	return signals()->dragLeaveSignal;
}

Gadget::DragDropSignal &Gadget::dropSignal()
{
	return signals()->dropSignal;
}

Gadget::DragDropSignal &Gadget::dragEndSignal()
{
	return signals()->dragEndSignal;
}

Gadget::KeySignal &Gadget::keyPressSignal()
{
	return signals()->keyPressSignal;
}

Gadget::KeySignal &Gadget::keyReleaseSignal()
{
	return signals()->keyReleaseSignal;
}

Gadget::Signals *Gadget::signals()
{
	if( !m_signals )
	{
		m_signals.reset( new Signals );
	}
	return m_signals.get();
}

Gadget::IdleSignal &Gadget::idleSignal()
{
	// Deliberately leaking here, as the alternative is for `g_idleSignal`
	// to be destroyed during shutdown when static destructors are run.
	// Static destructors are run _after_ Python has shut down, so we are
	// not in a position to destroy any slots that might still be holding
	// on to Python objects.
	static IdleSignal *g_idleSignal = new IdleSignal;
	idleSignalAccessedSignal()();
	return *g_idleSignal;
}

Gadget::IdleSignal &Gadget::idleSignalAccessedSignal()
{
	static IdleSignal g_idleSignalAccessedSignal;
	return g_idleSignalAccessedSignal;
}

void Gadget::styleChanged()
{
	dirty( DirtyType::Layout );
}

void Gadget::parentChanged( GraphComponent *oldParent )
{
	GraphComponent::parentChanged( oldParent );

	if( Gadget *oldParentGadget = IECore::runTimeCast<Gadget>( oldParent ) )
	{
		oldParentGadget->dirty( DirtyType::Layout );
	}
	if( Gadget *parentGadget = parent<Gadget>() )
	{
		parentGadget->dirty( DirtyType::Layout );
	}
}
