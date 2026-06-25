//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2026, Cinesite VFX Ltd. All rights reserved.
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

#include "GafferUIBindings/NodeGadgetBinding.h"

namespace
{

// This is the `__call__` operator for the metaclass we use for NodeGadgets.
// It is responsible for creating and initialising NodeGadget instances in
// Python, which allows us to emit `instanceCreatedSignal()` only when the Python
// `__init__` call has completed fully.
PyObject *nodeGadgetMetaclassCall( PyObject *self, PyObject *args, PyObject *kw )
{
	// Delegate the actual work to the default `type.__call__` method.
	// This will call `__new__` and `__init__` and return a new NodeGadget
	// instance.
	PyObject *result = PyType_Type.tp_call( self, args, kw );
	if( result )
	{
		// Emit the `instanceCreatedSignal()`, now that the Python instance
		// has fully constructed.
		auto n = boost::python::extract<GafferUI::NodeGadget *>( result )();
		GafferUI::NodeGadget::instanceCreatedSignal()( n );
	}
	return result;
}

} // namespace

/// \todo We're doing something similar for the DependencyNode binding. Consider
/// consolidating everything into the binding for RefCounted, perhaps by calling
/// a new `RefCounted::postConstructor()` virtual method.
PyTypeObject *GafferUIBindings::Detail::nodeGadgetMetaclass()
{
	static PyTypeObject g_nodeGadgetMetaclass;
	if( !g_nodeGadgetMetaclass.tp_name )
	{
		// Initialise. We derive from the standard Boost Python metaclass
		// because it has functionality critical to making the Boost bindings
		// work. The only thing we're doing is adding `nodeGadgetMetaclassCall`
		// as the implementation of the `__call__` method.
		Py_SET_TYPE( &g_nodeGadgetMetaclass, &PyType_Type );
		g_nodeGadgetMetaclass.tp_name = "GafferUI.NodeGadgetMetaclass";
		g_nodeGadgetMetaclass.tp_basicsize = PyType_Type.tp_basicsize,
		g_nodeGadgetMetaclass.tp_base = boost::python::objects::class_metatype().get();
		g_nodeGadgetMetaclass.tp_flags = Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE;
		g_nodeGadgetMetaclass.tp_call = nodeGadgetMetaclassCall;
		PyType_Ready( &g_nodeGadgetMetaclass );
	}

	return &g_nodeGadgetMetaclass;
}
