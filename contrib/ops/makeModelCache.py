import os
import glob

import IECore

class makeModelCache( IECore.Op ) :

	def __init__( self ) :
	
		IECore.Op.__init__( self, "Makes model caches out of arbitrary lists of geometry files.", IECore.FileNameParameter( "result", "" ) )
		
		self.parameters().addParameters(
			
			[
				IECore.PathVectorParameter(
					"inputPaths",
					"A list of files and/or directories containing geometry to be merged into the model cache.",
					defaultValue = IECore.StringVectorData(),
				),
				IECore.FileNameParameter(
					"outputFile",
					"The filename of the model cache to be written",
					defaultValue = "",
					allowEmptyString = False,
				),
			],
			
		)

	def doOperation( self, args ) :
	
		files = []
		for path in args["inputPaths"] :
		
			if os.path.isfile( path ) :
				files.append( path )
			elif os.path.isdir( path ) :
				files.extend( glob.glob( path + "/*.cob" ) )
				
		if not files :
			raise Exception( "No valid files found" )
			
		outFile = IECore.FileIndexedIO( args["outputFile"].value, "/", IECore.IndexedIOOpenMode.Write )
		
		header = IECore.HeaderGenerator.header()
		header.save( outFile, "header" )
		
		combinedBound = IECore.Box3f()
		
		outFile.mkdir( "root" )
		outFile.chdir( "root" )
		outFile.mkdir( "children" )
		outFile.chdir( "children" )
		
		for f in files :
		
			reader = None
			with IECore.IgnoredExceptions( RuntimeError ) :
				reader = IECore.Reader.create( f )
			
			if reader is None :
				continue
				
			o = None
			with IECore.IgnoredExceptions( RuntimeError ) :
				o = reader.read()
				
			if not isinstance( o, IECore.Primitive ) :
				continue
			
			name = os.path.splitext( os.path.basename( f ) )[0]
			outFile.mkdir( name )
			outFile.chdir( name )
			
			o.save( outFile, "geometry" )
			
			b = o.bound()
			combinedBound.extendBy( b )
			
			outFile.write(
				"bound",
				IECore.FloatVectorData( [
					b.min.x, b.min.y, b.min.z,
					b.max.x, b.max.y, b.max.z,
				] )
			)
			
			outFile.write(
				"transform",
				IECore.FloatVectorData( [
					1, 0, 0, 0,
					0, 1, 0, 0,
					0, 0, 1, 0,
					0, 0, 0, 1,
				] )
			)
			
			outFile.chdir( ".." )
		
		outFile.chdir( ".." )
		outFile.write(
			"bound",
			IECore.FloatVectorData( [
				combinedBound.min.x, combinedBound.min.y, combinedBound.min.z,
				combinedBound.max.x, combinedBound.max.y, combinedBound.max.z,
			] )
		)

		outFile.write(
				"transform",
				IECore.FloatVectorData( [
					1, 0, 0, 0,
					0, 1, 0, 0,
					0, 0, 1, 0,
					0, 0, 0, 1,
				] )
			)
	
		return args["outputFile"].value
			
IECore.registerRunTimeTyped( makeModelCache )