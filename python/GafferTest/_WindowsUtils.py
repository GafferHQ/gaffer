import ctypes as ctypes
from ctypes import wintypes as wintypes
from enum import Enum

# Adapted from https://stackoverflow.com/questions/8086412/howto-determine-file-owner-on-windows-using-python-without-pywin32

kernel32 = ctypes.WinDLL( 'kernel32', use_last_error = True )
advapi32 = ctypes.WinDLL( 'advapi32', use_last_error = True )

SE_FILE_OBJECT = 1
OWNER_SECURITY_INFORMATION = 0x00000001
GROUP_SECURITY_INFORMATION = 0x00000002
DACL_SECURITY_INFORMATION = 0x00000004
SACL_SECURITY_INFORMATION = 0x00000008
LABEL_SECURITY_INFORMATION = 0x00000010

class SID_NAME_USE( wintypes.DWORD ) :

	SidTypeUser = 1
	SidTypeGroup = 2
	SidTypeDomain = 3
	SidTypeAlias = 4
	SidTypeWellKnownGroup = 5
	SidTypeDeletedAccount = 6
	SidTypeInvalid = 7
	SidTypeUnknown = 8
	SidTypeComputer = 9
	SidTypeLabel = 10
	SidTypeLogonSession = 11

PSID_NAME_USE = ctypes.POINTER( SID_NAME_USE )

class PLOCAL( wintypes.LPVOID ) :

	__needsFree = False

	def __init__( self, value = None, needsFree = False ) :
		super( PLOCAL, self ).__init__( value )
		self.__needsFree = needsFree

	def __del__( self ):
		if self and self.__needsFree :
			kernel32.LocalFree( self )
			self.__needsFree = False

PACL = PLOCAL

class PSID( PLOCAL ) :

	def __init__( self, value = None, needsFree = False ) :
		super( PSID, self ).__init__( value, needsFree )

	def __str__( self ) :
		if not self:
			raise ValueError( "NULL pointer access" )
		sid = wintypes.LPWSTR()
		advapi32.ConvertSidToStringSidW( self, ctypes.byref( sid ) )
		try:
			return sid.value
		finally:
			if sid:
				kernel32.LocalFree( sid )

class PSECURITY_DESCRIPTOR( PLOCAL ) :
	def __init__( self, value = None, needsFree = False ) :
		super( PSECURITY_DESCRIPTOR, self ).__init__( value, needsFree )
		self.pOwner = PSID()
		self.pGroup = PSID()
		self.pDacl = PACL()
		self.pSacl = PACL()

	def owner( self ) :
		if not self or not self.pOwner :
			raise ValueError( "\"pOwner\" not set." )
		return lookupAccountSid( self.pOwner )

	def group( self ) :
		if not self or not self.pGroup :
			raise ValueError( "\"pGroup\" not set." )
		return lookupAccountSid( self.pGroup )

def lookupAccountSid( sid ) :
	SIZE = 256
	name = ctypes.create_unicode_buffer( SIZE )
	domain = ctypes.create_unicode_buffer( SIZE )
	cch_name = wintypes.DWORD( SIZE )
	cch_domain = wintypes.DWORD( SIZE )
	sid_type = SID_NAME_USE()
	advapi32.LookupAccountSidW(
		None,  # In : System Name
		sid,  # In : SID
		name,  # Out : Name
		ctypes.byref( cch_name ),  # In / Out : cchName
		domain,  # Out : Domain
		ctypes.byref( cch_domain ),  # In / Out : cchDomain
		ctypes.byref( sid_type )  # Out : Use
	)
	return name.value, domain.value

def getFileSecurity(
	fileName,
	request = (
		OWNER_SECURITY_INFORMATION |
		GROUP_SECURITY_INFORMATION
	)
):
	pSD = PSECURITY_DESCRIPTOR( needsFree = True )
	error = advapi32.GetNamedSecurityInfoW(
		fileName,  # In : File name
		SE_FILE_OBJECT,  # In : Object Type
		request,  # In : Security Info
		ctypes.byref( pSD.pOwner ),  # Out : Owner
		ctypes.byref( pSD.pGroup ),  # Out : Group
		ctypes.byref( pSD.pDacl ),  # Out : DACL (Discretionary access control list)
		ctypes.byref( pSD.pSacl ),  # Out : SACL (System access control list)
		ctypes.byref( pSD )  # Out : Security Descriptor
	)
	if error != 0:
		raise ctypes.WinError( error )
	return pSD
