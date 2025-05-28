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
	SceneViewTypeId = 121000,
	SceneGadgetTypeId = 121001,
	SelectionToolTypeId = 121002,
	CropWindowToolTypeId = 121003,
	ShaderViewTypeId = 121004,
	ShaderNodeGadgetTypeId = 121005,
	TransformToolTypeId = 121006,
	TranslateToolTypeId = 121007,
	ScaleToolTypeId = 121008,
	RotateToolTypeId = 121009,
	CameraToolTypeId = 121010,
	UVViewTypeId = 121011,
	UVSceneTypeId = 121012,
	HistoryPathTypeId = 121013,
	SetPathTypeId = 121014,
	LightToolTypeId = 121015,
	LightPositionToolTypeId = 121016,
	RenderPassPathTypeId = 121017,
	VisualiserToolTypeId = 121018,

	LastTypeId = 121199
};

} // namespace GafferSceneUI
