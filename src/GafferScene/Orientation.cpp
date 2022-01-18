//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2019, Image Engine Design Inc. All rights reserved.
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

/// Disable over-zealous GCC warning.
/// See https://stackoverflow.com/questions/21755206/how-to-get-around-gcc-void-b-4-may-be-used-uninitialized-in-this-funct
#if defined( __GNUC__ ) && !defined( __clang__ )
#pragma GCC diagnostic ignored "-Wmaybe-uninitialized"
#endif

#include "GafferScene/Orientation.h"

#include "Gaffer/StringPlug.h"

#include "IECoreScene/Primitive.h"

#include "IECore/AngleConversion.h"
#include "IECore/MatrixAlgo.h"

#include "OpenEXR/ImathEuler.h"
#include "OpenEXR/ImathMatrixAlgo.h"
#include "OpenEXR/ImathRandom.h"

#include <random>

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace IECoreScene;
using namespace Gaffer;
using namespace GafferScene;

//////////////////////////////////////////////////////////////////////////
// Internal utilities
//
// We deliberately separate the actual conversion operations out from
// `computeProcessedObject()` so that the latter has a simple structure
// that matches `hashProcessedObject()` closesly. This makes it easier
// to verify correctness, and harder to introduce bugs. Perhaps the
// conversion functions might make sense as IECoreScene Algo at some
// point.
//////////////////////////////////////////////////////////////////////////

namespace
{

struct ViewSpec
{
	std::string name;
	PrimitiveVariable::Interpolation interpolation = PrimitiveVariable::Invalid;
	size_t size = 0;
};

template<typename T>
PrimitiveVariable::IndexedView<T> indexedView( const Primitive *inputPrimitive, Primitive *outputPrimitive, const std::string &name, bool deleteInputs, ViewSpec &spec )
{
	const auto it = inputPrimitive->variables.find( name );
	if( it == inputPrimitive->variables.end() )
	{
		throw IECore::Exception(
			boost::str( boost::format( "Primitive variable \"%s\" not found" ) % name )
		);
	}

	using DataType = IECore::TypedData<vector<T>>;
	const DataType *data = runTimeCast<const DataType>( it->second.data.get() );
	if( !data )
	{
		throw IECore::Exception(
			boost::str(
				boost::format( "Primitive variable \"%s\" has wrong type \"%s\" (wanted \"%s\")" )
					% name
					% it->second.data->typeName()
					% DataType::staticTypeName()
			)
		);
	}

	if( spec.name == "" )
	{
		// First variable found.
		spec.name = name;
		spec.interpolation = it->second.interpolation;
		spec.size = data->readable().size();
	}
	else
	{
		// Check that we match any previously found variables.
		if( data->readable().size() != spec.size )
		{
			throw IECore::Exception(
				boost::str(
					boost::format( "Primitive variable \"%s\" has wrong size (%d, but should be %d to match \"%s\")" )
						% name
						% data->readable().size()
						% spec.size
						% spec.name
				)
			);
		}
	}

	if( deleteInputs )
	{
		// Although the returned IndexedView doesn't maintain any ownership
		// of the data, it's OK to erase here because we get the IndexedView
		// from `inputPrimitive`, and we only erase from `outputPrimitive`.
		outputPrimitive->variables.erase( name );
	}

	return PrimitiveVariable::IndexedView<T>( it->second );
}

PrimitiveVariable inEuler( const Primitive *inputPrimitive, Primitive *outputPrimitive, const std::string &eulerName, const Imath::Eulerf::Order order, bool deleteInputs )
{
	if( eulerName == "" )
	{
		return PrimitiveVariable();
	}

	ViewSpec spec;
	auto view = indexedView<V3f>( inputPrimitive, outputPrimitive, eulerName, deleteInputs, spec );

	QuatfVectorDataPtr quaternionData = new QuatfVectorData;
	auto &quaternions = quaternionData->writable();
	quaternions.reserve( view.size() );

	for( auto &eulerVec : view )
	{
		const Eulerf euler( degreesToRadians( eulerVec ), order, Eulerf::XYZLayout );
		quaternions.push_back( euler.toQuat() );
	}

	return PrimitiveVariable( spec.interpolation, quaternionData );
}

PrimitiveVariable inQuaternion( const Primitive *inputPrimitive, Primitive *outputPrimitive, const std::string &quaternionName, bool deleteInputs, bool xyzw )
{
	if( quaternionName == "" )
	{
		return PrimitiveVariable();
	}

	ViewSpec spec;
	auto view = indexedView<Quatf>( inputPrimitive, outputPrimitive, quaternionName, deleteInputs, spec );

	QuatfVectorDataPtr quaternionData = new QuatfVectorData;
	auto &quaternions = quaternionData->writable();
	quaternions.reserve( view.size() );

	for( auto &q : view )
	{
		if( xyzw )
		{
			quaternions.push_back( Quatf( q.v.z, V3f( q.r, q.v.x, q.v.y ) ) );
		}
		else
		{
			quaternions.push_back( q );
		}
	}

	return PrimitiveVariable( spec.interpolation, quaternionData );
}

PrimitiveVariable inAxisAngle( const Primitive *inputPrimitive, Primitive *outputPrimitive, const std::string &axisName, const std::string &angleName, bool deleteInputs )
{
	if( axisName == "" || angleName == "" )
	{
		return PrimitiveVariable();
	}

	ViewSpec spec;
	auto axisView = indexedView<V3f>( inputPrimitive, outputPrimitive, axisName, deleteInputs, spec );
	auto angleView = indexedView<float>( inputPrimitive, outputPrimitive, angleName, deleteInputs, spec );

	QuatfVectorDataPtr quaternionData = new QuatfVectorData;
	auto &quaternions = quaternionData->writable();
	quaternions.reserve( axisView.size() );

	for( size_t i = 0, s = axisView.size(); i < s; ++i )
	{
		quaternions.push_back( Quatf().setAxisAngle( axisView[i], angleView[i] ) );
	}

	return PrimitiveVariable( spec.interpolation, quaternionData );
}

PrimitiveVariable inAim( const Primitive *inputPrimitive, Primitive *outputPrimitive, const std::string &xAxisName, const std::string &yAxisName, const std::string &zAxisName, bool deleteInputs )
{
	ViewSpec spec;

	using OptionalVector = std::optional<PrimitiveVariable::IndexedView<V3f>>;
	OptionalVector xAxis, yAxis, zAxis;

	if( xAxisName != "" )
	{
		xAxis = indexedView<V3f>( inputPrimitive, outputPrimitive, xAxisName, deleteInputs, spec );
	}
	if( yAxisName != "" )
	{
		yAxis = indexedView<V3f>( inputPrimitive, outputPrimitive, yAxisName, deleteInputs, spec );
	}
	if( zAxisName != "" )
	{
		zAxis = indexedView<V3f>( inputPrimitive, outputPrimitive, zAxisName, deleteInputs, spec );
	}

	if( !xAxis && !yAxis && !zAxis )
	{
		return PrimitiveVariable();
	}

	QuatfVectorDataPtr quaternionData = new QuatfVectorData;
	auto &quaternions = quaternionData->writable();
	quaternions.reserve( spec.size );

	for( size_t i = 0; i < spec.size; ++i )
	{
		M44f m;
		if( xAxis && yAxis && zAxis )
		{
			m = matrixFromBasis( (*xAxis)[i], (*yAxis)[i], (*zAxis)[i], V3f( 0 ) );
		}
		else if( xAxis && yAxis )
		{
			const V3f &x = (*xAxis)[i];
			const V3f &y = (*yAxis)[i];
			m = matrixFromBasis( x, y, x.cross( y ), V3f( 0 ) );
		}
		else if( xAxis && zAxis )
		{
			const V3f &x = (*xAxis)[i];
			const V3f &z = (*zAxis)[i];
			m = matrixFromBasis( x, z.cross( x ), z, V3f( 0 ) );
		}
		else if( yAxis && zAxis )
		{
			const V3f &y = (*yAxis)[i];
			const V3f &z = (*zAxis)[i];
			m = matrixFromBasis( y.cross( z ), y, z, V3f( 0 ) );
		}
		else if( xAxis )
		{
			m = rotationMatrixWithUpDir( V3f( 1, 0, 0 ), (*xAxis)[i], V3f( 0, 1, 0 ) );
		}
		else if( yAxis )
		{
			m = rotationMatrixWithUpDir( V3f( 0, 1, 0 ), (*yAxis)[i], V3f( 0, 1, 0 ) );
		}
		else if( zAxis )
		{
			m = rotationMatrixWithUpDir( V3f( 0, 0, 1 ), (*zAxis)[i], V3f( 0, 1, 0 ) );
		}

		removeScalingAndShear( m );
		quaternions.push_back( extractQuat( m ) );
	}

	return PrimitiveVariable( spec.interpolation, quaternionData );
}

PrimitiveVariable inMatrix( const Primitive *inputPrimitive, Primitive *outputPrimitive, const std::string &matrixName, bool deleteInputs )
{
	ViewSpec spec;
	auto matrixView = indexedView<M33f>( inputPrimitive, outputPrimitive, matrixName, deleteInputs, spec );

	QuatfVectorDataPtr quaternionData = new QuatfVectorData;
	auto &quaternions = quaternionData->writable();
	quaternions.reserve( matrixView.size() );

	for( auto &m : matrixView )
	{
		quaternions.push_back( extractQuat( M44f( m, V3f( 0 ) ) ) );
	}

	return PrimitiveVariable( spec.interpolation, quaternionData );
}

void outEuler( const PrimitiveVariable &orientations, Primitive *outputPrimitive, const std::string &eulerName, Imath::Eulerf::Order order )
{
	if( eulerName == "" )
	{
		return;
	}

	const auto &quaternions = static_cast<const QuatfVectorData *>( orientations.data.get() )->readable();

	V3fVectorDataPtr eulerData = new V3fVectorData();
	auto &euler = eulerData->writable();
	euler.reserve( quaternions.size() );

	for( auto &q : quaternions )
	{
		Eulerf e( q.toMatrix33(), order );
		euler.push_back( radiansToDegrees( e.toXYZVector() ) );
	}

	outputPrimitive->variables[eulerName] = PrimitiveVariable( orientations.interpolation, eulerData );
}

void outQuaternion( const PrimitiveVariable &orientations, Primitive *outputPrimitive, const std::string &quaternionName )
{
	if( quaternionName == "" )
	{
		return;
	}
	outputPrimitive->variables[quaternionName] = orientations;
}

void outAxisAngle( const PrimitiveVariable &orientations, Primitive *outputPrimitive, const std::string &axisName, const std::string &angleName )
{
	const auto &quaternions = static_cast<const QuatfVectorData *>( orientations.data.get() )->readable();

	V3fVectorDataPtr axisData;
	vector<V3f> *axis = nullptr;
	if( axisName != "" )
	{
		axisData = new V3fVectorData();
		axis = &axisData->writable();
		axis->reserve( quaternions.size() );
		outputPrimitive->variables[axisName] = PrimitiveVariable( orientations.interpolation, axisData );
	}

	FloatVectorDataPtr angleData;
	vector<float> *angle = nullptr;
	if( angleName != "" )
	{
		angleData = new FloatVectorData();
		angle = &angleData->writable();
		angle->reserve( quaternions.size() );
		outputPrimitive->variables[angleName] = PrimitiveVariable( orientations.interpolation, angleData );
	}

	if( !axis && !angle )
	{
		return;
	}

	for( auto &q : quaternions )
	{
		if( axis )
		{
			axis->push_back( q.axis() );
		}
		if( angle )
		{
			angle->push_back( q.angle() );
		}
	}
}

void outAim( const PrimitiveVariable &orientations, Primitive *outputPrimitive, const std::string &xAxisName, const std::string &yAxisName, const std::string &zAxisName )
{
	const auto &quaternions = static_cast<const QuatfVectorData *>( orientations.data.get() )->readable();

	V3fVectorDataPtr xAxisData;
	vector<V3f> *xAxis = nullptr;
	if( xAxisName != "" )
	{
		xAxisData = new V3fVectorData;
		xAxis = &xAxisData->writable();
		xAxis->reserve( quaternions.size() );
		outputPrimitive->variables[xAxisName] = PrimitiveVariable( orientations.interpolation, xAxisData );
	}

	V3fVectorDataPtr yAxisData;
	vector<V3f> *yAxis = nullptr;
	if( yAxisName != "" )
	{
		yAxisData = new V3fVectorData;
		yAxis = &yAxisData->writable();
		yAxis->reserve( quaternions.size() );
		outputPrimitive->variables[yAxisName] = PrimitiveVariable( orientations.interpolation, yAxisData );
	}

	V3fVectorDataPtr zAxisData;
	vector<V3f> *zAxis = nullptr;
	if( zAxisName != "" )
	{
		zAxisData = new V3fVectorData;
		zAxis = &zAxisData->writable();
		zAxis->reserve( quaternions.size() );
		outputPrimitive->variables[zAxisName] = PrimitiveVariable( orientations.interpolation, zAxisData );
	}

	if( !xAxis && !yAxis && !zAxis )
	{
		return;
	}

	for( auto &q : quaternions )
	{
		const M44f m = q.toMatrix44();
		if( xAxis )
		{
			xAxis->push_back( V3f( m[0][0], m[0][1], m[0][2] ) );
		}
		if( yAxis )
		{
			yAxis->push_back( V3f( m[1][0], m[1][1], m[1][2] ) );
		}
		if( zAxis )
		{
			zAxis->push_back( V3f( m[2][0], m[2][1], m[2][2] ) );
		}
	}
}

void outMatrix( const PrimitiveVariable &orientations, Primitive *outputPrimitive, const std::string &matrixName )
{
	if( matrixName == "" )
	{
		return;
	}

	const auto &quaternions = static_cast<const QuatfVectorData *>( orientations.data.get() )->readable();

	M33fVectorDataPtr matricesData = new M33fVectorData();
	auto &matrices = matricesData->writable();
	matrices.reserve( matrices.size() );

	for( auto &q : quaternions )
	{
		matrices.push_back( q.toMatrix33() );
	}

	outputPrimitive->variables[matrixName] = PrimitiveVariable( orientations.interpolation, matricesData );
}

void randomise( vector<Quatf> &orientations, const V3f &axis, float spreadMax, float twistMax, Orientation::Space space )
{
	spreadMax = degreesToRadians( spreadMax );
	twistMax = degreesToRadians( twistMax );

	// For simplicity, we randomise relative to a fixed Y axis,
	// and map `axis` to and from that on either side.
	Quatf yToAxis; yToAxis.setRotation( V3f( 0, 1, 0 ), axis );
	const Quatf axisToY = yToAxis.inverse();

	// We randomise in cosine space to get an equal-area distribution rather than
	// an equal-angle one that would clump at the pole.
	const float cosSpread = cos( spreadMax );

	Rand32 random;
	for( auto &q : orientations )
	{
		// Generate a random axis that is perpendicular to our
		// central Y axis. Generate spread by rotating a random
		// amount about this axis.
		const float r = random.nextf( -M_PI, M_PI );
		const V3f spreadAxis( cos( r ), 0, sin( r ) );
		const float s = acos( random.nextf( cosSpread, 1 ) );
		Quatf spread; spread.setAxisAngle( spreadAxis, s );
		// Generate twist.
		Quatf twist; twist.setAxisAngle( V3f( 0, 1, 0 ), random.nextf( -twistMax, twistMax ) );
		// Compose with original orientation.
		if( space == Orientation::Space::Local )
		{
			q = q * yToAxis * spread * twist * axisToY;
		}
		else
		{
			q = yToAxis * spread * twist * axisToY * q;
		}
	}
}

} // namespace

//////////////////////////////////////////////////////////////////////////
// Orientation
//////////////////////////////////////////////////////////////////////////

GAFFER_NODE_DEFINE_TYPE( Orientation );

size_t Orientation::g_firstPlugIndex = 0;

Orientation::Orientation( const std::string &name )
	:	ObjectProcessor( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );

	// Input

	addChild( new IntPlug( "inMode", Plug::In, (int)Mode::Euler, (int)Mode::Euler, (int)Mode::QuaternionXYZW ) );
	addChild( new BoolPlug( "deleteInputs", Plug::In, true ) );

	addChild( new StringPlug( "inEuler", Plug::In, "" ) );
	addChild( new IntPlug( "inOrder", Plug::In, Eulerf::XYZ ) );

	addChild( new StringPlug( "inQuaternion", Plug::In, "orientation" ) );

	addChild( new StringPlug( "inAxis", Plug::In, "axis" ) );
	addChild( new StringPlug( "inAngle", Plug::In, "angle" ) );

	addChild( new StringPlug( "inXAxis" ) );
	addChild( new StringPlug( "inYAxis" ) );
	addChild( new StringPlug( "inZAxis" ) );

	addChild( new StringPlug( "inMatrix" ) );

	// Randomisation

	addChild( new BoolPlug( "randomEnabled", Plug::In, false ) );
	addChild( new V3fPlug( "randomAxis", Plug::In, V3f( 0, 1, 0 ) ) );
	addChild( new FloatPlug( "randomSpread", Plug::In, 0, 0, 180 ) );
	addChild( new FloatPlug( "randomTwist", Plug::In, 0, 0, 180 ) );
	addChild( new IntPlug( "randomSpace", Plug::In, (int)Space::Local, (int)Space::Local, (int)Space::Parent ) );

	// Output

	addChild( new IntPlug( "outMode", Plug::In, (int)Mode::Quaternion, (int)Mode::Euler, (int)Mode::Matrix ) );

	addChild( new StringPlug( "outEuler", Plug::In, "" ) );
	addChild( new IntPlug( "outOrder", Plug::In, Eulerf::XYZ ) );

	addChild( new StringPlug( "outQuaternion", Plug::In, "orientation" ) );

	addChild( new StringPlug( "outAxis", Plug::In, "" ) );
	addChild( new StringPlug( "outAngle", Plug::In, "" ) );

	addChild( new StringPlug( "outXAxis" ) );
	addChild( new StringPlug( "outYAxis" ) );
	addChild( new StringPlug( "outZAxis" ) );

	addChild( new StringPlug( "outMatrix" ) );
}

Orientation::~Orientation()
{
}

Gaffer::IntPlug *Orientation::inModePlug()
{
	return getChild<Gaffer::IntPlug>( g_firstPlugIndex );
}

const Gaffer::IntPlug *Orientation::inModePlug() const
{
	return getChild<Gaffer::IntPlug>( g_firstPlugIndex );
}

Gaffer::BoolPlug *Orientation::deleteInputsPlug()
{
	return getChild<Gaffer::BoolPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::BoolPlug *Orientation::deleteInputsPlug() const
{
	return getChild<Gaffer::BoolPlug>( g_firstPlugIndex + 1 );
}

Gaffer::StringPlug *Orientation::inEulerPlug()
{
	return getChild<Gaffer::StringPlug>( g_firstPlugIndex + 2 );
}

const Gaffer::StringPlug *Orientation::inEulerPlug() const
{
	return getChild<Gaffer::StringPlug>( g_firstPlugIndex + 2 );
}

Gaffer::IntPlug *Orientation::inOrderPlug()
{
	return getChild<Gaffer::IntPlug>( g_firstPlugIndex + 3 );
}

const Gaffer::IntPlug *Orientation::inOrderPlug() const
{
	return getChild<Gaffer::IntPlug>( g_firstPlugIndex + 3 );
}

Gaffer::StringPlug *Orientation::inQuaternionPlug()
{
	return getChild<Gaffer::StringPlug>( g_firstPlugIndex + 4 );
}

const Gaffer::StringPlug *Orientation::inQuaternionPlug() const
{
	return getChild<Gaffer::StringPlug>( g_firstPlugIndex + 4 );
}

Gaffer::StringPlug *Orientation::inAxisPlug()
{
	return getChild<Gaffer::StringPlug>( g_firstPlugIndex + 5 );
}

const Gaffer::StringPlug *Orientation::inAxisPlug() const
{
	return getChild<Gaffer::StringPlug>( g_firstPlugIndex + 5 );
}

Gaffer::StringPlug *Orientation::inAnglePlug()
{
	return getChild<Gaffer::StringPlug>( g_firstPlugIndex + 6 );
}

const Gaffer::StringPlug *Orientation::inAnglePlug() const
{
	return getChild<Gaffer::StringPlug>( g_firstPlugIndex + 6 );
}

Gaffer::StringPlug *Orientation::inXAxisPlug()
{
	return getChild<Gaffer::StringPlug>( g_firstPlugIndex + 7 );
}

const Gaffer::StringPlug *Orientation::inXAxisPlug() const
{
	return getChild<Gaffer::StringPlug>( g_firstPlugIndex + 7 );
}

Gaffer::StringPlug *Orientation::inYAxisPlug()
{
	return getChild<Gaffer::StringPlug>( g_firstPlugIndex + 8 );
}

const Gaffer::StringPlug *Orientation::inYAxisPlug() const
{
	return getChild<Gaffer::StringPlug>( g_firstPlugIndex + 8 );
}

Gaffer::StringPlug *Orientation::inZAxisPlug()
{
	return getChild<Gaffer::StringPlug>( g_firstPlugIndex + 9 );
}

const Gaffer::StringPlug *Orientation::inZAxisPlug() const
{
	return getChild<Gaffer::StringPlug>( g_firstPlugIndex + 9 );
}

Gaffer::StringPlug *Orientation::inMatrixPlug()
{
	return getChild<Gaffer::StringPlug>( g_firstPlugIndex + 10 );
}

const Gaffer::StringPlug *Orientation::inMatrixPlug() const
{
	return getChild<Gaffer::StringPlug>( g_firstPlugIndex + 10 );
}

Gaffer::BoolPlug *Orientation::randomEnabledPlug()
{
	return getChild<BoolPlug>( g_firstPlugIndex + 11 );
}

const Gaffer::BoolPlug *Orientation::randomEnabledPlug() const
{
	return getChild<BoolPlug>( g_firstPlugIndex + 11 );
}

Gaffer::V3fPlug *Orientation::randomAxisPlug()
{
	return getChild<V3fPlug>( g_firstPlugIndex + 12 );
}

const Gaffer::V3fPlug *Orientation::randomAxisPlug() const
{
	return getChild<V3fPlug>( g_firstPlugIndex + 12 );
}

Gaffer::FloatPlug *Orientation::randomSpreadPlug()
{
	return getChild<FloatPlug>( g_firstPlugIndex + 13 );
}

const Gaffer::FloatPlug *Orientation::randomSpreadPlug() const
{
	return getChild<FloatPlug>( g_firstPlugIndex + 13 );
}

Gaffer::FloatPlug *Orientation::randomTwistPlug()
{
	return getChild<FloatPlug>( g_firstPlugIndex + 14 );
}

const Gaffer::FloatPlug *Orientation::randomTwistPlug() const
{
	return getChild<FloatPlug>( g_firstPlugIndex + 14 );
}

Gaffer::IntPlug *Orientation::randomSpacePlug()
{
	return getChild<IntPlug>( g_firstPlugIndex + 15 );
}

const Gaffer::IntPlug *Orientation::randomSpacePlug() const
{
	return getChild<IntPlug>( g_firstPlugIndex + 15 );
}

Gaffer::IntPlug *Orientation::outModePlug()
{
	return getChild<Gaffer::IntPlug>( g_firstPlugIndex + 16 );
}

const Gaffer::IntPlug *Orientation::outModePlug() const
{
	return getChild<Gaffer::IntPlug>( g_firstPlugIndex + 16 );
}

Gaffer::StringPlug *Orientation::outEulerPlug()
{
	return getChild<Gaffer::StringPlug>( g_firstPlugIndex + 17 );
}

const Gaffer::StringPlug *Orientation::outEulerPlug() const
{
	return getChild<Gaffer::StringPlug>( g_firstPlugIndex + 17 );
}

Gaffer::IntPlug *Orientation::outOrderPlug()
{
	return getChild<Gaffer::IntPlug>( g_firstPlugIndex + 18 );
}

const Gaffer::IntPlug *Orientation::outOrderPlug() const
{
	return getChild<Gaffer::IntPlug>( g_firstPlugIndex + 18 );
}

Gaffer::StringPlug *Orientation::outQuaternionPlug()
{
	return getChild<Gaffer::StringPlug>( g_firstPlugIndex + 19 );
}

const Gaffer::StringPlug *Orientation::outQuaternionPlug() const
{
	return getChild<Gaffer::StringPlug>( g_firstPlugIndex + 19 );
}

Gaffer::StringPlug *Orientation::outAxisPlug()
{
	return getChild<Gaffer::StringPlug>( g_firstPlugIndex + 20 );
}

const Gaffer::StringPlug *Orientation::outAxisPlug() const
{
	return getChild<Gaffer::StringPlug>( g_firstPlugIndex + 20 );
}

Gaffer::StringPlug *Orientation::outAnglePlug()
{
	return getChild<Gaffer::StringPlug>( g_firstPlugIndex + 21 );
}

const Gaffer::StringPlug *Orientation::outAnglePlug() const
{
	return getChild<Gaffer::StringPlug>( g_firstPlugIndex + 21 );
}

Gaffer::StringPlug *Orientation::outXAxisPlug()
{
	return getChild<Gaffer::StringPlug>( g_firstPlugIndex + 22 );
}

const Gaffer::StringPlug *Orientation::outXAxisPlug() const
{
	return getChild<Gaffer::StringPlug>( g_firstPlugIndex + 22 );
}

Gaffer::StringPlug *Orientation::outYAxisPlug()
{
	return getChild<Gaffer::StringPlug>( g_firstPlugIndex + 23 );
}

const Gaffer::StringPlug *Orientation::outYAxisPlug() const
{
	return getChild<Gaffer::StringPlug>( g_firstPlugIndex + 23 );
}

Gaffer::StringPlug *Orientation::outZAxisPlug()
{
	return getChild<Gaffer::StringPlug>( g_firstPlugIndex + 24 );
}

const Gaffer::StringPlug *Orientation::outZAxisPlug() const
{
	return getChild<Gaffer::StringPlug>( g_firstPlugIndex + 24 );
}

Gaffer::StringPlug *Orientation::outMatrixPlug()
{
	return getChild<Gaffer::StringPlug>( g_firstPlugIndex + 25 );
}

const Gaffer::StringPlug *Orientation::outMatrixPlug() const
{
	return getChild<Gaffer::StringPlug>( g_firstPlugIndex + 25 );
}

bool Orientation::affectsProcessedObject( const Gaffer::Plug *input ) const
{
	return
		ObjectProcessor::affectsProcessedObject( input ) ||
		input == inModePlug() ||
		input == deleteInputsPlug() ||
		input == inEulerPlug() ||
		input == inOrderPlug() ||
		input == inQuaternionPlug() ||
		input == inAxisPlug() ||
		input == inAnglePlug() ||
		input == inXAxisPlug() ||
		input == inYAxisPlug() ||
		input == inZAxisPlug() ||
		input == inMatrixPlug() ||
		input == randomEnabledPlug() ||
		input->parent() == randomAxisPlug() ||
		input == randomSpreadPlug() ||
		input == randomTwistPlug() ||
		input == randomSpacePlug() ||
		input == outModePlug() ||
		input == outEulerPlug() ||
		input == outOrderPlug() ||
		input == outQuaternionPlug() ||
		input == outAxisPlug() ||
		input == outAnglePlug() ||
		input == outXAxisPlug() ||
		input == outYAxisPlug() ||
		input == outZAxisPlug() ||
		input == outMatrixPlug()
	;
}

void Orientation::hashProcessedObject( const ScenePath &path, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ObjectProcessor::hashProcessedObject( path, context, h );

	deleteInputsPlug()->hash( h );

	const int inMode = inModePlug()->getValue();
	h.append( inMode );

	switch( (Mode)inMode )
	{
		case Mode::Euler :
			inEulerPlug()->hash( h );
			inOrderPlug()->hash( h );
			break;
		case Mode::Quaternion :
		case Mode::QuaternionXYZW :
			inQuaternionPlug()->hash( h );
			break;
		case Mode::AxisAngle :
			inAxisPlug()->hash( h );
			inAnglePlug()->hash( h );
			break;
		case Mode::Aim :
			inXAxisPlug()->hash( h );
			inYAxisPlug()->hash( h );
			inZAxisPlug()->hash( h );
			break;
		case Mode::Matrix :
			inMatrixPlug()->hash( h );
			break;
	}

	randomEnabledPlug()->hash( h );
	randomAxisPlug()->hash( h );
	randomSpreadPlug()->hash( h );
	randomTwistPlug()->hash( h );
	randomSpacePlug()->hash( h );

	const int outMode = outModePlug()->getValue();
	h.append( outMode );

	switch( (Mode)outMode )
	{
		case Mode::Euler :
			outEulerPlug()->hash( h );
			outOrderPlug()->hash( h );
			break;
		case Mode::Quaternion :
			outQuaternionPlug()->hash( h );
			break;
		case Mode::AxisAngle :
			outAxisPlug()->hash( h );
			outAnglePlug()->hash( h );
			break;
		case Mode::Aim :
			outXAxisPlug()->hash( h );
			outYAxisPlug()->hash( h );
			outZAxisPlug()->hash( h );
			break;
		case Mode::Matrix :
			outMatrixPlug()->hash( h );
			break;
		case Mode::QuaternionXYZW :
			// Plug max value should prevent us getting here
			assert( 0 );
			break;
	}
}

IECore::ConstObjectPtr Orientation::computeProcessedObject( const ScenePath &path, const Gaffer::Context *context, const IECore::Object *inputObject ) const
{
	const Primitive *inputPrimitive = runTimeCast<const Primitive>( inputObject );
	if( !inputPrimitive )
	{
		return inputObject;
	}

	PrimitivePtr result = inputPrimitive->copy();
	const bool deleteInputs = deleteInputsPlug()->getValue();

	// Convert from input format into intermediate (quaternion) format.

	PrimitiveVariable inOrientation;
	const Mode inMode = (Mode)inModePlug()->getValue();
	switch( inMode )
	{
		case Mode::Euler :
			inOrientation = inEuler(
				inputPrimitive,
				result.get(),
				inEulerPlug()->getValue(),
				(Imath::Eulerf::Order)inOrderPlug()->getValue(),
				deleteInputs
			);
			break;
		case Mode::Quaternion :
		case Mode::QuaternionXYZW :
			inOrientation = inQuaternion(
				inputPrimitive,
				result.get(),
				inQuaternionPlug()->getValue(),
				deleteInputs,
				inMode == Mode::QuaternionXYZW
			);
			break;
		case Mode::AxisAngle :
			inOrientation = inAxisAngle(
				inputPrimitive,
				result.get(),
				inAxisPlug()->getValue(),
				inAnglePlug()->getValue(),
				deleteInputs
			);
			break;
		case Mode::Aim :
			inOrientation = inAim(
				inputPrimitive,
				result.get(),
				inXAxisPlug()->getValue(),
				inYAxisPlug()->getValue(),
				inZAxisPlug()->getValue(),
				deleteInputs
			);
			break;
		case Mode::Matrix :
			inOrientation = inMatrix(
				inputPrimitive,
				result.get(),
				inMatrixPlug()->getValue(),
				deleteInputs
			);
			break;
	}

	// Apply randomisation

	if( randomEnabledPlug()->getValue() )
	{
		if( !inOrientation.data )
		{
			QuatfVectorDataPtr d = new QuatfVectorData();
			d->writable().resize( result->variableSize( PrimitiveVariable::Vertex ) );
			inOrientation.data = d;
			inOrientation.interpolation = PrimitiveVariable::Vertex;
		}
		randomise(
			static_cast<QuatfVectorData *>( inOrientation.data.get() )->writable(),
			randomAxisPlug()->getValue(),
			randomSpreadPlug()->getValue(),
			randomTwistPlug()->getValue(),
			(Space)randomSpacePlug()->getValue()
		);
	}

	// Convert from intermediate format into output format.

	if( !inOrientation.data )
	{
		// One or more required input primitive variables not specified,
		// and randomisation is off.
		return result;
	}

	switch( (Mode)outModePlug()->getValue() )
	{
		case Mode::Euler :
			outEuler(
				inOrientation,
				result.get(),
				outEulerPlug()->getValue(),
				(Imath::Eulerf::Order)outOrderPlug()->getValue()
			);
			break;
		case Mode::Quaternion :
			outQuaternion(
				inOrientation,
				result.get(),
				outQuaternionPlug()->getValue()
			);
			break;
		case Mode::AxisAngle :
			outAxisAngle(
				inOrientation,
				result.get(),
				outAxisPlug()->getValue(),
				outAnglePlug()->getValue()
			);
			break;
		case Mode::Aim :
			outAim(
				inOrientation,
				result.get(),
				outXAxisPlug()->getValue(),
				outYAxisPlug()->getValue(),
				outZAxisPlug()->getValue()
			);
			break;
		case Mode::Matrix :
			outMatrix(
				inOrientation,
				result.get(),
				outMatrixPlug()->getValue()
			);
			break;
		case Mode::QuaternionXYZW :
			// Plug max value should prevent us getting here
			assert( 0 );
	}

	return result;
}
