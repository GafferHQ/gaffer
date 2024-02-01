//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2017, John Haddon. All rights reserved.
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

#pragma once

#include "IECoreDelight/Export.h"

#include "IECoreScene/PrimitiveVariable.h"

#include "IECore/CompoundData.h"
#include "IECore/VectorTypedData.h"

#include <vector>

#include <nsi.h>

namespace IECoreDelight
{

/// Aids in the creation of parameter lists to be passed to the
/// NSI API. The ParameterList does not copy any of the data passed
/// to it; it is the caller's responsibility to keep all data alive
/// for as long as the ParameterList is used.
class IECOREDELIGHT_API ParameterList
{

	public :

		ParameterList();
		ParameterList( std::initializer_list<NSIParam_t> parameters );
		explicit ParameterList( const IECore::CompoundDataMap &values );

		~ParameterList();

		void add( const NSIParam_t &parameter );
		void add( const char *name, const std::string &value );
		// Prevent calls to `add()` with a temporary string, since that
		// would cause a dangling pointer to be passed to 3Delight.
		void add( const char *name, const std::string &&value ) = delete;
		/// \deprecated Use the version below.
		void add( const char *name, const IECore::Data *value );
		void add( const char *name, const IECore::Data *value, bool isSingleArray );
		void add( const char *name, const IECore::Data *value, const IECore::IntVectorData *indices );

		/// \deprecated Use the version below.
		NSIParam_t parameter( const char *name, const IECore::Data *value );
		NSIParam_t parameter( const char *name, const IECore::Data *value, bool isSingleArray );
		const char *allocate( const std::string &s );

		int size() const;
		const NSIParam_t *data() const;

	private :

		template<typename T>
		T *allocate();

		std::vector<NSIParam_t> m_params;
		std::vector<const void *> m_allocations;

};

} // namespace IECoreDelight
