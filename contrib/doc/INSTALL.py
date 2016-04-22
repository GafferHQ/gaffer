#!/usr/bin/env python

from optparse import OptionParser
import os,sys


class installationTool():
	
	def cmdLine(self):
		usage = "%prog [options]"
		
		parser = OptionParser(usage=usage)
		parser.add_option("-a", "--runall",
							action="store_true",
							dest="runall_flag",
							default=False,
							help="Run reference doc generation process")
		parser.add_option("-r", "--runreference",
							action="store_true",
							dest="runreference_flag",
							default=False,
							help="Run reference doc generation process")
		parser.add_option("-g", "--runguide",
							action="store_true",
							dest="runguide_flag",
							default=False,
							help="Run user guide generation process")
		parser.add_option("-l", "--runlicenses",
							action="store_true",
							dest="runlicenses_flag",
							default=False,
							help="Run licenses generation process")
		parser.add_option("-d", "--runasciidoc",
							action="store_true",
							dest="runasciidoc_flag",
							default=False,
							help="Run the asciidoc conversion process")
		parser.add_option("-p", "--runpdf",
							action="store_true",
							dest="runpdf_flag",
							default=False,
							help="Run the pdf conversion process")
		parser.add_option("-i", "--images",
							action="store_true",
							dest="images_flag",
							default=False,
							help="Generate the Gaffer UI images")
		parser.add_option("-v", "--verbose",
							type='int',
							dest="verbose_flag",
							default=0,
							help="Enable verbose output from cmds")
		
		(opts, args) = parser.parse_args()
		
		#check to see if we have been passed any flags. if no flags, this tmp will stay False
		tmp = False
		for opt, value in opts.__dict__.items():
			if opt != 'verbose_flag':
				if value:
					tmp = True
		
		self.opts = {}
		
		if tmp == False or opts.runall_flag:
			#we have no flags, so we want to treat that the same as --all=True
			#turn everything on
			for opt, value in opts.__dict__.items():
				if opt == 'verbose_flag':
					self.opts[opt] = value
				else:
					self.opts[opt] = True
				
		else:
			for opt, value in opts.__dict__.items():
				self.opts[opt] = value
		
		self.runCommands()
		
	
	def logit(self,message):
		'''
		simple formatted output.
		only enabled in verbose mode
		'''
		if self.opts['verbose_flag']:
			print '\033[92m%s:\033[0m %s' % (self.messageHeader,message)
	
	
	def runCommands(self):
	
		gp_cmd = 'gaffer python'
		ad_cmd = 'asciidoc'
		sg_cmd = 'gaffer screengrab'
		pdf_cmd = 'prince'
		if self.opts['verbose_flag'] > 1: #extra verbose
			ad_cmd += ' -v'
			pdf_cmd += ' -v'
		
		build_root = os.getcwd()
		
		if self.opts['runreference_flag']:
			#build the node reference
			os.chdir( os.path.join (build_root, 'GafferNodeReference' ))
			self.messageHeader = 'GafferNodeReference'
			
			self.logit('Running any dynamic content generation scripts...')
			prescripts_dir = os.path.join( build_root, 'GafferNodeReference', 'dynamicContentGenerators' )
			if os.path.exists(prescripts_dir):
			    for script in os.listdir( prescripts_dir  ):
				    self.logit( script )
				    os.system( gp_cmd + ' ' + os.path.join( prescripts_dir, script ))
			
			
			if self.opts['runasciidoc_flag']:
				## run asciidoc then convert the result into a pdf
				self.logit('Processing Asciidoc source...')
				os.system( ad_cmd + ' GafferNodeReference.txt' )
			if self.opts['runpdf_flag']:
				self.logit('Postconverting html to pdf...')
				os.system( pdf_cmd + ' GafferNodeReference.html GafferNodeReference.pdf' )
			
			self.logit('Done.')


		if self.opts['runlicenses_flag']:
			#build the node reference
			os.chdir( os.path.join (build_root, 'GafferLicenses' ))
			self.messageHeader = 'GafferLicenses'
			
			self.logit('Running any dynamic content generation scripts...')
			prescripts_dir = os.path.join( build_root, 'GafferLicenses', 'dynamicContentGenerators' )
			if os.path.exists(prescripts_dir):
			    for script in os.listdir( prescripts_dir  ):
				    self.logit( script )
				    os.system( gp_cmd + ' ' + os.path.join( prescripts_dir, script ))
			
			
			if self.opts['runasciidoc_flag']:
				## run asciidoc then convert the result into a pdf
				self.logit('Processing Asciidoc source...')
				os.system( ad_cmd + ' GafferLicenses.txt' )
			if self.opts['runpdf_flag']:
				self.logit('Postconverting html to pdf...')
				os.system( pdf_cmd + ' GafferLicenses.html GafferLicenses.pdf' )
			
			self.logit('Done.')


		if self.opts['runguide_flag']:
			#build the user guide
			os.chdir( os.path.join( build_root, 'GafferUserGuide' ))
			self.messageHeader = 'GafferUserGuide'
			
			self.logit('Running any dynamic content generation scripts...')
			prescripts_dir = os.path.join( build_root, 'GafferUserGuide', 'dynamicContentGenerators' )
			if os.path.exists(prescripts_dir):
			    for script in os.listdir( prescripts_dir  ):
				    self.logit( script )
				    os.system( gp_cmd + ' ' + os.path.join( prescripts_dir, script ))
			
			if self.opts['images_flag']:
				##generate images from reference scripts
				self.logit('Generating Gaffer UI images...')
				source_dir = os.path.join( build_root, 'GafferUserGuide', 'images', 'autoGenerated_source' )
				target_dir = os.path.join( build_root, 'GafferUserGuide', 'images', 'autoGenerated_target' )
				
				for source in sorted(os.listdir( source_dir )):
					if source.endswith('.gfr'):
						self.logit('Processing [ %s ]' % ( source ) )
						target_img = source[:-4] + ".png"
						sg_cmd_full = "%s -script %s -image %s" % \
										(sg_cmd, os.path.join( source_dir, source ), os.path.join( target_dir, target_img ) )
						
						pythonfile = os.path.join( source_dir, source[:-4] + '.py' )
						if os.path.exists( pythonfile ):
							#there is a corresponding post launch python file
							sg_cmd_full = '%s -cmdfile %s' % ( sg_cmd_full, pythonfile)
							
						self.logit( sg_cmd_full )
						os.system( sg_cmd_full )
			
			if self.opts['runasciidoc_flag']:
				## run asciidoc then convert the result into a pdf
				self.logit('Processing Asciidoc source...')
				os.system( ad_cmd + " GafferUserGuide.txt" )
				
			if self.opts['runpdf_flag']:
				self.logit('Postconverting html to pdf...')
				os.system( pdf_cmd + " GafferUserGuide.html GafferUserGuide.pdf" )
			
			self.logit('Done.')


if __name__ == "__main__":
	# run the code
	doIt=installationTool()
	doIt.cmdLine()
