##########################################################################
#
#  Copyright (c) 2019, John Haddon. All rights reserved.
#
#  Redistribution and use in source and binary forms, with or without
#  modification, are permitted provided that the following conditions are
#  met:
#
#      * Redistributions of source code must retain the above
#        copyright notice, this list of conditions and the following
#        disclaimer.
#
#      * Redistributions in binary form must reproduce the above
#        copyright notice, this list of conditions and the following
#        disclaimer in the documentation and/or other materials provided with
#        the distribution.
#
#      * Neither the name of John Haddon nor the names of
#        any other contributors to this software may be used to endorse or
#        promote products derived from this software without specific prior
#        written permission.
#
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS
#  IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
#  THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
#  PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR
#  CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
#  EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
#  PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
#  PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
#  LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
#  NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
#  SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
##########################################################################

import unittest

import Gaffer
import GafferTest

class MonitorAlgoTest( GafferTest.TestCase ) :

	def testAnnotate( self ) :

		s = Gaffer.ScriptNode()
		s["b"] = Gaffer.Box()

		s["b"]["n1"] = GafferTest.AddNode()
		s["b"]["n1"]["op1"].setValue( 10024 )

		s["b"]["n2"] = GafferTest.AddNode()
		s["b"]["n2"]["op1"].setValue( 10023 )

		with Gaffer.PerformanceMonitor() as m :
			with Gaffer.Context() as c :

				s["b"]["n1"]["sum"].getValue()
				s["b"]["n2"]["sum"].getValue()

				c.setFrame( 2 )
				s["b"]["n1"]["sum"].getValue()

		Gaffer.MonitorAlgo.annotate( s, m, Gaffer.MonitorAlgo.PerformanceMetric.ComputeCount )

		self.assertEqual(
			Gaffer.MetadataAlgo.getAnnotation( s["b"]["n1"], "performanceMonitor:computeCount" ).text(),
			"Compute count : 1"
		)
		self.assertEqual(
			Gaffer.MetadataAlgo.getAnnotation( s["b"]["n2"], "performanceMonitor:computeCount" ).text(),
			"Compute count : 1"
		)
		self.assertEqual(
			Gaffer.MetadataAlgo.getAnnotation( s["b"], "performanceMonitor:computeCount" ).text(),
			"Compute count : 2"
		)

		Gaffer.MonitorAlgo.annotate( s, m, Gaffer.MonitorAlgo.PerformanceMetric.HashesPerCompute )

		self.assertEqual(
			Gaffer.MetadataAlgo.getAnnotation( s["b"]["n1"], "performanceMonitor:hashesPerCompute" ).text(),
			"Hashes per compute : 2"
		)
		self.assertEqual(
			Gaffer.MetadataAlgo.getAnnotation( s["b"]["n2"], "performanceMonitor:hashesPerCompute" ).text(),
			"Hashes per compute : 1"
		)
		self.assertEqual(
			Gaffer.MetadataAlgo.getAnnotation( s["b"], "performanceMonitor:hashesPerCompute" ).text(),
			"Hashes per compute : 1.5"
		)

		Gaffer.MonitorAlgo.removePerformanceAnnotations( s )
		for node in Gaffer.Node.RecursiveRange( s ) :
			self.assertEqual(
				Gaffer.Metadata.registeredValues( node, Gaffer.Metadata.RegistrationTypes.Instance ),
				[]
			)

if __name__ == "__main__":
	unittest.main()
