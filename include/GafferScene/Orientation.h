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

#pragma once

#include "GafferScene/ObjectProcessor.h"

namespace Gaffer
{

class StringPlug;

} // namespace Gaffer

namespace GafferScene
{

class GAFFERSCENE_API Orientation : public ObjectProcessor
{

	public :

		Orientation( const std::string &name=defaultName<Orientation>() );
		~Orientation() override;

		GAFFER_NODE_DECLARE_TYPE( GafferScene::Orientation, OrientationTypeId, ObjectProcessor );

		enum class Mode
		{
			Euler,
			Quaternion,
			AxisAngle,
			Aim,
			Matrix,
			// Used to fix incorrect Alembic export from Houdini
			// (SideFX bug #92479).
			QuaternionXYZW,
		};

		/// Input
		/// =====

		Gaffer::IntPlug *inModePlug();
		const Gaffer::IntPlug *inModePlug() const;

		Gaffer::BoolPlug *deleteInputsPlug();
		const Gaffer::BoolPlug *deleteInputsPlug() const;

		// Euler
		// -----

		Gaffer::StringPlug *inEulerPlug();
		const Gaffer::StringPlug *inEulerPlug() const;

		Gaffer::IntPlug *inOrderPlug(); /// Values are Imath::Euler::Order
		const Gaffer::IntPlug *inOrderPlug() const;

		// Quaternion
		// ----------

		Gaffer::StringPlug *inQuaternionPlug();
		const Gaffer::StringPlug *inQuaternionPlug() const;

		// Axis Angle
		// ----------

		Gaffer::StringPlug *inAxisPlug();
		const Gaffer::StringPlug *inAxisPlug() const;

		Gaffer::StringPlug *inAnglePlug();
		const Gaffer::StringPlug *inAnglePlug() const;

		// Basis vectors
		// -------------

		Gaffer::StringPlug *inXAxisPlug();
		const Gaffer::StringPlug *inXAxisPlug() const;

		Gaffer::StringPlug *inYAxisPlug();
		const Gaffer::StringPlug *inYAxisPlug() const;

		Gaffer::StringPlug *inZAxisPlug();
		const Gaffer::StringPlug *inZAxisPlug() const;

		// Matrix
		// ------

		Gaffer::StringPlug *inMatrixPlug();
		const Gaffer::StringPlug *inMatrixPlug() const;

		/// Randomisation
		/// =============

		Gaffer::BoolPlug *randomEnabledPlug();
		const Gaffer::BoolPlug *randomEnabledPlug() const;

		Gaffer::V3fPlug *randomAxisPlug();
		const Gaffer::V3fPlug *randomAxisPlug() const;

		Gaffer::FloatPlug *randomSpreadPlug();
		const Gaffer::FloatPlug *randomSpreadPlug() const;

		Gaffer::FloatPlug *randomTwistPlug();
		const Gaffer::FloatPlug *randomTwistPlug() const;

		enum class Space
		{
			Local,
			Parent
		};

		Gaffer::IntPlug *randomSpacePlug();
		const Gaffer::IntPlug *randomSpacePlug() const;

		/// Output
		/// ======

		Gaffer::IntPlug *outModePlug();
		const Gaffer::IntPlug *outModePlug() const;

		// Euler
		// -----

		Gaffer::StringPlug *outEulerPlug();
		const Gaffer::StringPlug *outEulerPlug() const;

		Gaffer::IntPlug *outOrderPlug(); /// Values are Imath::Euler::Order
		const Gaffer::IntPlug *outOrderPlug() const;

		// Quaternion
		// ----------

		Gaffer::StringPlug *outQuaternionPlug();
		const Gaffer::StringPlug *outQuaternionPlug() const;

		// Axis Angle
		// ----------

		Gaffer::StringPlug *outAxisPlug();
		const Gaffer::StringPlug *outAxisPlug() const;

		Gaffer::StringPlug *outAnglePlug();
		const Gaffer::StringPlug *outAnglePlug() const;

		// Basis vectors
		// -------------

		Gaffer::StringPlug *outXAxisPlug();
		const Gaffer::StringPlug *outXAxisPlug() const;

		Gaffer::StringPlug *outYAxisPlug();
		const Gaffer::StringPlug *outYAxisPlug() const;

		Gaffer::StringPlug *outZAxisPlug();
		const Gaffer::StringPlug *outZAxisPlug() const;

		// Matrix
		// ------

		Gaffer::StringPlug *outMatrixPlug();
		const Gaffer::StringPlug *outMatrixPlug() const;

	protected :

		bool affectsProcessedObject( const Gaffer::Plug *input ) const override;
		void hashProcessedObject( const ScenePath &path, const Gaffer::Context *context, IECore::MurmurHash &h ) const override;
		IECore::ConstObjectPtr computeProcessedObject( const ScenePath &path, const Gaffer::Context *context, const IECore::Object *inputObject ) const override;

	private :

		static size_t g_firstPlugIndex;

};

IE_CORE_DECLAREPTR( Orientation )

} // namespace GafferScene
