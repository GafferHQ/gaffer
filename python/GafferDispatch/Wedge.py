##########################################################################
#
#  Copyright (c) 2015, Image Engine Design Inc. All rights reserved.
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

import enum
import imath

import IECore

import Gaffer
import GafferDispatch

class Wedge( GafferDispatch.TaskContextProcessor ) :

	Mode = enum.IntEnum( "Mode", [ "FloatRange", "IntRange", "ColorRange", "FloatList", "IntList", "StringList" ], start = 0 )

	def __init__( self, name = "Wedge" ) :

		GafferDispatch.TaskContextProcessor.__init__( self, name )

		self["variable"] = Gaffer.StringPlug( defaultValue = "wedge:value" )
		self["indexVariable"] = Gaffer.StringPlug( defaultValue = "wedge:index" )

		self["mode"] = Gaffer.IntPlug(
			defaultValue = int( self.Mode.FloatRange ),
			minValue = int( self.Mode.FloatRange ),
			maxValue = int( self.Mode.StringList ),
		)

		# float range

		self["floatMin"] = Gaffer.FloatPlug( defaultValue = 0 )
		self["floatMax"] = Gaffer.FloatPlug( defaultValue = 1 )
		self["floatSteps"] = Gaffer.IntPlug( minValue = 2, defaultValue = 11 )

		# int range

		self["intMin"] = Gaffer.IntPlug( defaultValue = 0 )
		self["intMax"] = Gaffer.IntPlug( defaultValue = 5 )
		self["intStep"] = Gaffer.IntPlug( minValue = 1, defaultValue = 1 )

		# color range

		self["ramp"] = Gaffer.SplinefColor3fPlug(
			defaultValue = Gaffer.SplineDefinitionfColor3f(
				(
					( 0, imath.Color3f( 0 ) ),
					( 1, imath.Color3f( 1 ) ),
				),
				Gaffer.SplineDefinitionInterpolation.CatmullRom
			)
		)

		self["colorSteps"] = Gaffer.IntPlug( defaultValue = 5, minValue = 2 )

		# lists

		self["floats"] = Gaffer.FloatVectorDataPlug( defaultValue = IECore.FloatVectorData() )
		self["ints"] = Gaffer.IntVectorDataPlug( defaultValue = IECore.IntVectorData() )
		self["strings"] = Gaffer.StringVectorDataPlug( defaultValue = IECore.StringVectorData() )

	def values( self ) :

		mode = self.Mode( self["mode"].getValue() )
		if mode == self.Mode.FloatRange :

			min = self["floatMin"].getValue()
			max = self["floatMax"].getValue()
			steps = self["floatSteps"].getValue()

			values = []
			for i in range( 0, steps ) :
				t = float( i ) / ( steps - 1 )
				values.append( min + t * ( max - min ) )

		elif mode == self.Mode.IntRange :

			min = self["intMin"].getValue()
			max = self["intMax"].getValue()
			step = self["intStep"].getValue()

			if max < min :
				min, max = max, min

			if step == 0 :
				raise RuntimeError( "Invalid step - step must not be 0" )
			elif step < 0 :
				step = -step

			values = []
			while True :
				value = min + len( values ) * step
				if value > max :
					break
				values.append( value )

		elif mode == self.Mode.ColorRange :

			spline = self["ramp"].getValue().spline()
			steps = self["colorSteps"].getValue()
			values = [ spline( i / float( steps - 1 ) ) for i in range( 0, steps ) ]

		elif mode == self.Mode.FloatList :

			values = self["floats"].getValue()

		elif mode == self.Mode.IntList :

			values = self["ints"].getValue()

		elif mode == self.Mode.StringList :

			values = self["strings"].getValue()

		return values

	def _processedContexts( self, context ) :

		# make a context for each of the wedge values

		variable = self["variable"].getValue()
		indexVariable = self["indexVariable"].getValue()

		contexts = []
		for index, value in enumerate( self.values() ) :
			contexts.append( Gaffer.Context( context ) )
			contexts[-1][variable] = value
			contexts[-1][indexVariable] = index

		return contexts

IECore.registerRunTimeTyped( Wedge, typeName = "GafferDispatch::Wedge" )
