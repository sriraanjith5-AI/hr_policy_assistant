from pypdf import PdfReader


class PDFLoader:

    def __init__(self, file_path):
        self.file_path = file_path

    def load(self):

        reader = PdfReader(self.file_path)

        full_text = ""

        for page in reader.pages:

            full_text += page.extract_text()

        return full_text