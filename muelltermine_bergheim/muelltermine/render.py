from io import BytesIO
from math import sqrt
from threading import Lock

import pypdfium2

# PDFium calls must not run concurrently across HTTP threads.
RENDER_LOCK = Lock()


def render_page(content: bytes, page_number: int) -> bytes:
    with RENDER_LOCK:
        document = pypdfium2.PdfDocument(content)
        try:
            if not 1 <= page_number <= len(document):
                raise ValueError('Unbekannte PDF-Seite.')
            page = document[page_number - 1]
            try:
                width, height = page.get_size()
                scale = min(1.5, sqrt(6_000_000 / (width * height)))
                bitmap = page.render(scale=scale)
                try:
                    image = bitmap.to_pil()
                    stream = BytesIO()
                    image.save(stream, format='PNG')
                    image.close()
                    return stream.getvalue()
                finally:
                    bitmap.close()
            finally:
                page.close()
        finally:
            document.close()
