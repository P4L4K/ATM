import os
def open_image():
    file_path = "atm_barcode.jpg"
    try:
        os.startfile(file_path)
    except Exception as e:
        print(f"Error: {e}")


