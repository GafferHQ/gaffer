//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2011-2013, Image Engine Design Inc. All rights reserved.
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

#ifndef GAFFERUI_COMPOUNDNODULE_H
#define GAFFERUI_COMPOUNDNODULE_H

#include "GafferUI/Nodule.h"
#include "GafferUI/LinearContainer.h"

namespace Gaffer
{

IE_CORE_FORWARDDECLARE( CompoundPlug )

} // namespace Gaffer

namespace GafferUI
{

IE_CORE_FORWARDDECLARE( LinearContainer );

/// A Nodule subclass to represent the child plugs of a CompoundPlug. This
/// is not registered automatically with the Nodule factory on the assumption
/// that generally individual connections within a CompoundPlug do not need
/// to be displayed to the user. Use Nodule::registerNodule( nodeType, plugPath, creator )
/// to cause the use of the CompoundNodule for specific plugs.
class CompoundNodule : public Nodule
{

	public :

		/// The default value for direction causes increasing direction when oriented in X and decreasing when
		/// oriented in Y, it may be overridden by explicitly specifying a direction.
		CompoundNodule( Gaffer::CompoundPlugPtr plug, LinearContainer::Orientation orientation=LinearContainer::X,
			float spacing = 0.0f, LinearContainer::Direction direction=LinearContainer::InvalidDirection );
		virtual ~CompoundNodule();

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( GafferUI::CompoundNodule, CompoundNoduleTypeId, Nodule );

		virtual Imath::Box3f bound() const;

		virtual bool acceptsChild( const Gaffer::GraphComponent *potentialChild ) const;

		/// Returns a Nodule for a child of the CompoundPlug being represented.
		Nodule *nodule( const Gaffer::Plug *plug );
		const Nodule *nodule( const Gaffer::Plug *plug ) const;
		
	protected :

		void doRender( const Style *style ) const;
	
	private :
	
		void childAdded( Gaffer::GraphComponent *parent, Gaffer::GraphComponent *child );
		void childRemoved( Gaffer::GraphComponent *parent, Gaffer::GraphComponent *child );
		void childRenderRequest( Gadget *child );

		typedef std::map<const Gaffer::Plug *, Nodule *> NoduleMap;
		NoduleMap m_nodules;
		
		LinearContainerPtr m_row;
				
};

IE_CORE_DECLAREPTR( CompoundNodule );

} // namespace GafferUI

#endif // GAFFERUI_COMPOUNDNODULE_H
