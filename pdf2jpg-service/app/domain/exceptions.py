class UnsupportedFileTypeError(Exception):
    def __init__(self, filename: str):
        self.filename = filename
        self.message = f"The file '{self.filename}' is not a supported file type for conversion."
        super().__init__(self.message)

class PDFConversionError(Exception):
    def __init__(self, detail: str = "An error occurred while converting the PDF file."):
        self.message = detail
        super().__init__(self.message)

class ConversionFileNotFoundError(Exception):
    def __init__(self, path: str):
        self.path = path
        self.message = f"The file at path '{self.path}' was not found for conversion."
        super().__init__(self.message)
