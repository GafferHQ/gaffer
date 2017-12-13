//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2017, Image Engine Design Inc. All rights reserved.
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

#ifndef GAFFERUI_AUXILIARYCONNECTIONSGADGET_H
#define GAFFERUI_AUXILIARYCONNECTIONSGADGET_H

#include "Gaffer/Set.h"

#include "GafferUI/Gadget.h"
#include "GafferUI/Style.h"
#include "GafferUI/AuxiliaryConnectionGadget.h"

namespace Gaffer
{
  IE_CORE_FORWARDDECLARE( Node );
}

namespace GafferUI
{

  IE_CORE_FORWARDDECLARE( GraphGadget );

class AuxiliaryConnectionsGadget : public Gadget
{

public:

  AuxiliaryConnectionsGadget();
  ~AuxiliaryConnectionsGadget();

  IE_CORE_DECLARERUNTIMETYPEDEXTENSION( GafferUI::AuxiliaryConnectionsGadget, AuxiliaryConnectionsGadgetTypeId, Gadget );

  Imath::Box3f bound() const override;

  AuxiliaryConnectionGadget *auxiliaryConnectionGadget( const Gaffer::Plug *dstPlug );
  const AuxiliaryConnectionGadget *auxiliaryConnectionGadget( const Gaffer::Plug *dstPlug ) const;

  size_t auxiliaryConnectionGadgets( const Gaffer::Plug *plug, std::vector<AuxiliaryConnectionGadget *> &connections, const Gaffer::Set *excludedNodes );
  size_t auxiliaryConnectionGadgets( const Gaffer::Plug *plug, std::vector<const AuxiliaryConnectionGadget *> &connections, const Gaffer::Set *excludedNodes ) const;

  size_t auxiliaryConnectionGadgets( const Gaffer::Node *node, std::vector<AuxiliaryConnectionGadget *> &connections, const Gaffer::Set *excludedNodes );
  size_t auxiliaryConnectionGadgets( const Gaffer::Node *node, std::vector<const AuxiliaryConnectionGadget *> &connections, const Gaffer::Set *excludedNodes ) const;

  void markDirty( const Gaffer::Plug *dstPlug );
  void markDirty( ConstNodeGadgetPtr nodeGadget );

  void removeAuxiliaryConnectionGadgets( const NodeGadget *nodeGadget );

  void doRenderLayer( Layer layer, const Style *style ) const override;

 private:

  const GraphGadget *graphGadget() const;

  void addAuxiliaryConnection( const Gaffer::Plug *srcPlug, const Gaffer::Plug *dstPlug );
  void removeAuxiliaryConnection( const Gaffer::Plug *dstPlug );

  // Update all NodeGadgets that were previously flagged as dirty
  void updateAuxiliaryConnections() const;

  AuxiliaryConnectionGadget *findAuxiliaryConnectionGadget( const Gaffer::Plug *plug ) const;

  // This container provides access to AuxiliaryConnectionGadget* either
  // via a pair of NodeGadgets or via a single Plug pointer. This is needed as
  // in some cases it's not possible to retrieve a pair of NodeGadgets in
  // order to remove the respective connection (think plugInputChangedSignals
  // that don't give access to the plug that was part of the connection
  // previously)
  // The container never takes ownership of the Gadgets put in. Any
  // addChild/removeChild calls must be made accordingly to guarantee life time
  // of Gadgets
  class AuxiliaryConnectionGadgetContainer
  {

  public:

    AuxiliaryConnectionGadget *find( const NodeGadget *srcNode, const NodeGadget *dstNode ) const;
    AuxiliaryConnectionGadget *find( const Gaffer::Plug *dstPlug ) const;
    AuxiliaryConnectionGadget *insert( const NodeGadget *srcNodeGadget, const NodeGadget *dstNodeGadget, const Gaffer::Plug *srcPlug, const Gaffer::Plug *dstPlug );

    // Remove all information about a connection between two plugs. The return
    // value indicates if the connection between the two NodeGadgets as a whole
    // was removed by this operation, as well.
    bool erase( const Gaffer::Plug *dstPlug );

  private:

    typedef std::pair<const NodeGadget*, const NodeGadget*> NodesKey;
    typedef const Gaffer::Plug* PlugKey;

    std::map<NodesKey, AuxiliaryConnectionGadget*> m_nodesMap;
    std::map<PlugKey, NodesKey> m_plugMap;
  };

  mutable AuxiliaryConnectionGadgetContainer m_auxiliaryConnectionGadgets;
  mutable std::set<ConstNodeGadgetPtr> m_nodeGadgetsToUpdate;
};

IE_CORE_DECLAREPTR( AuxiliaryConnectionsGadget );

} // namespace GafferUI

#endif // GAFFERUI_AUXILIARYCONNECTIONGADGET_H
