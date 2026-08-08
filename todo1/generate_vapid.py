
#from py_vapid import Vapid
#from cryptography.hazmat.primitives import serialization

#vapid = Vapid()
#vapid.generate_keys()

#print(vapid.private_pem().decode())

#public_key = vapid.public_key.public_bytes(
#    encoding=serialization.Encoding.X962,
#    format=serialization.PublicFormat.UncompressedPoint,
#)

#print(public_key.hex())

#import base64

#public_key = vapid.public_key.public_bytes(
#    encoding=serialization.Encoding.X962,
#    format=serialization.PublicFormat.UncompressedPoint,
#)

#public_key_b64 = base64.urlsafe_b64encode(public_key).rstrip(b'=')

#print(public_key_b64.decode())


from py_vapid import Vapid
from cryptography.hazmat.primitives import serialization
import base64

vapid = Vapid()
vapid.generate_keys()

print("PRIVATE:")
print(vapid.private_pem().decode())

public_key = vapid.public_key.public_bytes(
    encoding=serialization.Encoding.X962,
    format=serialization.PublicFormat.UncompressedPoint,
)

public_key_b64 = base64.urlsafe_b64encode(public_key).rstrip(b'=')

print("PUBLIC:")
print(public_key_b64.decode())