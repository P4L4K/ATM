import secrets

def generate_otp(length=6):
    # The default length is 6, but you can change it as needed
    if length < 1:
        raise ValueError("OTP length must be at least 1")

    # Generate a random number with enough bits to cover the specified length
    max_value = 10**length - 1
    otp = secrets.randbelow(max_value + 1)

    # Format the OTP to ensure it has the specified length
    otp_str = f"{otp:0{length}}"

    return otp_str

