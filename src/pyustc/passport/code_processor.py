import re

def default_processer(img: bytes):
    """
    The default code processer, using pytesseract to recognize the validate code.
    """
    import os
    try:
        import pytesseract
    except ImportError:
        raise ImportError("Please install tesseract to use the default code processer")
    temp_path = "code.tmp.jpg"
    while os.path.exists(temp_path):
        temp_path += ".jpg"
    with open(temp_path, "wb") as f:
        f.write(img)
    code: str = pytesseract.image_to_string(temp_path)
    os.remove(temp_path)
    code = re.sub(r"\D", "", code.strip())
    if len(code) == 4:
        return code

code_processer = default_processer
def set_code_processer(processer):
    global code_processer
    code_processer = processer
