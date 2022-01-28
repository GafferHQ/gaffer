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

#ifndef GAFFERSCENE_TYPEIDS_H
#define GAFFERSCENE_TYPEIDS_H

namespace GafferScene
{

enum TypeId
{
	ScenePlugTypeId = 110501,
	SceneNodeTypeId = 110502,
	FilterProcessorTypeId = 110503,
	SetFilterTypeId = 110504,
	SceneProcessorTypeId = 110505,
	SceneElementProcessorTypeId = 110506,
	PointsTypeTypeId = 110507,
	PrimitiveVariableProcessorTypeId = 110508,
	DeletePrimitiveVariablesTypeId = 110509,
	GroupTypeId = 110510,
	ShaderPlugTypeId = 110511,
	UDIMQueryTypeId = 110512,
	WireframeTypeId = 110513,
	ObjectSourceTypeId = 110514,
	PlaneTypeId = 110515,
	SeedsTypeId = 110516,
	InstancerTypeId = 110517,
	BranchCreatorTypeId = 110518,
	ObjectToSceneTypeId = 110519,
	CameraTypeId = 110520,
	GlobalsProcessorTypeId = 110521,
	OutputsTypeId = 110522,
	OptionsTypeId = 110523,
	ShaderTypeId = 110524,
	ShaderAssignmentTypeId = 110525,
	FilterTypeId = 110526,
	PathFilterTypeId = 110527,
	AttributesTypeId = 110528,
	GlobalShaderTypeId = 110529,
	ClippingPlaneTypeId = 110530,
	TweaksPlugTypeId = 110531,
	StandardOptionsTypeId = 110532,
	SubTreeTypeId = 110533,
	OpenGLAttributesTypeId = 110534,
	SceneWriterTypeId = 110535,
	SceneReaderTypeId = 110536,
	ReverseWindingTypeId = 110537,
	LightTypeId = 110538,
	StandardAttributesTypeId = 110539,
	OpenGLShaderTypeId = 110540,
	TransformTypeId = 110541,
	ConstraintTypeId = 110542,
	AimConstraintTypeId = 110543,
	MeshTypeTypeId = 110544,
	FilteredSceneProcessorTypeId = 110545,
	PruneTypeId = 110546,
	FreezeTransformTypeId = 110547,
	MeshDistortionTypeId = 110548,
	OpenGLRenderTypeId = 110549,
	InteractiveRenderTypeId = 110550,
	CubeTypeId = 110551,
	SphereTypeId = 110552,
	TextTypeId = 110553,
	MapProjectionTypeId = 110554,
	PointConstraintTypeId = 110555,
	CustomAttributesTypeId = 110556,
	CustomOptionsTypeId = 110557,
	MapOffsetTypeId = 110558,
	IsolateTypeId = 110559,
	AttributeProcessorTypeId = 110560,
	DeleteAttributesTypeId = 110561,
	UnionFilterTypeId = 110562,
	SetVisualiserTypeId = 110563,
	LightFilterTypeId = 110564,
	ParentConstraintTypeId = 110565,
	ParentTypeId = 110566,
	PrimitiveVariablesTypeId = 110567,
	DuplicateTypeId = 110568,
	GridTypeId = 110569,
	SetTypeId = 110570,
	CoordinateSystemTypeId = 110571,
	DeleteGlobalsTypeId = 110572,
	DeleteOptionsTypeId = 110573,
	DeleteOutputsTypeId = 110574,
	ExternalProceduralTypeId = 110575,
	ScenePathTypeId = 110576,
	MeshToPointsTypeId = 110577,
	OrientationTypeId = 110578,
	DeleteSetsTypeId = 110579,
	ParametersTypeId = 110580,
	SceneFilterPathFilterTypeId = 110581,
	DeleteObjectTypeId = 110582,
	AttributeVisualiserTypeId = 110583,
	CopyPrimitiveVariablesTypeId = 110584,
	RenderTypeId = 110585,
	FilterPlugTypeId = 110586,
	ShaderTweaksTypeId = 110587,
	TweakPlugTypeId = 110588,
	CopyOptionsTypeId = 110589,
	LightToCameraTypeId = 110590,
	FilterResultsTypeId = 110591,
	ObjectProcessorTypeId = 110592,
	MeshTangentsTypeId = 110593,
	ResamplePrimitiveVariablesTypeId = 110594,
	DeleteFacesTypeId = 110595,
	DeleteCurvesTypeId = 110596,
	DeletePointsTypeId = 110597,
	DeformerTypeId = 110598,
	CollectScenesTypeId = 110599,
	CapsuleTypeId = 110600,
	EncapsulateTypeId = 110601,
	CopyAttributesTypeId = 110602,
	CollectPrimitiveVariablesTypeId = 110603,
	PrimitiveVariableExistsTypeId = 110604,
	CollectTransformsTypeId = 110605,
	CameraTweaksTypeId = 110606,
	MergeScenesTypeId = 110607,
	ShuffleAttributesTypeId = 110608,
	ShufflePrimitiveVariablesTypeId = 110609,
	LocaliseAttributesTypeId = 110610,
	PrimitiveSamplerTypeId = 110611,
	ClosestPointSamplerTypeId = 110612,
	CurveSamplerTypeId = 110613,
	UnencapsulateTypeId = 110614,
	MotionPathTypeId = 110615,
	InstancerContextVariablePlugTypeId = 110616,
	FilterQueryTypeId = 110617,
	TransformQueryTypeId = 110618,
	BoundQueryTypeId = 110619,
	ExistenceQueryTypeId = 110620,
	AttributeQueryTypeId = 110621,
	UVSamplerTypeId = 110622,
	CryptomatteTypeId = 110623,

	PreviewGeometryTypeId = 110648,
	PreviewProceduralTypeId = 110649,

	LastTypeId = 110650
};

} // namespace GafferScene

#endif // GAFFERSCENE_TYPEIDS_H
