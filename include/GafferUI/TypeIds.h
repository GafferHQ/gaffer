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

#ifndef GAFFERUI_TYPEIDS_H
#define GAFFERUI_TYPEIDS_H

namespace GafferUI
{

enum TypeId
{
	GadgetTypeId = 110251,
	NodeGadgetTypeId = 110252,
	GraphGadgetTypeId = 110253,
	ContainerGadgetTypeId = 110254,
	AuxiliaryConnectionsGadgetTypeId = 110255,
	TextGadgetTypeId = 110256,
	NameGadgetTypeId = 110257,
	IndividualContainerTypeId = 110258,
	FrameTypeId = 110259,
	StyleTypeId = 110260,
	StandardStyleTypeId = 110261,
	NoduleTypeId = 110262,
	LinearContainerTypeId = 110263,
	ConnectionGadgetTypeId = 110264,
	StandardNodeGadgetTypeId = 110265,
	AuxiliaryNodeGadgetTypeId = 110266,
	StandardNoduleTypeId = 110267,
	CompoundNoduleTypeId = 110268,
	ImageGadgetTypeId = 110269,
	ViewportGadgetTypeId = 110270,
	ViewTypeId = 110271,
	ConnectionCreatorTypeId = 110272,
	CompoundNumericNoduleTypeId = 110273,
	PlugGadgetTypeId = 110274,
	GraphLayoutTypeId = 110275,
	StandardGraphLayoutTypeId = 110276,
	BackdropNodeGadgetTypeId = 110277,
	SpacerGadgetTypeId = 110278,
	StandardConnectionGadgetTypeId = 110279,
	HandleTypeId = 110280,
	ToolTypeId = 110281,
	DotNodeGadgetTypeId = 110282,
	PlugAdderTypeId = 110283,
	NoduleLayoutTypeId = 110284,
	TranslateHandleTypeId = 110285,
	ScaleHandleTypeId = 110286,
	RotateHandleTypeId = 110287,
	AnimationGadgetTypeId = 110288,
	AnnotationsGadgetTypeId = 110289,
	GraphGadgetSetPositionsActionTypeId = 110290,

	LastTypeId = 110450
};

} // namespace GafferUI

#endif // GAFFERUI_TYPEIDS_H
