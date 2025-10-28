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

	GraphComponentTypeId = 118000,
	NodeTypeId = 118001,
	PlugTypeId = 118002,
	ValuePlugTypeId = 118003,
	FloatPlugTypeId = 118004,
	IntPlugTypeId = 118005,
	StringPlugTypeId = 118006,
	ScriptNodeTypeId = 118007,
	ApplicationRootTypeId = 118008,
	ScriptContainerTypeId = 118009,
	SetTypeId = 118010,
	ObjectPlugTypeId = 118011,
	NameValuePlugTypeId = 118012,
	V2fPlugTypeId = 118013,
	V3fPlugTypeId = 118014,
	V2iPlugTypeId = 118015,
	V3iPlugTypeId = 118016,
	Color3fPlugTypeId = 118017,
	Color4fPlugTypeId = 118018,
	RampffPlugTypeId = 118019,
	RampfColor3fPlugTypeId = 118020,
	M33fPlugTypeId = 118021,
	M44fPlugTypeId = 118022,
	BoolPlugTypeId = 118023,
	AtomicBox2fPlugTypeId = 118024,
	IntVectorDataPlugTypeId = 118025,
	FloatVectorDataPlugTypeId = 118026,
	StringVectorDataPlugTypeId = 118027,
	V3fVectorDataPlugTypeId = 118028,
	StandardSetTypeId = 118029,
	ChildSetTypeId = 118030,
	BoolVectorDataPlugTypeId = 118031,
	AnimationTypeId = 118032,
	AnimationCurvePlugTypeId = 118033,
	PreferencesTypeId = 118034,
	ObjectVectorPlugTypeId = 118035,
	Box2iPlugTypeId = 118036,
	Box3iPlugTypeId = 118037,
	Box2fPlugTypeId = 118038,
	Box3fPlugTypeId = 118039,
	PrimitivePlugTypeId = 118040,
	ExpressionTypeId = 118041,
	ContextProcessorTypeId = 118042,
	TimeWarpTypeId = 118043,
	TransformPlugTypeId = 118044,
	AtomicBox3fPlugTypeId = 118045,
	AtomicBox2iPlugTypeId = 118046,
	CompoundObjectPlugTypeId = 118047,
	CompoundDataPlugTypeId = 118048,
	ContextVariablesTypeId = 118049,
	RandomTypeId = 118050,
	DependencyNodeTypeId = 118051,
	AtomicCompoundDataPlugTypeId = 118052,
	BoxTypeId = 118053,
	InternedStringVectorDataPlugTypeId = 118054,
	RampfColor4fPlugTypeId = 118055,
	NumericBookmarkSetTypeId = 118056,
	NameSwitchTypeId = 118057,
	Transform2DPlugTypeId = 118058,
	ReferenceTypeId = 118059,
	ComputeNodeTypeId = 118060,
	SpreadsheetTypeId = 118061,
	Color3fVectorDataPlugTypeId = 118062,
	ActionTypeId = 118063,
	SimpleActionTypeId = 118064,
	SetValueActionTypeId = 118065,
	CompoundActionTypeId = 118066,
	CompoundDataMemberPlugTypeId = 118067,
	ArrayPlugTypeId = 118068,
	BackdropTypeId = 118069,
	SwitchTypeId = 118070,
	SpreadsheetCellPlugTypeId = 118071,
	PathMatcherDataPlugTypeId = 118072,
	SubGraphTypeId = 118073,
	DotTypeId = 118074,
	PathTypeId = 118075,
	PathFilterTypeId = 118076,
	CompoundPathFilterTypeId = 118077,
	LeafPathFilterTypeId = 118078,
	MatchPatternPathFilterTypeId = 118079,
	FileSystemPathTypeId = 118080,
	LoopTypeId = 118081,
	FileSequencePathFilterTypeId = 118082,
	M44fVectorDataPlugTypeId = 118083,
	V2iVectorDataPlugTypeId = 118084,
	BoxIOTypeId = 118085,
	BoxInTypeId = 118086,
	BoxOutTypeId = 118087,
	DeleteContextVariablesTypeId = 118088,
	SpreadsheetRowsPlugTypeId = 118089,
	SpreadsheetRowPlugTypeId = 118090,
	ShufflePlugTypeId = 118091,
	ShufflesPlugTypeId = 118092,
	EditScopeTypeId = 118093,
	MessagesDataTypeId = 118094,
	M33fVectorDataPlugTypeId = 118095,
	ScriptNodeFocusSetTypeId = 118096,
	AnimationKeyTypeId = 118097,
	RandomChoiceTypeId = 118098,
	ContextQueryTypeId = 118099,
	TweakPlugTypeId = 118100,
	TweaksPlugTypeId = 118101,
	V2fVectorDataPlugTypeId = 118102,
	V3iVectorDataPlugTypeId = 118103,
	ContextVariableTweaksTypeId = 118104,
	HiddenFilePathFilterTypeId = 118105,
	Color4fVectorDataPlugTypeId = 118106,
	OptionalValuePlugTypeId = 118107,
	CollectTypeId = 118108,
	Box2fVectorDataPlugTypeId = 118109,
	PatternMatchTypeId = 118110,
	Int64VectorDataPlugTypeId = 118111,

	LastTypeId = 118799

};

} // namespace Gaffer
