//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2011, John Haddon. All rights reserved.
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

#ifndef GAFFERUI_GRAPHGADGET_H
#define GAFFERUI_GRAPHGADGET_H

#include "GafferUI/ContainerGadget.h"

namespace Gaffer
{
IE_CORE_FORWARDDECLARE( Node );
IE_CORE_FORWARDDECLARE( Plug );
IE_CORE_FORWARDDECLARE( ScriptNode );
}

namespace GafferUI
{

IE_CORE_FORWARDDECLARE( NodeGadget );
IE_CORE_FORWARDDECLARE( ConnectionGadget );

class GraphGadget : public ContainerGadget
{

	public :

		GraphGadget( Gaffer::NodePtr graphRoot );
		virtual ~GraphGadget();

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( GraphGadget, GraphGadgetTypeId, ContainerGadget );

		NodeGadgetPtr nodeGadget( Gaffer::ConstNodePtr node );
		ConstNodeGadgetPtr nodeGadget( Gaffer::ConstNodePtr node ) const;

	protected :

		void doRender( IECore::RendererPtr renderer ) const;

		void childAdded( GraphComponent *parent, GraphComponent *child );
		void childRemoved( GraphComponent *parent, GraphComponent *child );
		void inputChanged( Gaffer::PlugPtr dstPlug );
		void plugSet( Gaffer::PlugPtr plug );
	
		bool keyPressed( GadgetPtr gadget, const KeyEvent &event );
		
		bool buttonPress( GadgetPtr gadget, const ButtonEvent &event );
		bool buttonRelease( GadgetPtr gadget, const ButtonEvent &event );
		
		IECore::RunTimeTypedPtr dragBegin( GadgetPtr gadget, const ButtonEvent &event );	
		bool dragUpdate( GadgetPtr gadget, const ButtonEvent &event );
		
		void addNodeGadget( Gaffer::Node *node );
		NodeGadget *findNodeGadget( const Gaffer::Node *node ) const;
		void updateNodeGadgetTransform( NodeGadget *nodeGadget );
		
		void addConnectionGadget( Gaffer::Plug *dstPlug );
		ConnectionGadget *connectionGadget( Gaffer::Plug *dstPlug );
		
	private :
	
		Gaffer::ScriptNodePtr script();
	
		Gaffer::Node *m_graphRoot;
		
		typedef std::map<const Gaffer::Node *, NodeGadget *> NodeGadgetMap;
		NodeGadgetMap m_nodeGadgets;
	
		typedef std::map<const Gaffer::Plug *, ConnectionGadget *> ConnectionGadgetMap;
		ConnectionGadgetMap m_connectionGadgets;

		Imath::V2f m_lastDragPosition;
		

};

IE_CORE_DECLAREPTR( GraphGadget );

} // namespace GafferUI

#endif // GAFFERUI_GRAPHGADGET_H
