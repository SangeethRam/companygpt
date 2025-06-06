import os
import re
import glob
import pandas as pd
from io import StringIO
from typing import List
from docx import Document
from pptx import Presentation
from tempfile import gettempdir
from datetime import datetime
import hashlib
# from fastapi import FastAPI
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from typing import Dict, List
from pydantic import BaseModel


load_dotenv()

GEN_DOC_PORT = os.getenv("GEN_DOC_PORT")
mcp = FastMCP("GenerateDocuments", port=GEN_DOC_PORT)
BASE_URL = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.abspath(os.path.join(BASE_URL, ".."))
PPT_TEMPLATE_DATA_DIR = os.path.join(BACKEND_DIR, "data", "doctemplates")
ppt_filename = "Orion_Innovation_Template.pptx"
ppt_template_path = os.path.join(PPT_TEMPLATE_DATA_DIR, ppt_filename)
TEMP_DIR = gettempdir()
os.makedirs(TEMP_DIR, exist_ok=True)

# Metadata store to map content hashes to filenames
generated_docs = {}

class Slide(BaseModel):
    layout: int
    placeholders: List[str]

# --- Helpers ---

def sanitize_filename(text: str, max_length: int = 50) -> str:
    text = text.replace('\n', ' ').replace('\r', ' ')
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    text = text.replace(' ', '_')
    return text[:max_length] or "document"

def get_content_hash(content: str) -> str:
    return hashlib.sha256(content.encode('utf-8')).hexdigest()

def generate_timestamped_filename(base_name: str, ext: str) -> str:
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    return f"{base_name}_{timestamp}.{ext}"

def combine_placeholders(slides: List[Slide]) -> List[Dict]:
    structured = []
    for slide in slides:
        title = slide.placeholders[0] if slide.placeholders else ""
        content = "\n".join(slide.placeholders[1:]) if len(slide.placeholders) > 1 else ""
        structured.append({
            "layout": slide.layout,
            "placeholders": [title, content] if content else [title]
        })
    return structured

# --- Prompts ---
@mcp.prompt("""
When the user asks to generate a document, choose the appropriate tool:
- Use `Generate_PPT` for presentations. Format slides as: [{"layout": 0, "placeholders": ["Title", "Date"]}, {"layout": 1, "placeholders": ["Title", "Content"]}
- Use `Generate_Word_Doc` for narrative or textual content. Pass the text as a single string.
- Use `Generate_Excel` for tabular data. Accept a CSV string as input.

Always include relevant structure to make the tool call successful.
""")

# --- Tools ---

@mcp.tool(name="Generate_Word_Doc", description="Generate a Word document from input content")
async def generate_word_doc(content: str) -> str:
    content_hash = get_content_hash(content)

    # Check reuse
    if content_hash in generated_docs:
        return generated_docs[content_hash]

    # Generate new file
    doc = Document()
    doc.add_heading("Generated Document", 0)
    doc.add_paragraph(content)

    filename = generate_timestamped_filename(sanitize_filename(content), "docx")
    file_path = os.path.join(TEMP_DIR, filename)
    doc.save(file_path)

    generated_docs[content_hash] = file_path
    return file_path

@mcp.tool(name="Generate_Excel", description="Generate an Excel file from CSV string")
async def generate_excel(csv_data: str) -> str:
    content_hash = get_content_hash(csv_data)
    if content_hash in generated_docs:
        return generated_docs[content_hash]

    df = pd.read_csv(StringIO(csv_data))
    first_line = csv_data.splitlines()[0] if csv_data else "excel_data"
    filename = generate_timestamped_filename(sanitize_filename(first_line), "xlsx")
    file_path = os.path.join(TEMP_DIR, filename)
    df.to_excel(file_path, index=False)

    generated_docs[content_hash] = file_path
    return file_path

@mcp.tool(name="Generate_PPT", description="Generate a PowerPoint presentation from structured slide content")
async def generate_ppt(slides: List[Slide]) -> str:
    print(f"Structured slides received: {slides}")

    # Create a hash of the slide structure for caching
    joined_text = " ".join(" ".join(s.placeholders) for s in slides)
    content_hash = get_content_hash(joined_text)

    if content_hash in generated_docs:
        return generated_docs[content_hash]

    prs = Presentation(ppt_template_path)

    # Iterate over each slide layout
    for layout_idx, slide_layout in enumerate(prs.slide_layouts):
        print(f"Slide Layout {layout_idx}: {slide_layout.name}")
        for ph in slide_layout.placeholders:
            print(f"  Placeholder idx: {ph.placeholder_format.idx}, name: '{ph.name}'")
        print("-" * 40)

    # Combine placeholders into a structured format
    structured_slides = combine_placeholders(slides)
    print(f"Combined placeholders: {structured_slides}")

    for idx, slide_info in enumerate(slides):
        layout_idx = slide_info.layout
        placeholders = slide_info.placeholders

        try:
            slide_layout = prs.slide_layouts[layout_idx]
            slide = prs.slides.add_slide(slide_layout)

            for ph in slide.placeholders:
                try:
                    if ph.placeholder_format.idx == 0 and len(placeholders) > 0:
                        ph.text = placeholders[1]  # heading or title
                    elif ph.placeholder_format.idx == 10 and len(placeholders) > 1:
                        ph.text = placeholders[0]  # content
                except Exception as e:
                    print(f"Warning: Failed to set text in placeholder '{ph.name}' on slide {idx}: {e}")

        except Exception as e:
            print(f"Error adding slide {idx}: {e}")

    filename = generate_timestamped_filename(sanitize_filename(joined_text), "pptx")
    file_path = os.path.join(TEMP_DIR, filename)
    prs.save(file_path)

    generated_docs[content_hash] = file_path
    return file_path


@mcp.tool(name="Cleanup_Temp_Files", description="Delete all generated temporary document files")
async def cleanup_temp_files() -> str:
    deleted = 0
    for ext in ["docx", "pptx", "xlsx"]:
        pattern = os.path.join(TEMP_DIR, f"*.{ext}")
        for filepath in glob.glob(pattern):
            try:
                os.remove(filepath)
                deleted += 1
            except Exception:
                pass
    generated_docs.clear()
    return f"Deleted {deleted} temporary files."

# --- Server Start ---
if __name__ == "__main__":
    mcp.run(transport="sse")
