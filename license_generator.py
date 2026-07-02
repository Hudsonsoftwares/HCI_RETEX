import json
import hmac
import hashlib
import secrets
import string
import datetime
import os

SECRET_SALT = "V3nD0r_S3cr3t_S@lt_2026!"

def generate_license():
    print("=== Odoo Module License Generator ===")
    customer = input("Customer Name: ")
    company = input("Company Name: ")
    email = input("Customer Email (optional): ")
    db_uuid = input("Database UUID (optional, press Enter to skip): ")
    expiry = input("Expiry Date (YYYY-MM-DD): ")
    modules = input("Licensed Modules (comma separated): ")
    
    try:
        datetime.datetime.strptime(expiry, '%Y-%m-%d')
    except ValueError:
        print("Invalid date format. Must be YYYY-MM-DD.")
        return

    chars = string.ascii_uppercase + string.digits
    segments = [''.join(secrets.choice(chars) for _ in range(4)) for _ in range(4)]
    license_key = 'OD18-' + '-'.join(segments)

    payload = {
        "license_key": license_key,
        "customer": customer,
        "company": company,
        "database_uuid": db_uuid,
        "expiry": expiry,
        "grace_period": 15,
        "max_activations": 1,
        "modules": modules
    }

    # Sign the payload
    payload_str = json.dumps(payload, sort_keys=True)
    signature = hmac.new(SECRET_SALT.encode(), payload_str.encode(), hashlib.sha256).hexdigest()
    payload["signature"] = signature
    
    filename = f"license_{license_key}.json"
    
    with open(filename, 'w') as f:
        json.dump(payload, f, indent=4)
        
    print(f"\nSuccess! License generated and saved to {os.path.abspath(filename)}")
    print(f"License Key: {license_key}")
    print("Please send this file to your client.")

if __name__ == "__main__":
    generate_license()
