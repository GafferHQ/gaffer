//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2011-2012, John Haddon. All rights reserved.
//  Copyright (c) 2011-2014, Image Engine Design Inc. All rights reserved.
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

#include "AnimationGadgetBinding.h"
#include "ConnectionGadgetBinding.h"
#include "ContainerGadgetBinding.h"
#include "EventBinding.h"
#include "GadgetBinding.h"
#include "GraphGadgetBinding.h"
#include "HandleBinding.h"
#include "ImageGadgetBinding.h"
#include "NameGadgetBinding.h"
#include "NodeGadgetBinding.h"
#include "NoduleBinding.h"
#include "PathColumnBinding.h"
#include "PathListingWidgetBinding.h"
#include "PlugAdderBinding.h"
#include "PlugGadgetBinding.h"
#include "PointerBinding.h"
#include "SpacerGadgetBinding.h"
#include "StyleBinding.h"
#include "TextGadgetBinding.h"
#include "ToolBinding.h"
#include "ViewBinding.h"
#include "ViewportGadgetBinding.h"
#include "WidgetSignalBinding.h"

using namespace GafferUIModule;

BOOST_PYTHON_MODULE( _GafferUI )
{

	bindGadget();
	bindEvent();
	bindContainerGadget();
	bindGraphGadget();
	bindTextGadget();
	bindNameGadget();
	bindNodeGadget();
	bindNodule();
	bindConnectionGadget();
	bindWidgetSignal();
	bindImageGadget();
	bindStyle();
	bindViewportGadget();
	bindView();
	bindPlugGadget();
	bindPointer();
	bindSpacerGadget();
	bindHandle();
	bindTool();
	bindPathListingWidget();
	bindPlugAdder();
	bindAnimationGadget();
	bindPathColumn();

}
