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

#pragma once

namespace GafferSceneUI
{

enum TypeId
{
	SceneViewTypeId = 110651,
	SceneGadgetTypeId = 110652,
	SelectionToolTypeId = 110653,
	CropWindowToolTypeId = 110654,
	ShaderViewTypeId = 110655,
	ShaderNodeGadgetTypeId = 110656,
	TransformToolTypeId = 110657,
	TranslateToolTypeId = 110658,
	ScaleToolTypeId = 110659,
	RotateToolTypeId = 110660,
	CameraToolTypeId = 110661,
	UVViewTypeId = 110662,
	UVSceneTypeId = 110663,
	HistoryPathTypeId = 110664,
	SetPathTypeId = 110665,
	LightToolTypeId = 110666,
	LightPositionToolTypeId = 110667,
	RenderPassPathTypeId = 110668,
	VisualiserToolTypeId = 110669,

	LastTypeId = 110700
};

} // namespace GafferSceneUI
