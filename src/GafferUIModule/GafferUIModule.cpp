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

#include "boost/python.hpp"

#include "GafferUIBindings/GadgetBinding.h"
#include "GafferUIBindings/EventBinding.h"
#include "GafferUIBindings/ModifiableEventBinding.h"
#include "GafferUIBindings/KeyEventBinding.h"
#include "GafferUIBindings/ButtonEventBinding.h"
#include "GafferUIBindings/NodeGadgetBinding.h"
#include "GafferUIBindings/ContainerGadgetBinding.h"
#include "GafferUIBindings/GraphGadgetBinding.h"
#include "GafferUIBindings/RenderableGadgetBinding.h"
#include "GafferUIBindings/IndividualContainerBinding.h"
#include "GafferUIBindings/FrameBinding.h"
#include "GafferUIBindings/TextGadgetBinding.h"
#include "GafferUIBindings/NameGadgetBinding.h"
#include "GafferUIBindings/LinearContainerBinding.h"
#include "GafferUIBindings/NoduleBinding.h"
#include "GafferUIBindings/DragDropEventBinding.h"
#include "GafferUIBindings/ConnectionGadgetBinding.h"
#include "GafferUIBindings/WidgetSignalBinding.h"
#include "GafferUIBindings/StandardNodeGadgetBinding.h"
#include "GafferUIBindings/SplinePlugGadgetBinding.h"
#include "GafferUIBindings/StandardNoduleBinding.h"
#include "GafferUIBindings/CompoundNoduleBinding.h"
#include "GafferUIBindings/ImageGadgetBinding.h"
#include "GafferUIBindings/StyleBinding.h"
#include "GafferUIBindings/StandardStyleBinding.h"
#include "GafferUIBindings/ViewportGadgetBinding.h"
#include "GafferUIBindings/ViewBinding.h"
#include "GafferUIBindings/View3DBinding.h"
#include "GafferUIBindings/PlugGadgetBinding.h"
#include "GafferUIBindings/GraphLayoutBinding.h"
#include "GafferUIBindings/PointerBinding.h"
#include "GafferUIBindings/BackdropNodeGadgetBinding.h"
#include "GafferUIBindings/MetadataBinding.h"
#include "GafferUIBindings/SpacerGadgetBinding.h"

using namespace GafferUIBindings;

BOOST_PYTHON_MODULE( _GafferUI )
{

	bindGadget();
	bindEvent();
	bindModifiableEvent();
	bindKeyEvent();
	bindButtonEvent();
	bindContainerGadget();
	bindGraphGadget();
	bindRenderableGadget();
	bindIndividualContainer();
	bindFrame();
	bindTextGadget();
	bindNameGadget();
	bindNodeGadget();
	bindLinearContainer();
	bindNodule();
	bindDragDropEvent();
	bindConnectionGadget();
	bindWidgetSignal();
	bindStandardNodeGadget();
	bindSplinePlugGadget();
	bindStandardNodule();
	bindCompoundNodule();
	bindImageGadget();
	bindStyle();
	bindStandardStyle();
	bindViewportGadget();
	bindView();
	bindView3D();
	bindPlugGadget();
	bindGraphLayout();
	bindPointer();
	bindBackdropNodeGadget();
	bindMetadata();
	bindSpacerGadget();
	
}
