//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2012, John Haddon. All rights reserved.
//  Copyright (c) 2013, Image Engine Design Inc. All rights reserved.
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

namespace GafferScene
{

enum TypeId
{
	ScenePlugTypeId = 120000,
	SceneNodeTypeId = 120001,
	FilterProcessorTypeId = 120002,
	SetFilterTypeId = 120003,
	SceneProcessorTypeId = 120004,
	SceneElementProcessorTypeId = 120005,
	PointsTypeTypeId = 120006,
	PrimitiveVariableProcessorTypeId = 120007,
	DeletePrimitiveVariablesTypeId = 120008,
	GroupTypeId = 120009,
	ShaderPlugTypeId = 120010,
	UDIMQueryTypeId = 120011,
	WireframeTypeId = 120012,
	ObjectSourceTypeId = 120013,
	PlaneTypeId = 120014,
	ScatterTypeId = 120015,
	InstancerTypeId = 120016,
	BranchCreatorTypeId = 120017,
	ObjectToSceneTypeId = 120018,
	CameraTypeId = 120019,
	GlobalsProcessorTypeId = 120020,
	OutputsTypeId = 120021,
	OptionsTypeId = 120022,
	ShaderTypeId = 120023,
	ShaderAssignmentTypeId = 120024,
	FilterTypeId = 120025,
	PathFilterTypeId = 120026,
	AttributesTypeId = 120027,
	GlobalShaderTypeId = 120028,
	ClippingPlaneTypeId = 120029,
	RenameTypeId = 120030,
	StandardOptionsTypeId = 120031,
	SubTreeTypeId = 120032,
	OpenGLAttributesTypeId = 120033,
	SceneWriterTypeId = 120034,
	SceneReaderTypeId = 120035,
	ReverseWindingTypeId = 120036,
	LightTypeId = 120037,
	StandardAttributesTypeId = 120038,
	OpenGLShaderTypeId = 120039,
	TransformTypeId = 120040,
	ConstraintTypeId = 120041,
	AimConstraintTypeId = 120042,
	MeshTypeTypeId = 120043,
	FilteredSceneProcessorTypeId = 120044,
	PruneTypeId = 120045,
	FreezeTransformTypeId = 120046,
	MeshDistortionTypeId = 120047,
	PrimitiveVariableTweaksTypeId = 120048,
	InteractiveRenderTypeId = 120049,
	CubeTypeId = 120050,
	SphereTypeId = 120051,
	TextTypeId = 120052,
	MapProjectionTypeId = 120053,
	PointConstraintTypeId = 120054,
	CustomAttributesTypeId = 120055,
	CustomOptionsTypeId = 120056,
	MapOffsetTypeId = 120057,
	IsolateTypeId = 120058,
	AttributeProcessorTypeId = 120059,
	DeleteAttributesTypeId = 120060,
	UnionFilterTypeId = 120061,
	SetVisualiserTypeId = 120062,
	LightFilterTypeId = 120063,
	ParentConstraintTypeId = 120064,
	ParentTypeId = 120065,
	PrimitiveVariablesTypeId = 120066,
	DuplicateTypeId = 120067,
	GridTypeId = 120068,
	SetTypeId = 120069,
	CoordinateSystemTypeId = 120070,
	DeleteGlobalsTypeId = 120071,
	DeleteOptionsTypeId = 120072,
	DeleteOutputsTypeId = 120073,
	ExternalProceduralTypeId = 120074,
	ScenePathTypeId = 120075,
	MeshToPointsTypeId = 120076,
	OrientationTypeId = 120077,
	DeleteSetsTypeId = 120078,
	ParametersTypeId = 120079,
	SceneFilterPathFilterTypeId = 120080,
	DeleteObjectTypeId = 120081,
	AttributeVisualiserTypeId = 120082,
	CopyPrimitiveVariablesTypeId = 120083,
	RenderTypeId = 120084,
	FilterPlugTypeId = 120085,
	ShaderTweaksTypeId = 120086,
	ImageToPointsTypeId = 120087,
	CopyOptionsTypeId = 120088,
	LightToCameraTypeId = 120089,
	FilterResultsTypeId = 120090,
	ObjectProcessorTypeId = 120091,
	MeshTangentsTypeId = 120092,
	ResamplePrimitiveVariablesTypeId = 120093,
	DeleteFacesTypeId = 120094,
	DeleteCurvesTypeId = 120095,
	DeletePointsTypeId = 120096,
	DeformerTypeId = 120097,
	CollectScenesTypeId = 120098,
	CapsuleTypeId = 120099,
	EncapsulateTypeId = 120100,
	CopyAttributesTypeId = 120101,
	CollectPrimitiveVariablesTypeId = 120102,
	PrimitiveVariableExistsTypeId = 120103,
	CollectTransformsTypeId = 120104,
	CameraTweaksTypeId = 120105,
	MergeScenesTypeId = 120106,
	ShuffleAttributesTypeId = 120107,
	ShufflePrimitiveVariablesTypeId = 120108,
	LocaliseAttributesTypeId = 120109,
	PrimitiveSamplerTypeId = 120110,
	ClosestPointSamplerTypeId = 120111,
	CurveSamplerTypeId = 120112,
	UnencapsulateTypeId = 120113,
	MotionPathTypeId = 120114,
	InstancerContextVariablePlugTypeId = 120115,
	FilterQueryTypeId = 120116,
	TransformQueryTypeId = 120117,
	BoundQueryTypeId = 120118,
	ExistenceQueryTypeId = 120119,
	AttributeQueryTypeId = 120120,
	UVSamplerTypeId = 120121,
	CryptomatteTypeId = 120122,
	ShaderQueryTypeId = 120123,
	AttributeTweaksTypeId = 120124,
	OptionTweaksTypeId = 120125,
	OptionQueryTypeId = 120126,
	PrimitiveVariableQueryTypeId = 120127,
	SetQueryTypeId = 120128,
	MeshSegmentsTypeId = 120129,
	VisibleSetDataTypeId = 120130,
	MeshSplitTypeId = 120131,
	FramingConstraintTypeId = 120132,
	MeshNormalsTypeId = 120133,
	ImageScatterTypeId = 120134,
	InstancerCapsuleTypeId = 120135,
	RenderPassesTypeId = 120136,
	DeleteRenderPassesTypeId = 120137,
	MeshTessellateTypeId = 120138,
	RenderPassShaderTypeId = 120139,
	ShaderTweakProxyTypeId = 120140,
	MergeObjectsTypeId = 120141,
	MergeMeshesTypeId = 120142,
	MergePointsTypeId = 120143,
	MergeCurvesTypeId = 120144,
	ShuffleRenderPassesTypeId = 120145,
	ShuffleOptionsTypeId = 120146,
	CatalogueTypeId = 120147,
	CatalogueImageTypeId = 120148,
	DisplayTypeId = 120149,
	GafferDisplayDriverTypeId = 120150,
	CameraQueryTypeId = 120151,

	LastTypeId = 120999
};

} // namespace GafferScene
