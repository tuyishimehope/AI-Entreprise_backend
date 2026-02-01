import pymupdf


class DocumentProcessor:
    @staticmethod
    def extract_text(filename: str, extension: str) -> str:
        text_parts = []
        with pymupdf.open(filename=filename, filetype=extension) as doc:
            for page in doc:
                text_parts.append(page.get_text())
        return "\n".join(text_parts)
