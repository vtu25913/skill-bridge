"""
modules/utils.py — File text extraction utilities
"""
import io


def extract_text_from_file(uploaded_file) -> str:
    """
    Extract plain text from an uploaded Streamlit file object.
    Returns the extracted text, or a string starting with '[ERROR:' on failure.
    Never returns empty string silently — always explains what happened.
    """
    if uploaded_file is None:
        return ""

    filename = uploaded_file.name.lower()

    # Read all bytes once — Streamlit file pointer can only be read once
    try:
        raw_bytes = uploaded_file.read()
    except Exception as e:
        return f"[ERROR: Could not read file — {e}]"

    # ── Plain text ─────────────────────────────────────────────────────────
    if filename.endswith(".txt") or filename.endswith(".md"):
        try:
            return raw_bytes.decode("utf-8", errors="ignore").strip()
        except Exception as e:
            return f"[ERROR: Could not decode text file — {e}]"

    # ── PDF ────────────────────────────────────────────────────────────────
    if filename.endswith(".pdf"):
        # Try pypdf first
        try:
            import pypdf
            reader = pypdf.PdfReader(io.BytesIO(raw_bytes))
            pages = [page.extract_text() or "" for page in reader.pages]
            text = "\n".join(pages).strip()
            if text:
                return text
        except Exception:
            pass

        # Try pdfplumber as fallback
        try:
            import pdfplumber
            with pdfplumber.open(io.BytesIO(raw_bytes)) as pdf:
                pages = [p.extract_text() or "" for p in pdf.pages]
            text = "\n".join(pages).strip()
            if text:
                return text
        except Exception:
            pass

        return (
            "[ERROR: Could not extract text from this PDF. "
            "It may be image-based (scanned) or corrupted. "
            "Please paste the text manually in the text area below.]"
        )

    # ── DOCX ───────────────────────────────────────────────────────────────
    if filename.endswith(".docx"):
        try:
            from docx import Document
            doc = Document(io.BytesIO(raw_bytes))
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            text = "\n".join(paragraphs).strip()
            if text:
                return text
            return "[ERROR: DOCX file appears to be empty. Please paste the text manually.]"
        except ImportError:
            return (
                "[ERROR: python-docx not installed. "
                "Please paste the resume text manually in the text area below.]"
            )
        except Exception as e:
            return f"[ERROR: Could not read DOCX — {e}. Please paste the text manually.]"

    # ── DOC (old Word format) ──────────────────────────────────────────────
    if filename.endswith(".doc"):
        return (
            "[ERROR: Old .doc format not supported. "
            "Please save as .docx or .txt, or paste the text manually.]"
        )

    # ── Generic fallback ───────────────────────────────────────────────────
    try:
        text = raw_bytes.decode("utf-8", errors="ignore").strip()
        if text:
            return text
        return "[ERROR: File appears empty or unreadable. Please paste text manually.]"
    except Exception as e:
        return f"[ERROR: Unrecognised format — {e}. Please paste text manually.]"