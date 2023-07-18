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

#pragma once

namespace Gaffer
{

enum TypeId
{

	GraphComponentTypeId = 110000,
	NodeTypeId = 110001,
	PlugTypeId = 110002,
	ValuePlugTypeId = 110003,
	FloatPlugTypeId = 110004,
	IntPlugTypeId = 110005,
	StringPlugTypeId = 110006,
	ScriptNodeTypeId = 110007,
	ApplicationRootTypeId = 110008,
	ScriptContainerTypeId = 110009,
	SetTypeId = 110010,
	ObjectPlugTypeId = 110011,
	NameValuePlugTypeId = 110012,
	V2fPlugTypeId = 110013,
	V3fPlugTypeId = 110014,
	V2iPlugTypeId = 110015,
	V3iPlugTypeId = 110016,
	Color3fPlugTypeId = 110017,
	Color4fPlugTypeId = 110018,
	SplineffPlugTypeId = 110019,
	SplinefColor3fPlugTypeId = 110020,
	M33fPlugTypeId = 110021,
	M44fPlugTypeId = 110022,
	BoolPlugTypeId = 110023,
	AtomicBox2fPlugTypeId = 110024,
	IntVectorDataPlugTypeId = 110025,
	FloatVectorDataPlugTypeId = 110026,
	StringVectorDataPlugTypeId = 110027,
	V3fVectorDataPlugTypeId = 110028,
	StandardSetTypeId = 110029,
	ChildSetTypeId = 110030,
	BoolVectorDataPlugTypeId = 110031,
	AnimationTypeId = 110032,
	AnimationCurvePlugTypeId = 110033,
	PreferencesTypeId = 110034,
	ObjectVectorPlugTypeId = 110035,
	Box2iPlugTypeId = 110036,
	Box3iPlugTypeId = 110037,
	Box2fPlugTypeId = 110038,
	Box3fPlugTypeId = 110039,
	PrimitivePlugTypeId = 110040,
	ExpressionTypeId = 110041,
	ContextProcessorTypeId = 110042,
	TimeWarpTypeId = 110043,
	TransformPlugTypeId = 110044,
	AtomicBox3fPlugTypeId = 110045,
	AtomicBox2iPlugTypeId = 110046,
	CompoundObjectPlugTypeId = 110047,
	CompoundDataPlugTypeId = 110048,
	ContextVariablesTypeId = 110049,
	RandomTypeId = 110050,
	DependencyNodeTypeId = 110051,
	AtomicCompoundDataPlugTypeId = 110052,
	BoxTypeId = 110053,
	InternedStringVectorDataPlugTypeId = 110054,
	SplinefColor4fPlugTypeId = 110055,
	NumericBookmarkSetTypeId = 110056,
	NameSwitchTypeId = 110057,
	Transform2DPlugTypeId = 110058,
	ReferenceTypeId = 110059,
	ComputeNodeTypeId = 110060,
	SpreadsheetTypeId = 110061,
	Color3fVectorDataPlugTypeId = 110062,
	ActionTypeId = 110063,
	SimpleActionTypeId = 110064,
	SetValueActionTypeId = 110065,
	CompoundActionTypeId = 110066,
	CompoundDataMemberPlugTypeId = 110067,
	ArrayPlugTypeId = 110068,
	BackdropTypeId = 110069,
	SwitchTypeId = 110070,
	SpreadsheetCellPlugTypeId = 110071,
	PathMatcherDataPlugTypeId = 110072,
	SubGraphTypeId = 110073,
	DotTypeId = 110074,
	PathTypeId = 110075,
	PathFilterTypeId = 110076,
	CompoundPathFilterTypeId = 110077,
	LeafPathFilterTypeId = 110078,
	MatchPatternPathFilterTypeId = 110079,
	FileSystemPathTypeId = 110080,
	LoopTypeId = 110081,
	FileSequencePathFilterTypeId = 110082,
	M44fVectorDataPlugTypeId = 110083,
	V2iVectorDataPlugTypeId = 110084,
	BoxIOTypeId = 110085,
	BoxInTypeId = 110086,
	BoxOutTypeId = 110087,
	DeleteContextVariablesTypeId = 110088,
	SpreadsheetRowsPlugTypeId = 110089,
	SpreadsheetRowPlugTypeId = 110090,
	ShufflePlugTypeId = 110091,
	ShufflesPlugTypeId = 110092,
	EditScopeTypeId = 110093,
	MessagesDataTypeId = 110094,
	M33fVectorDataPlugTypeId = 110095,
	ScriptNodeFocusSetTypeId = 110096,
	AnimationKeyTypeId = 110097,
	RandomChoiceTypeId = 110098,
	ContextQueryTypeId = 110099,
	TweakPlugTypeId = 110100,
	TweaksPlugTypeId = 110101,
	V2fVectorDataPlugTypeId = 110102,
	V3iVectorDataPlugTypeId = 110103,
	ContextVariableTweaksTypeId = 110104,
	HiddenFilePathFilterTypeId = 110105,
	Color4fVectorDataPlugTypeId = 110106,
	OptionalValuePlugTypeId = 110107,

	LastTypeId = 110159,

};

} // namespace Gaffer
