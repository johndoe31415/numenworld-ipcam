#	numenworld-ipcam - Reverse engineering of the NuMenWorld NCV-I536A IP camera
#	Copyright (C) 2019-2019 Johannes Bauer
#
#	This file is part of numenworld-ipcam.
#
#	numenworld-ipcam is free software; you can redistribute it and/or modify
#	it under the terms of the GNU General Public License as published by
#	the Free Software Foundation; this program is ONLY licensed under
#	version 3 of the License, later versions are explicitly excluded.
#
#	numenworld-ipcam is distributed in the hope that it will be useful,
#	but WITHOUT ANY WARRANTY; without even the implied warranty of
#	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#	GNU General Public License for more details.
#
#	You should have received a copy of the GNU General Public License
#	along with numenworld-ipcam; if not, write to the Free Software
#	Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
#	Johannes Bauer <JohannesBauer@gmx.de>

import hashlib

class HorrificallyBrokenPasswordFunction():
	@classmethod
	def derive(self, passphrase):
		alphabet = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
		assert(len(alphabet) == 62)
		passphrase = passphrase.encode("utf-8")
		hashval = hashlib.md5(passphrase).digest()
		encoded = ""
		for i in range(0, 16, 2):
			index = (hashval[i] + hashval[i + 1]) % len(alphabet)
			char = alphabet[index]
			encoded += char
		return encoded

if __name__ == "__main__":
	assert(HorrificallyBrokenPasswordFunction.derive("") == "tlJwpbo6")
	assert(HorrificallyBrokenPasswordFunction.derive("abc") == "LkM7s2Ht")
