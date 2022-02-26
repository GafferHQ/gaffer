import os
import random
import math

directory = os.path.dirname( os.path.realpath( __file__ ) )


smallSize = 100
largeSize = 8000
colorSize = 5000

bigLUTSize = 9
smallLUTSize = 5

random.seed( 42 )

f = open( os.path.join( directory, "pandemoniumSmall1D.spi1d" ), "w" )
f.write( """
Version 1
From -0.125 1.125
Length %i
Components 1
{
""" % smallSize )
for i in range( smallSize ):
	f.write( "\t%f\n" % random.random() )
f.write( "}" )
f.close()

f = open( os.path.join( directory, "pandemoniumLarge1D.spi1d" ), "w" )
f.write( """
Version 1
From -0.125 1.125
Length %i
Components 1
{
""" % largeSize )
for i in range( largeSize ):
	t = i / ( largeSize / math.pi )
	# Can't have too many high frequency transforms where every element is random, or else we magnify floating
	# point inaccuracy too much, so use a sine instead for some transforms
	f.write( "\t%f\n" % math.sin( t ) )
f.write( "}" )
f.close()

f = open( os.path.join( directory, "pandemoniumColor1D.spi1d" ), "w" )
f.write( """
Version 1
From -0.125 1.125
Length %i
Components 3
{
""" % colorSize )
for i in range( colorSize ):
	t = i / ( largeSize / math.pi )
	f.write( "\t%f %f %f\n" % ( math.sin( t ), math.sin( t * 2 ) * 0.5 + 0.5, math.sin( t * 3 ) * 0.5 + 0.5  ) )
f.write( "}" )
f.close()

f = open( os.path.join( directory, "pandemoniumBig.cube" ), "w" )
f.write( "LUT_3D_SIZE %i\n" % bigLUTSize )
for i in range( bigLUTSize * bigLUTSize * bigLUTSize ):
	f.write( "\t%f %f %f\n" % ( random.random(), random.random(), random.random() ) )
f.close()

f = open( os.path.join( directory, "pandemoniumSmall.cube" ), "w" )
f.write( "LUT_3D_SIZE %i\n" % smallLUTSize )
for i in range( smallLUTSize * smallLUTSize * smallLUTSize ):
	f.write( "\t%f %f %f\n" % ( random.random(), random.random(), random.random() ) )
f.close()
