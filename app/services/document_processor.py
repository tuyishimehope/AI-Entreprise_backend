import pymupdf


class DocumentProcessor:
    @staticmethod
    def extract_text(content: bytes, extension: str) -> str:
        text_parts = []
        with pymupdf.open(stream=content, filetype=extension) as doc:
            for page in doc:
                text_parts.append(page.get_text())
        return "\n".join(text_parts)
