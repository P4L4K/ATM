import hashlib
import base64

import hashlib
import base64

import hashlib
import base64

def generate_unique_code(input_string):
    # Use SHA-256 hash function
    hash_object = hashlib.sha256(input_string.encode())
    # Get the hexadecimal digest
    hex_digest = hash_object.hexdigest()
    # Filter out only alphabetic characters from the digest
    filtered_hex = ''.join(c for c in hex_digest if c.isalpha())
    # Take the first 6 characters of the filtered digest
    unique_code = filtered_hex[:6]
    
    return unique_code.upper()  # Convert to uppercase to ensure alphabets only




