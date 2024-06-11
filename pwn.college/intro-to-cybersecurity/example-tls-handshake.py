import base64
import json
import os
import re
from Crypto.Cipher import AES
from Crypto.Hash.SHA256 import SHA256Hash
from Crypto.PublicKey import RSA
from Crypto.Random.random import getrandbits
from Crypto.Util.Padding import pad, unpad


"""
    p = int.from_bytes(bytes.fromhex(
        "FFFFFFFF FFFFFFFF C90FDAA2 2168C234 C4C6628B 80DC1CD1 "
        "29024E08 8A67CC74 020BBEA6 3B139B22 514A0879 8E3404DD "
        "EF9519B3 CD3A431B 302B0A6D F25F1437 4FE1356D 6D51C245 "
        "E485B576 625E7EC6 F44C42E9 A637ED6B 0BFF5CB6 F406B7ED "
        "EE386BFB 5A899FA5 AE9F2411 7C4B1FE6 49286651 ECE45B3D "
        "C2007CB8 A163BF05 98DA4836 1C55D39A 69163FA8 FD24CF5F "
        "83655D23 DCA3AD96 1C62F356 208552BB 9ED52907 7096966D "
        "670C354E 4ABC9804 F1746C08 CA18217C 32905E46 2E36CE3B "
        "E39E772C 180E8603 9B2783A2 EC07A28F B5C55DF0 6F4C52C9 "
        "DE2BCBF6 95581718 3995497C EA956AE5 15D22618 98FA0510 "
        "15728E5A 8AACAA68 FFFFFFFF FFFFFFFF"
    ), "big")
    g = 2

    show_hex("p", p)
    show_hex("g", g)

    root_key = RSA.generate(2048)

    show_hex("root key d", root_key.d)

    root_certificate = {
        "name": "root",
        "key": {
            "e": root_key.e,
            "n": root_key.n,
        },
        "signer": "root",
    }

    root_trusted_certificates = {
        "root": root_certificate,
    }

    root_certificate_data = json.dumps(root_certificate).encode()
    root_certificate_hash = SHA256Hash(root_certificate_data).digest()
    root_certificate_signature = pow(
        int.from_bytes(root_certificate_hash, "little"),
        root_key.d,
        root_key.n
    ).to_bytes(256, "little")

    show_b64("root certificate", root_certificate_data)
    show_b64("root certificate signature", root_certificate_signature)

    name = ''.join(random.choices(string.ascii_lowercase, k=16))
    show("name", name)

    a = getrandbits(2048)
    A = pow(g, a, p)
    show_hex("A", A)

    B = input_hex("B")
    if not (B > 2**1024):
        print("Invalid B value (B <= 2**1024)", file=sys.stderr)
        exit(1)

    s = pow(B, a, p)
    key = SHA256Hash(s.to_bytes(256, "little")).digest()[:16]
    cipher_encrypt = AES.new(key=key, mode=AES.MODE_CBC, iv=b"\0"*16)
    cipher_decrypt = AES.new(key=key, mode=AES.MODE_CBC, iv=b"\0"*16)

    def decrypt_input_b64(name):
        data = input_b64(name)
        try:
            return unpad(cipher_decrypt.decrypt(data), cipher_decrypt.block_size)
        except ValueError as e:
            print(f"{name}: {e}", file=sys.stderr)
            exit(1)

    user_certificate_data = decrypt_input_b64("user certificate")
    user_certificate_signature = decrypt_input_b64("user certificate signature")
    user_signature = decrypt_input_b64("user signature")

    try:
        user_certificate = json.loads(user_certificate_data)
    except json.JSONDecodeError:
        print("Invalid user certificate", file=sys.stderr)
        exit(1)

    user_name = user_certificate.get("name")
    if user_name != name:
        print(f"Invalid user certificate name: `{user_name}`", file=sys.stderr)
        exit(1)

    user_key = user_certificate.get("key", {})
    if not (isinstance(user_key.get("e"), int) and isinstance(user_key.get("n"), int)):
        print(f"Invalid user certificate key: `{user_key}`", file=sys.stderr)
        exit(1)

    if not (user_key["e"] > 2):
        print("Invalid user certificate key e value (e > 2)", file=sys.stderr)
        exit(1)

    if not (2**512 < user_key["n"] < 2**1024):
        print("Invalid user certificate key n value (2**512 < n < 2**1024)", file=sys.stderr)
        exit(1)

    user_signer = user_certificate.get("signer")
    if user_signer not in root_trusted_certificates:
        print(f"Untrusted user certificate signer: `{user_signer}`", file=sys.stderr)
        exit(1)

    user_signer_key = root_trusted_certificates[user_signer]["key"]
    user_certificate_hash = SHA256Hash(user_certificate_data).digest()
    user_certificate_check = pow(
        int.from_bytes(user_certificate_signature, "little"),
        user_signer_key["e"],
        user_signer_key["n"]
    ).to_bytes(256, "little")[:len(user_certificate_hash)]

    if user_certificate_check != user_certificate_hash:
        print("Untrusted user certificate: invalid signature", file=sys.stderr)
        exit(1)

    user_signature_data = (
        name.encode().ljust(256, b"\0") +
        A.to_bytes(256, "little") +
        B.to_bytes(256, "little")
    )
    user_signature_hash = SHA256Hash(user_signature_data).digest()
    user_signature_check = pow(
        int.from_bytes(user_signature, "little"),
        user_key["e"],
        user_key["n"]
    ).to_bytes(256, "little")[:len(user_signature_hash)]

    if user_signature_check != user_signature_hash:
        print("Untrusted user: invalid signature", file=sys.stderr)
        exit(1)

    ciphertext = cipher_encrypt.encrypt(pad(flag, cipher_encrypt.block_size))
    show_b64("secret ciphertext", ciphertext)
"""


b = getrandbits(2048)
g = 2
p = None
A = None
d = None
e = None
n = None
name = None
user_key = RSA.generate(1024)
pat0 = re.compile(r".*p: 0x(.*)\n")
pat1 = re.compile(r".*root key d: 0x(.*)\n")
pat2 = re.compile(r".*root certificate \(b64\): (.*)\n")
pat3 = re.compile(r".*name: (.*)\n")
pat4 = re.compile(r".*A: (.*)\n")
pat5 = re.compile(r".*secret ciphertext \(b64\): (.*)\n")
r_pipe0, w_pipe0 = os.pipe()
r_pipe1, w_pipe1 = os.pipe()

pid = os.fork()

if pid == -1:
	print("Error fork.")
	exit(1)

if pid == 0:
	os.close(w_pipe0)
	os.close(r_pipe1)

	os.dup2(r_pipe0, 0)
	os.close(r_pipe0)

	os.dup2(w_pipe1, 1)
	os.close(w_pipe1)

	os.execv("/challenge/run", ["/challenge/run"])
	print("Error execv.")
	exit(1)

os.close(r_pipe0)
os.close(w_pipe1)

output = os.fdopen(r_pipe1, "r")
input = os.fdopen(w_pipe0, "wb")

while True:
	line = output.readline()
	print(line)
	m = pat0.match(line)
	if m:
		p = int(m.group(1), 16)
		print(f"p = {p}")
	m = pat1.match(line)
	if m:
		d = int(m.group(1), 16)
		print(f"d = {d}")
	m = pat2.match(line)
	if m:
		cert = base64.standard_b64decode(m.group(1).encode("utf-8")).decode("utf-8")
		cert = json.loads(cert)
		e = cert["key"]["e"]
		n = cert["key"]["n"]
		print(f"cert = {cert}, e = {e}, n = {n}")
	m = pat3.match(line)
	if m:
		name = m.group(1)
	m = pat4.match(line)
	if m:
		A = int(m.group(1), 16)
		s = pow(A, b, p)
		key = SHA256Hash(s.to_bytes(256, "little")).digest()[:16]
		cipher_encrypt = AES.new(key=key, mode=AES.MODE_CBC, iv=b"\0"*16)
		cipher_decrypt = AES.new(key=key, mode=AES.MODE_CBC, iv=b"\0"*16)
		print(f"A = {A}, s = {s}, key = {key}")
		B = pow(g, b, p)
		input.write(hex(B).encode("utf-8") + b"\n")
		input.flush()
		user_certificate = {
			"name": name,
			"key": {
				"e": user_key.e,
				"n": user_key.n,
			},
			"signer": "root",
		}
		user_certificate_data = json.dumps(user_certificate).encode()
		user_certificate_hash = SHA256Hash(user_certificate_data).digest()
		user_certificate_signature = pow(int.from_bytes(user_certificate_hash, "little"), d, n).to_bytes(256, "little")
		user_signature_data = name.encode().ljust(256, b"\0") + A.to_bytes(256, "little") + B.to_bytes(256, "little")
		user_signature_hash = SHA256Hash(user_signature_data).digest()
		user_signature = pow(int.from_bytes(user_signature_hash, "little"), user_key.d, user_key.n).to_bytes(256, "little")
		user_certificate_data_cipher = cipher_encrypt.encrypt(pad(user_certificate_data, cipher_encrypt.block_size))
		user_certificate_signature_cipher = cipher_encrypt.encrypt(pad(user_certificate_signature, cipher_encrypt.block_size))
		user_signature_cipher = cipher_encrypt.encrypt(pad(user_signature, cipher_encrypt.block_size))
		input.write(base64.standard_b64encode(user_certificate_data_cipher) + b"\n")
		input.flush()
		input.write(base64.standard_b64encode(user_certificate_signature_cipher) + b"\n")
		input.flush()
		input.write(base64.standard_b64encode(user_signature_cipher) + b"\n")
		input.flush()
	m = pat5.match(line)
	if m:
		flag = unpad(cipher_decrypt.decrypt(base64.standard_b64decode(m.group(1).encode("utf-8"))), cipher_decrypt.block_size)
		print(flag)
		break
