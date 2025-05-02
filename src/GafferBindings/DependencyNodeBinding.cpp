//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2020, Cinesite VFX Ltd. All rights reserved.
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

#include "GafferBindings/DependencyNodeBinding.h"

using namespace Gaffer;

namespace GafferBindings
{

// This is the `__call__` operator for the metaclass we use for DependencyNodes.
// It is responsible for creating and initialising DependencyNode instances in
// Python, which gives us a chance to inform the DependencyNodeWrapper when
// `__init__` has completed.
PyObject *dependencyNodeMetaclassCall( PyObject *self, PyObject *args, PyObject *kw )
{
	// Delegate the actual work to the default `type.__call__` method.
	// This will call `__new__` and `__init__` and return a new DependencyNode
	// instance.
	PyObject *result = PyType_Type.tp_call( self, args, kw );
	if( result )
	{
		// Inform the DependencyNodeWrapper that __init__ has completed.
		auto n = boost::python::extract<DependencyNode *>( result )();
		if( auto w = dynamic_cast<GafferBindings::DependencyNodeWrapperBase *>( n ) )
		{
			w->m_initialised = true;
		}
	}
	return result;
}

} // namespace GafferBindings

PyTypeObject *GafferBindings::Detail::dependencyNodeMetaclass()
{
	static PyTypeObject g_dependencyNodeMetaclass;
	if( !g_dependencyNodeMetaclass.tp_name )
	{
		// Initialise. We derive from the standard Boost Python metaclass
		// because it has functionality critical to making the Boost bindings
		// work. The only thing we're doing is adding `dependencyNodeMetaclassCall`
		// as the implementation of the `__call__` method.
		Py_SET_TYPE( &g_dependencyNodeMetaclass, &PyType_Type );
		g_dependencyNodeMetaclass.tp_name = "Gaffer.DependencyNodeMetaclass";
		g_dependencyNodeMetaclass.tp_basicsize = PyType_Type.tp_basicsize,
		g_dependencyNodeMetaclass.tp_base = boost::python::objects::class_metatype().get();
		g_dependencyNodeMetaclass.tp_flags = Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE;
		g_dependencyNodeMetaclass.tp_call = dependencyNodeMetaclassCall;
		PyType_Ready( &g_dependencyNodeMetaclass );
	}

	return &g_dependencyNodeMetaclass;
}
