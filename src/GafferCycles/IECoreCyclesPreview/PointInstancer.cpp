//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2026, Cinesite VFX Ltd. All rights reserved.
//
//  Redistribution and use in source and binary forms, with or without
//  modification, are permitted provided that the following conditions are
//  met:
//
//     * Redistributions of source code must retain the above copyright
//       notice, this list of conditions and the following disclaimer.
//
//     * Redistributions in binary form must reproduce the above copyright
//       notice, this list of conditions and the following disclaimer in the
//       documentation and/or other materials provided with the distribution.
//
//     * Neither the name of Image Engine Design nor the names of any
//       other contributors to this software may be used to endorse or
//       promote products derived from this software without specific prior
//       written permission.
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

#include "PointInstancer.h"

#include "GafferCycles/IECoreCyclesPreview/SocketAlgo.h"

#include "IECore/DataAlgo.h"
#include "IECore/TypeTraits.h"

using namespace std;
using namespace IECoreCycles;

namespace
{

// Based on `RendererAlgo::SampledTransform::concatenate()`.
void concatenate(
	IECoreScenePreview::Renderer::Samples<ccl::Transform> &samples,
	const IECoreScenePreview::Renderer::Samples<ccl::Transform> &childSamples
)
{
	if( childSamples.empty() )
	{
		return;
	}

	if( samples.empty() )
	{
		samples = childSamples;
		return;
	}

	if( childSamples.size() == 1 )
	{
		for( auto &sample : samples )
		{
			sample = sample * childSamples[0];
		}
	}
	else if( samples.size() == 1 )
	{
		const ccl::Transform parentSample = samples[0];
		samples = childSamples;
		for( auto &sample : samples )
		{
			sample = parentSample * sample;
		}
	}
	else
	{
		IECoreScenePreview::Renderer::Samples<ccl::DecomposedTransform> decomposedSamples;
		decomposedSamples.resize( samples.size() );
		ccl::transform_motion_decompose( decomposedSamples.data(), samples.data(), samples.size() );

		IECoreScenePreview::Renderer::Samples<ccl::Transform> updatedSamples;
		updatedSamples.reserve( childSamples.size() );

		for( size_t i = 0; i < childSamples.size(); ++i )
		{
			ccl::Transform transformAtTime;
			const float sampleTime = (float)i / (float)(childSamples.size() - 1);
			ccl::transform_motion_array_interpolate( &transformAtTime, decomposedSamples.data(), decomposedSamples.size(), sampleTime );
			updatedSamples.push_back( transformAtTime * childSamples[i] );
		}

		samples = updatedSamples;
	}
}

struct ParamValueCreator
{

	ccl::ParamValue operator()( ccl::ustring name, int value ) const
	{
		return ccl::ParamValue( name, value );
	}

	ccl::ParamValue operator()( ccl::ustring name, float value ) const
	{
		return ccl::ParamValue( name, value );
	}

	ccl::ParamValue operator()( ccl::ustring name, const Imath::V3f &value ) const
	{
		const ccl::float4 f4 = ccl::make_float4( value[0], value[1], value[2], 1.0f );
		return ccl::ParamValue( name, ccl::TypeFloat4, 1, &f4 );
	}

	ccl::ParamValue operator()( ccl::ustring name, const Imath::Color3f &value ) const
	{
		return (*this)( name, Imath::Color4f( value[0], value[1], value[2], 1.0f ) );
	}

	ccl::ParamValue operator()( ccl::ustring name, const Imath::Color4f &value ) const
	{
		const ccl::float4 f4 = ccl::make_float4( value[0], value[1], value[2], value[3] );
		return ccl::ParamValue( name, ccl::TypeRGBA, 1, &f4 );
	}

};

using InstanceAttributeFunction = std::function<void ( size_t pointIndex, ccl::vector<ccl::ParamValue> &attributes )>;

vector<InstanceAttributeFunction> createInstanceAttributeFunctions( const IECoreScene::PointInstancer *instancer )
{
	vector<InstanceAttributeFunction> result;

	for( const auto &[name, primitiveVariable] : instancer->instanceAttributes() )
	{
		IECore::dispatch(

			primitiveVariable.data.get(),

			/// \todo Drop explicit capture of structured bindings
			/// when we're on C++20.
			[&, &name=name, &primitiveVariable=primitiveVariable]( auto typedData ) -> void {

				using DataType = remove_const_t<remove_pointer_t<decltype( typedData )>>;
				if constexpr( IECore::TypeTraits::IsVectorTypedData<DataType>::value )
				{
					using ElementType = typename DataType::ValueType::value_type;
					if constexpr( std::is_invocable_v<ParamValueCreator, ccl::ustring &, ElementType> )
					{
						IECoreScene::PrimitiveVariable::IndexedView<ElementType> indexedView( primitiveVariable );
						ccl::ustring uName( name.c_str() );
						InstanceAttributeFunction f = [uName, indexedView] ( size_t pointIndex, ccl::vector<ccl::ParamValue> &attributes ) {
							attributes.push_back( ParamValueCreator()( uName, indexedView[pointIndex] ) );
						};
						result.push_back( f );
					}
				}

			}

		);
	}

	return result;
}

} // namespace

PointInstancer::PointInstancer(
	ccl::Scene *scene,
	NodeDeleter *nodeDeleter,
	const IECoreScenePreview::Renderer::PointInstancerSamples &samples,
	const std::vector<SharedGeometryPtr> &prototypes
)
	:	m_scene( scene ), m_nodeDeleter( nodeDeleter ), m_prototypes( prototypes )
{
	auto prototypeIndices = samples[0]->getPrototypeIndex();
	IECoreScene::PointInstancer::VisibilityQuery visibilityQuery( *samples[0] );

	vector<IECoreScene::PointInstancer::TransformQuery> transformQueries;
	for( const auto &sample : samples )
	{
		transformQueries.push_back( IECoreScene::PointInstancer::TransformQuery( *sample ) );
	}

	vector<InstanceAttributeFunction> attributeFunctions = createInstanceAttributeFunctions( samples[0].get() );

	// Hold lock throughought rather than constantly take and release
	// for each instance.
	std::scoped_lock sceneLock( m_scene->mutex );

	m_instances.reserve( prototypeIndices.size() );
	for( size_t instanceIndex = 0; instanceIndex < prototypeIndices.size(); ++instanceIndex )
	{
		const size_t prototypeIndex = prototypeIndices[instanceIndex];
		if(
			!m_prototypes[prototypeIndex] ||
			!visibilityQuery.visible( instanceIndex )
		)
		{
			continue;
		}

		IECoreScenePreview::Renderer::Samples<ccl::Transform> transformSamples;
		transformSamples.reserve( transformQueries.size() );
		for( const auto &query : transformQueries )
		{
			transformSamples.push_back( SocketAlgo::setTransform( query.transform( instanceIndex ) ) );
		}

		UniqueObjectPtr object( m_scene->create_node<ccl::Object>(), NodeDeleter::ObjectDeleter( nodeDeleter ) );
		// Makes non-thread-safe refcount increment on geometry, which
		// is protected by `sceneLock`.
		object->set_geometry( const_cast<ccl::Geometry *>( m_prototypes[prototypeIndex].get() ) );
		object->tag_update( m_scene );

		if( !attributeFunctions.empty() )
		{
			object->attributes.reserve( attributeFunctions.size() );
			for( const auto &f : attributeFunctions )
			{
				f( instanceIndex, object->attributes );
			}
		}

		m_instances.push_back( { std::move( object ), transformSamples } );
	}
}

void PointInstancer::link( const IECore::InternedString &type, const IECoreScenePreview::Renderer::ConstObjectSetPtr &objects )
{
}

void PointInstancer::transform( const IECoreScenePreview::Renderer::TransformSamples &samples, const IECoreScenePreview::Renderer::SampleTimes &times )
{
	IECoreScenePreview::Renderer::Samples<ccl::Transform> parentSamples;
	parentSamples.reserve( samples.size() );
	for( auto &sample : samples )
	{
		parentSamples.push_back( SocketAlgo::setTransform( sample ) );
	}

	std::scoped_lock sceneLock( m_scene->mutex );

	IECoreScenePreview::Renderer::Samples<ccl::Transform> instanceSamples;
	ccl::array<ccl::Transform> motion;
	for( const auto &instance : m_instances )
	{
		instanceSamples = parentSamples;
		concatenate( instanceSamples, instance.transformSamples );
		const size_t primarySampleIndex = (instanceSamples.size() - 1) / 2;
		instance.object->set_tfm( instanceSamples[primarySampleIndex ] );

		if( instanceSamples.size() > 1 )
		{
			motion.resize( instanceSamples.size() );
			std::copy( instanceSamples.begin(), instanceSamples.end(), motion.begin() );
			instance.object->set_motion( motion );
		}

		instance.object->tag_update( m_scene );
	}
}

bool PointInstancer::attributes( const IECoreScenePreview::Renderer::AttributesInterface *attributes )
{
	return true;
}

void PointInstancer::assignID( uint32_t id )
{
	for( auto &instance : m_instances )
	{
		instance.object->set_pass_id( id );
	}
}

void PointInstancer::assignInstanceID( uint32_t id )
{
	// Instance IDs not needed in Cycles, because encapsulated instancers aren't supported.
}
