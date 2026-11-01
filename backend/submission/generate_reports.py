"""
Academic Report Generator for SchemaSense AI
Converts ACADEMIC_REPORT_DRAFT.md into:
1. Publication-grade Word Document (SchemaSense_AI_AAT1_Report.docx)
2. Professional PDF Preview (SchemaSense_AI_AAT1_Report_Preview.pdf)
"""

import os
import re
import sys
from pathlib import Path

# python-docx imports
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

# reportlab imports
import reportlab
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Preformatted,
    KeepTogether,
    PageBreak,
    HRFlowable,
    Image as RLImage,
)
from PIL import Image as PILImage
from reportlab.pdfgen import canvas


class NumberedCanvas(canvas.Canvas):
    """Two-pass canvas to dynamically compute and print total page count."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            super().showPage()
        super().save()

    def draw_page_number(self, page_count):
        if self._pageNumber > 1:
            self.saveState()
            self.setFont("Helvetica", 8)
            self.setFillColor(colors.HexColor("#64748B"))
            # Header
            self.drawString(
                54,
                750,
                "SchemaSense AI — Generative AI AAT-1 Academic Project Report",
            )
            self.setStrokeColor(colors.HexColor("#CBD5E1"))
            self.setLineWidth(0.5)
            self.line(54, 744, 558, 744)

            # Footer
            page_text = f"Page {self._pageNumber} of {page_count}"
            self.drawRightString(558, 36, page_text)
            self.drawString(
                54,
                36,
                "Confidential — Academic Assessment Task 1 (Coursework Submission)",
            )
            self.line(54, 46, 558, 46)
            self.restoreState()


def set_cell_background(cell, fill_hex):
    """Set background color of a Word table cell."""
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    tc_pr.append(shd)


def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    """Set cell margins/padding in dxa (1 pt = 20 dxa)."""
    tc_pr = cell._tc.get_or_add_tcPr()
    tc_mar = parse_xml(
        f'<w:tcMar {nsdecls("w")}>'
        f'<w:top w:w="{top}" w:type="dxa"/>'
        f'<w:bottom w:w="{bottom}" w:type="dxa"/>'
        f'<w:left w:w="{left}" w:type="dxa"/>'
        f'<w:right w:w="{right}" w:type="dxa"/>'
        f'</w:tcMar>'
    )
    tc_pr.append(tc_mar)


def add_page_number_to_section(section):
    """Add Page X of Y to Word document footer."""
    footer = section.footer
    p = footer.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    run = p.add_run("SchemaSense AI | Page ")
    run.font.name = "Calibri"
    run.font.size = Pt(9)
    run.font.color.rgb = RGBColor(100, 116, 139)

    fld_page = OxmlElement('w:fldSimple')
    fld_page.set(qn('w:instr'), 'PAGE')
    p._p.append(fld_page)

    run2 = p.add_run(" of ")
    run2.font.name = "Calibri"
    run2.font.size = Pt(9)
    run2.font.color.rgb = RGBColor(100, 116, 139)

    fld_numpages = OxmlElement('w:fldSimple')
    fld_numpages.set(qn('w:instr'), 'NUMPAGES')
    p._p.append(fld_numpages)


def parse_markdown_blocks(md_text):
    """Parses markdown text into structured semantic blocks."""
    lines = md_text.splitlines()
    blocks = []
    i = 0
    n = len(lines)

    while i < n:
        line = lines[i]

        # Fenced code block or diagram
        if line.startswith("```"):
            fence = line[:3]
            lang = line[3:].strip()
            code_lines = []
            i += 1
            while i < n and not lines[i].startswith("```"):
                code_lines.append(lines[i])
                i += 1
            if i < n:
                i += 1
            blocks.append({
                "type": "code",
                "lang": lang,
                "content": "\n".join(code_lines)
            })
            continue

        # Horizontal rule
        if re.match(r"^(\-{3,}|\*{3,}|_{3,})$", line.strip()):
            blocks.append({"type": "hr"})
            i += 1
            continue

        # Headings
        m_h = re.match(r"^(#{1,6})\s+(.*)$", line)
        if m_h:
            level = len(m_h.group(1))
            text = m_h.group(2).strip()
            blocks.append({"type": "heading", "level": level, "text": text})
            i += 1
            continue

        # Table block
        if "|" in line and line.strip().startswith("|") and line.strip().endswith("|"):
            table_lines = []
            while i < n and "|" in lines[i] and lines[i].strip().startswith("|"):
                table_lines.append(lines[i].strip())
                i += 1
            blocks.append({"type": "table", "lines": table_lines})
            continue

        # Blockquote
        if line.startswith(">"):
            quote_lines = []
            while i < n and lines[i].startswith(">"):
                quote_lines.append(re.sub(r"^>\s?", "", lines[i]))
                i += 1
            blocks.append({"type": "quote", "text": " ".join(quote_lines)})
            continue

        # List items (bullets or numbered)
        m_bullet = re.match(r"^(\s*)[-*+]\s+(.*)$", line)
        m_num = re.match(r"^(\s*)\d+\.\s+(.*)$", line)
        if m_bullet or m_num:
            list_type = "bullet" if m_bullet else "numbered"
            list_items = []
            while i < n:
                curr = lines[i]
                b_m = re.match(r"^(\s*)[-*+]\s+(.*)$", curr)
                n_m = re.match(r"^(\s*)\d+\.\s+(.*)$", curr)
                if b_m:
                    list_items.append({"type": "bullet", "text": b_m.group(2)})
                    i += 1
                elif n_m:
                    list_items.append({"type": "numbered", "text": n_m.group(2)})
                    i += 1
                elif curr.strip() == "":
                    # Peek next
                    if i + 1 < n and (re.match(r"^\s*[-*+]\s+", lines[i+1]) or re.match(r"^\s*\d+\.\s+", lines[i+1])):
                        i += 1
                        continue
                    else:
                        break
                else:
                    break
            blocks.append({"type": "list", "items": list_items})
            continue

        # Empty line
        if not line.strip():
            i += 1
            continue

        # Regular paragraph
        para_lines = [line]
        i += 1
        while i < n and lines[i].strip() and not lines[i].startswith(("#", "```", ">", "|", "---", "***")) and not re.match(r"^\s*[-*+]\s+", lines[i]) and not re.match(r"^\s*\d+\.\s+", lines[i]):
            para_lines.append(lines[i])
            i += 1
        blocks.append({"type": "paragraph", "text": " ".join(para_lines)})

    return blocks


def clean_markdown_inline(text):
    """Strips markdown inline syntax for clean text rendering."""
    t = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
    t = re.sub(r"\*(.*?)\*", r"\1", t)
    t = re.sub(r"`(.*?)`", r"\1", t)
    t = re.sub(r"\$(.*?)\$", r"\1", t)
    t = re.sub(r"\\text\{(.*?)\}", r"\1", t)
    t = re.sub(r"\\to", "->", t)
    t = re.sub(r"\\approx", "~", t)
    t = re.sub(r"\\sim", "~", t)
    t = re.sub(r"&emsp;", "    ", t)
    return t


def add_formatted_runs_docx(paragraph, text, base_font="Calibri", base_size=11, color_rgb=(15, 23, 42)):
    """Applies inline formatting (bold, italic, code) to a Word paragraph."""
    # Pattern to match **bold**, *italic*, and `code`
    tokens = re.split(r"(\*\*.*?\*\*|\*.*?\*|`.*?`|\$.*?\$)", text)
    for tok in tokens:
        if not tok:
            continue
        if tok.startswith("**") and tok.endswith("**"):
            r = paragraph.add_run(clean_markdown_inline(tok[2:-2]))
            r.bold = True
            r.font.name = base_font
            r.font.size = Pt(base_size)
            r.font.color.rgb = RGBColor(*color_rgb)
        elif tok.startswith("*") and tok.endswith("*") and len(tok) > 1:
            r = paragraph.add_run(clean_markdown_inline(tok[1:-1]))
            r.italic = True
            r.font.name = base_font
            r.font.size = Pt(base_size)
            r.font.color.rgb = RGBColor(*color_rgb)
        elif tok.startswith("`") and tok.endswith("`"):
            r = paragraph.add_run(clean_markdown_inline(tok[1:-1]))
            r.font.name = "Consolas"
            r.font.size = Pt(base_size - 1)
            r.font.color.rgb = RGBColor(15, 23, 42)
            # Add light shading to inline code
            r_pr = r._r.get_or_add_rPr()
            shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="F1F5F9"/>')
            r_pr.append(shd)
        elif tok.startswith("$") and tok.endswith("$"):
            r = paragraph.add_run(clean_markdown_inline(tok[1:-1]))
            r.italic = True
            r.font.name = "Cambria Math" if base_font != "Consolas" else base_font
            r.font.size = Pt(base_size)
            r.font.color.rgb = RGBColor(*color_rgb)
        else:
            r = paragraph.add_run(clean_markdown_inline(tok))
            r.font.name = base_font
            r.font.size = Pt(base_size)
            r.font.color.rgb = RGBColor(*color_rgb)


FIGURE_MAP = {
    1: ["fig01_schema_explorer.png", "fig01_schema_explorer.jpg", "fig01_schema_explorer.jpeg"],
    2: ["fig02_test_verification.png", "fig02_test_verification.jpg", "fig02_test_verification.jpeg"],
    3: [
        "fig03_real_generation.png",
        "fig03_real_generation.jpg",
        "fig03_real_generation.jpeg",
        "fig03_generated_sql.png",
        "fig03_generated_sql.jpg",
        "fig03_generated_sql.jpeg",
    ],
    4: ["fig04_correction_trace.png", "fig04_correction_trace.jpg", "fig04_correction_trace.jpeg"],
    5: ["fig05_semantic_warning.png", "fig05_semantic_warning.jpg", "fig05_semantic_warning.jpeg"],
    6: ["fig06_colab_runtime.png", "fig06_colab_runtime.jpg", "fig06_colab_runtime.jpeg"],
    7: ["fig07_colab_results.png", "fig07_colab_results.jpg", "fig07_colab_results.jpeg", "schemasense_evaluation_metrics.png"],
    8: ["fig08_history_insights.png", "fig08_history_insights.jpg", "fig08_history_insights.jpeg"],
}


def find_figure_file(text: str, figures_dir: Path | None) -> Path | None:
    """Finds an existing screenshot or chart file for a figure placeholder."""
    if not figures_dir or not figures_dir.exists():
        return None
    m = re.search(r"FIGURE\s*(\d+)", text, re.IGNORECASE)
    if not m:
        return None
    fig_num = int(m.group(1))
    candidates = FIGURE_MAP.get(fig_num, [])
    for fname in candidates:
        cand_path = figures_dir / fname
        if cand_path.exists() and cand_path.stat().st_size > 0:
            return cand_path
        # Also check docs directory for schemasense_evaluation_metrics.png
        if fname == "schemasense_evaluation_metrics.png":
            doc_path = figures_dir.parent.parent / "docs" / fname
            if doc_path.exists() and doc_path.stat().st_size > 0:
                return doc_path
    return None


def build_docx_report(blocks, output_path, figures_dir: Path | None = None):
    """Generates the professional Word DOCX report."""
    doc = docx.Document()

    # Set page margins to 1 inch
    for sec in doc.sections:
        sec.top_margin = Inches(1.0)
        sec.bottom_margin = Inches(1.0)
        sec.left_margin = Inches(1.0)
        sec.right_margin = Inches(1.0)
        add_page_number_to_section(sec)

    # Document Header Title
    title_p = doc.add_paragraph()
    title_p.paragraph_format.space_before = Pt(24)
    title_p.paragraph_format.space_after = Pt(8)
    title_run = title_p.add_run("SchemaSense AI: Schema-Aware Natural Language to SQL Query Generation with Automatic Self-Correction")
    title_run.font.name = "Calibri"
    title_run.font.size = Pt(22)
    title_run.bold = True
    title_run.font.color.rgb = RGBColor(15, 23, 42)

    # Subtitle
    sub_p = doc.add_paragraph()
    sub_p.paragraph_format.space_after = Pt(16)
    sub_run = sub_p.add_run("Academic Assessment Task 1 (AAT-1) Final Project Report\nGenerative Artificial Intelligence — B.Tech Computer Science & Engineering (Semester VII)")
    sub_run.font.name = "Calibri"
    sub_run.font.size = Pt(13)
    sub_run.italic = True
    sub_run.font.color.rgb = RGBColor(71, 85, 105)

    doc.add_paragraph().paragraph_format.space_after = Pt(12)

    in_appendix = False

    for b in blocks:
        b_type = b["type"]

        if b_type == "hr":
            # Add subtle divider line
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(8)
            p.paragraph_format.space_after = Pt(12)
            p_border = parse_xml(f'<w:pBdr {nsdecls("w")}><w:bottom w:val="single" w:sz="6" w:space="1" w:color="CBD5E1"/></w:pBdr>')
            p._p.get_or_add_pPr().append(p_border)
            continue

        elif b_type == "heading":
            level = b["level"]
            text = clean_markdown_inline(b["text"])

            if "Appendix" in text or "Figure" in text:
                in_appendix = True

            p = doc.add_paragraph()
            p.paragraph_format.keep_with_next = True
            run = p.add_run(text)
            run.font.name = "Calibri"
            run.bold = True

            if level == 1:
                p.paragraph_format.space_before = Pt(20)
                p.paragraph_format.space_after = Pt(8)
                run.font.size = Pt(18)
                run.font.color.rgb = RGBColor(15, 23, 42)
            elif level == 2:
                p.paragraph_format.space_before = Pt(16)
                p.paragraph_format.space_after = Pt(6)
                run.font.size = Pt(14)
                run.font.color.rgb = RGBColor(30, 41, 59)
            elif level == 3:
                p.paragraph_format.space_before = Pt(12)
                p.paragraph_format.space_after = Pt(4)
                run.font.size = Pt(12)
                run.font.color.rgb = RGBColor(51, 65, 85)
            else:
                p.paragraph_format.space_before = Pt(8)
                p.paragraph_format.space_after = Pt(2)
                run.font.size = Pt(11)
                run.font.color.rgb = RGBColor(71, 85, 105)

        elif b_type == "paragraph":
            text = b["text"]
            # Check for figure placeholder
            if "FIGURE" in text and ("Placeholder" in text or "Figure" in text):
                fig_file = find_figure_file(text, figures_dir)
                if fig_file:
                    try:
                        p_img = doc.add_paragraph()
                        p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
                        p_img.paragraph_format.space_before = Pt(8)
                        p_img.paragraph_format.space_after = Pt(2)
                        p_img.paragraph_format.keep_with_next = True
                        r_img = p_img.add_run()
                        r_img.add_picture(str(fig_file), width=Inches(5.8))

                        p_cap = doc.add_paragraph()
                        p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
                        p_cap.paragraph_format.space_before = Pt(2)
                        p_cap.paragraph_format.space_after = Pt(12)
                        r_cap = p_cap.add_run(clean_markdown_inline(text))
                        r_cap.font.name = "Calibri"
                        r_cap.font.size = Pt(9.5)
                        r_cap.italic = True
                        r_cap.font.color.rgb = RGBColor(71, 85, 105)
                    except Exception as e:
                        print(f"Warning: could not embed DOCX picture {fig_file}: {e}")
                        fig_table = doc.add_table(rows=1, cols=1)
                        fig_table.alignment = WD_TABLE_ALIGNMENT.CENTER
                        cell = fig_table.cell(0, 0)
                        set_cell_background(cell, "F8FAFC")
                        set_cell_margins(cell, top=160, bottom=160, left=200, right=200)
                        p = cell.paragraphs[0]
                        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                        add_formatted_runs_docx(p, text, base_font="Calibri", base_size=10.5, color_rgb=(71, 85, 105))
                        doc.add_paragraph().paragraph_format.space_after = Pt(8)
                else:
                    fig_table = doc.add_table(rows=1, cols=1)
                    fig_table.alignment = WD_TABLE_ALIGNMENT.CENTER
                    cell = fig_table.cell(0, 0)
                    set_cell_background(cell, "F8FAFC")
                    set_cell_margins(cell, top=160, bottom=160, left=200, right=200)

                    p = cell.paragraphs[0]
                    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    add_formatted_runs_docx(p, text, base_font="Calibri", base_size=10.5, color_rgb=(71, 85, 105))

                    doc.add_paragraph().paragraph_format.space_after = Pt(8)
            else:
                p = doc.add_paragraph()
                p.paragraph_format.space_before = Pt(0)
                p.paragraph_format.space_after = Pt(6)
                p.paragraph_format.line_spacing = 1.15
                add_formatted_runs_docx(p, text, base_font="Calibri", base_size=11, color_rgb=(15, 23, 42))

        elif b_type == "quote":
            quote_table = doc.add_table(rows=1, cols=1)
            quote_table.alignment = WD_TABLE_ALIGNMENT.CENTER
            cell = quote_table.cell(0, 0)
            set_cell_background(cell, "F1F5F9")
            set_cell_margins(cell, top=140, bottom=140, left=200, right=160)
            # Add thick left border
            tc_pr = cell._tc.get_or_add_tcPr()
            tc_bdr = parse_xml(
                f'<w:tcBorders {nsdecls("w")}>'
                f'<w:left w:val="single" w:sz="24" w:space="0" w:color="3B82F6"/>'
                f'<w:top w:val="none"/>'
                f'<w:bottom w:val="none"/>'
                f'<w:right w:val="none"/>'
                f'</w:tcBorders>'
            )
            tc_pr.append(tc_bdr)

            p = cell.paragraphs[0]
            p.paragraph_format.space_after = Pt(0)
            p.paragraph_format.line_spacing = 1.15
            add_formatted_runs_docx(p, b["text"], base_font="Calibri", base_size=10.5, color_rgb=(30, 41, 59))
            doc.add_paragraph().paragraph_format.space_after = Pt(6)

        elif b_type == "list":
            for item in b["items"]:
                p = doc.add_paragraph(style="List Bullet" if item["type"] == "bullet" else "List Number")
                p.paragraph_format.space_before = Pt(0)
                p.paragraph_format.space_after = Pt(3)
                p.paragraph_format.line_spacing = 1.15
                add_formatted_runs_docx(p, item["text"], base_font="Calibri", base_size=11, color_rgb=(15, 23, 42))

        elif b_type == "code":
            lang = b["lang"]
            content = b["content"]

            # Check if this code block is a figure placeholder with an available image
            if "INSERT FIGURE" in content:
                fig_file = find_figure_file(content, figures_dir)
                if fig_file:
                    try:
                        p_img = doc.add_paragraph()
                        p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
                        p_img.paragraph_format.space_before = Pt(8)
                        p_img.paragraph_format.space_after = Pt(2)
                        p_img.paragraph_format.keep_with_next = True
                        r_img = p_img.add_run()
                        r_img.add_picture(str(fig_file), width=Inches(5.8))
                        continue
                    except Exception as e:
                        print(f"Warning: could not embed DOCX picture {fig_file}: {e}")

            # Display inside single-cell shaded box
            code_table = doc.add_table(rows=1, cols=1)
            code_table.alignment = WD_TABLE_ALIGNMENT.CENTER
            cell = code_table.cell(0, 0)
            set_cell_background(cell, "0F172A" if lang in ("bash", "sh") else "F8FAFC")
            set_cell_margins(cell, top=140, bottom=140, left=180, right=180)

            # Border
            tc_pr = cell._tc.get_or_add_tcPr()
            bdr_color = "334155" if lang in ("bash", "sh") else "CBD5E1"
            tc_bdr = parse_xml(
                f'<w:tcBorders {nsdecls("w")}>'
                f'<w:left w:val="single" w:sz="6" w:space="0" w:color="{bdr_color}"/>'
                f'<w:top w:val="single" w:sz="6" w:space="0" w:color="{bdr_color}"/>'
                f'<w:bottom w:val="single" w:sz="6" w:space="0" w:color="{bdr_color}"/>'
                f'<w:right w:val="single" w:sz="6" w:space="0" w:color="{bdr_color}"/>'
                f'</w:tcBorders>'
            )
            tc_pr.append(tc_bdr)

            p = cell.paragraphs[0]
            p.paragraph_format.space_after = Pt(0)
            p.paragraph_format.line_spacing = 1.05
            font_color = (248, 250, 252) if lang in ("bash", "sh") else (15, 23, 42)
            run = p.add_run(content)
            run.font.name = "Consolas"
            run.font.size = Pt(9.0)
            run.font.color.rgb = RGBColor(*font_color)

            doc.add_paragraph().paragraph_format.space_after = Pt(6)

        elif b_type == "table":
            table_lines = b["lines"]
            rows = []
            for t_line in table_lines:
                # skip separator line
                if re.match(r"^\|\s*:?---", t_line):
                    continue
                cells = [c.strip() for c in t_line.split("|")[1:-1]]
                if cells:
                    rows.append(cells)

            if rows:
                num_cols = len(rows[0])
                t = doc.add_table(rows=len(rows), cols=num_cols)
                t.alignment = WD_TABLE_ALIGNMENT.CENTER

                for row_idx, r_data in enumerate(rows):
                    is_header = (row_idx == 0)
                    for col_idx, cell_txt in enumerate(r_data[:num_cols]):
                        c = t.cell(row_idx, col_idx)
                        set_cell_background(c, "1E293B" if is_header else ("F8FAFC" if row_idx % 2 == 1 else "FFFFFF"))
                        set_cell_margins(c, top=100, bottom=100, left=140, right=140)

                        # Light borders
                        tc_pr = c._tc.get_or_add_tcPr()
                        tc_bdr = parse_xml(
                            f'<w:tcBorders {nsdecls("w")}>'
                            f'<w:left w:val="single" w:sz="4" w:space="0" w:color="E2E8F0"/>'
                            f'<w:top w:val="single" w:sz="4" w:space="0" w:color="E2E8F0"/>'
                            f'<w:bottom w:val="single" w:sz="4" w:space="0" w:color="CBD5E1"/>'
                            f'<w:right w:val="single" w:sz="4" w:space="0" w:color="E2E8F0"/>'
                            f'</w:tcBorders>'
                        )
                        tc_pr.append(tc_bdr)

                        p = c.paragraphs[0]
                        p.paragraph_format.space_after = Pt(0)
                        p.paragraph_format.line_spacing = 1.05
                        txt_color = (255, 255, 255) if is_header else (15, 23, 42)
                        add_formatted_runs_docx(p, cell_txt, base_font="Calibri", base_size=9.5 if not is_header else 10.0, color_rgb=txt_color)
                        if is_header:
                            for r in p.runs:
                                r.bold = True

                doc.add_paragraph().paragraph_format.space_after = Pt(8)

    if output_path.exists():
        backup_path = output_path.with_suffix(".docx.bak")
        try:
            import shutil
            shutil.copy2(output_path, backup_path)
        except Exception:
            pass

    try:
        doc.save(str(output_path))
        print(f"DOCX Report created successfully at: {output_path}")
    except PermissionError:
        print(f"ERROR: Permission denied saving '{output_path}'. If open in Microsoft Word, please close it and re-run.", file=sys.stderr)
        raise


def to_reportlab_html(text):
    """Converts markdown text to valid, strictly well-formed XML for ReportLab."""
    if not text:
        return ""
    # Normalize br tags
    text = text.replace("<br>", "__BR__").replace("<br/>", "__BR__")
    # Split on markdown formatting tokens
    tokens = re.split(r"(\*\*.*?\*\*|\*.*?\*|`.*?`|\$.*?\$|__BR__)", text)
    parts = []
    for tok in tokens:
        if not tok:
            continue
        if tok == "__BR__":
            parts.append("<br/>")
        elif tok.startswith("**") and tok.endswith("**"):
            inner = tok[2:-2].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            parts.append(f"<b>{inner}</b>")
        elif tok.startswith("*") and tok.endswith("*") and len(tok) > 1:
            inner = tok[1:-1].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            parts.append(f"<i>{inner}</i>")
        elif tok.startswith("`") and tok.endswith("`"):
            inner = tok[1:-1].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            parts.append(f'<font name="Courier">{inner}</font>')
        elif tok.startswith("$") and tok.endswith("$"):
            inner = tok[1:-1].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            inner = inner.replace(r"\to", "->").replace(r"\approx", "~").replace(r"\sim", "~")
            parts.append(f"<i>{inner}</i>")
        else:
            cleaned = tok.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            cleaned = cleaned.replace(r"\to", "->").replace(r"\approx", "~").replace(r"\sim", "~")
            cleaned = cleaned.replace("&amp;emsp;", "    ")
            parts.append(cleaned)
    return "".join(parts)


def build_pdf_report(blocks, output_path, figures_dir=None):
    """Generates the professional PDF preview report using ReportLab."""
    pdf = SimpleDocTemplate(
        str(output_path),
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54,
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        "CoverTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#0F172A"),
        spaceAfter=10,
    )
    subtitle_style = ParagraphStyle(
        "CoverSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#475569"),
        spaceAfter=18,
    )
    h1_style = ParagraphStyle(
        "CustomH1",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=14,
        leading=18,
        textColor=colors.HexColor("#0F172A"),
        spaceBefore=14,
        spaceAfter=6,
        keepWithNext=True,
    )
    h2_style = ParagraphStyle(
        "CustomH2",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=15,
        textColor=colors.HexColor("#1E293B"),
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True,
    )
    h3_style = ParagraphStyle(
        "CustomH3",
        parent=styles["Heading3"],
        fontName="Helvetica-Bold",
        fontSize=10.5,
        leading=13,
        textColor=colors.HexColor("#334155"),
        spaceBefore=8,
        spaceAfter=3,
        keepWithNext=True,
    )
    body_style = ParagraphStyle(
        "CustomBody",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9.5,
        leading=13,
        textColor=colors.HexColor("#0F172A"),
        spaceAfter=5,
    )
    bullet_style = ParagraphStyle(
        "CustomBullet",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9.5,
        leading=13,
        textColor=colors.HexColor("#0F172A"),
        leftIndent=15,
        spaceAfter=3,
    )
    quote_style = ParagraphStyle(
        "CustomQuote",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=9.5,
        leading=13.5,
        textColor=colors.HexColor("#1E293B"),
    )
    code_style = ParagraphStyle(
        "CustomCode",
        parent=styles["Normal"],
        fontName="Courier",
        fontSize=7.5,
        leading=9.5,
        textColor=colors.HexColor("#0F172A"),
    )
    table_cell_style = ParagraphStyle(
        "TableCell",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#0F172A"),
    )
    table_header_style = ParagraphStyle(
        "TableHeader",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8.5,
        leading=11,
        textColor=colors.white,
    )
    fig_style = ParagraphStyle(
        "FigurePlaceholder",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#3B82F6"),
        alignment=1, # Centered
    )

    story = []

    # Title & Subtitle
    story.append(Paragraph("SchemaSense AI: Schema-Aware Natural Language to SQL Query Generation with Automatic Self-Correction", title_style))
    story.append(Paragraph("Academic Assessment Task 1 (AAT-1) Project Report — Generative Artificial Intelligence (B.Tech CSE)", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#CBD5E1"), spaceAfter=14))

    for b in blocks:
        b_type = b["type"]

        if b_type == "hr":
            story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#E2E8F0"), spaceBefore=6, spaceAfter=8))

        elif b_type == "heading":
            level = b["level"]
            text = to_reportlab_html(b["text"])
            if level == 1:
                story.append(Paragraph(text, h1_style))
            elif level == 2:
                story.append(Paragraph(text, h2_style))
            else:
                story.append(Paragraph(text, h3_style))

        elif b_type == "paragraph":
            text = b["text"]
            formatted_text = to_reportlab_html(text)

            if "FIGURE" in text and ("Placeholder" in text or "Figure" in text):
                fig_file = find_figure_file(text, figures_dir)
                if fig_file:
                    try:
                        with PILImage.open(fig_file) as img:
                            orig_w, orig_h = img.size
                        # Max dimensions in PDF points (width: 480 pt, max height: 240 pt)
                        max_w = 480.0
                        max_h = 240.0
                        ratio = min(max_w / orig_w, max_h / orig_h)
                        target_w = orig_w * ratio
                        target_h = orig_h * ratio
                        rl_img = RLImage(str(fig_file), width=target_w, height=target_h)
                        story.append(Spacer(1, 4))
                        story.append(rl_img)
                        caption_p = Paragraph(f"<b>{formatted_text}</b>", fig_style)
                        story.append(caption_p)
                        story.append(Spacer(1, 6))
                    except Exception as img_err:
                        print(f"Warning: could not load PDF image {fig_file}: {img_err}")
                        fig_content = Paragraph(f"<b>[ FIGURE PLACEHOLDER ]</b><br/>{formatted_text}", fig_style)
                        fig_t = Table([[fig_content]], colWidths=[490])
                        fig_t.setStyle(TableStyle([
                            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
                            ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#93C5FD")),
                            ("TOPPADDING", (0, 0), (-1, -1), 10),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
                            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                        ]))
                        story.append(Spacer(1, 4))
                        story.append(fig_t)
                        story.append(Spacer(1, 6))
                else:
                    fig_content = Paragraph(f"<b>[ FIGURE PLACEHOLDER ]</b><br/>{formatted_text}", fig_style)
                    fig_t = Table([[fig_content]], colWidths=[490])
                    fig_t.setStyle(TableStyle([
                        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
                        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#93C5FD")),
                        ("TOPPADDING", (0, 0), (-1, -1), 10),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
                        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ]))
                    story.append(Spacer(1, 4))
                    story.append(fig_t)
                    story.append(Spacer(1, 6))
            else:
                story.append(Paragraph(formatted_text, body_style))

        elif b_type == "quote":
            q_text = to_reportlab_html(b["text"])
            q_p = Paragraph(q_text, quote_style)
            q_table = Table([[q_p]], colWidths=[490])
            q_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F1F5F9")),
                ("LINEBEFORE", (0, 0), (-1, -1), 3, colors.HexColor("#3B82F6")),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ]))
            story.append(Spacer(1, 4))
            story.append(q_table)
            story.append(Spacer(1, 6))

        elif b_type == "list":
            for item in b["items"]:
                prefix = "&bull; " if item["type"] == "bullet" else ""
                it_text = to_reportlab_html(item["text"])
                story.append(Paragraph(f"{prefix}{it_text}", bullet_style))

        elif b_type == "code":
            content = b["content"]
            lang = b["lang"]

            # Check if this code block is a figure placeholder with an available image
            if "INSERT FIGURE" in content:
                fig_file = find_figure_file(content, figures_dir)
                if fig_file:
                    try:
                        with PILImage.open(fig_file) as img:
                            orig_w, orig_h = img.size
                        max_w = 480.0
                        max_h = 240.0
                        ratio = min(max_w / orig_w, max_h / orig_h)
                        target_w = orig_w * ratio
                        target_h = orig_h * ratio
                        rl_img = RLImage(str(fig_file), width=target_w, height=target_h)
                        story.append(Spacer(1, 4))
                        story.append(rl_img)
                        story.append(Spacer(1, 4))
                        continue
                    except Exception as img_err:
                        print(f"Warning: could not load PDF image {fig_file}: {img_err}")

            safe_content = content.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            bg_color = colors.HexColor("#0F172A") if lang in ("bash", "sh") else colors.HexColor("#F8FAFC")
            border_color = colors.HexColor("#334155") if lang in ("bash", "sh") else colors.HexColor("#CBD5E1")

            code_lines = safe_content.splitlines()
            chunk_size = 25
            for ch_start in range(0, max(len(code_lines), 1), chunk_size):
                chunk = "\n".join(code_lines[ch_start:ch_start + chunk_size])
                p_chunk = Preformatted(chunk, code_style)
                code_table = Table([[p_chunk]], colWidths=[490])
                code_table.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, -1), bg_color),
                    ("BOX", (0, 0), (-1, -1), 0.5, border_color),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ]))
                story.append(Spacer(1, 2))
                story.append(code_table)
            story.append(Spacer(1, 5))

        elif b_type == "table":
            table_lines = b["lines"]
            rows = []
            for t_line in table_lines:
                if re.match(r"^\|\s*:?---", t_line):
                    continue
                cells = [c.strip() for c in t_line.split("|")[1:-1]]
                if cells:
                    rows.append(cells)

            if rows:
                num_cols = len(rows[0])
                col_width = 490.0 / num_cols
                table_data = []

                for r_idx, r in enumerate(rows):
                    row_data = []
                    is_head = (r_idx == 0)
                    for c_txt in r[:num_cols]:
                        clean_c = to_reportlab_html(c_txt)
                        c_p = Paragraph(f"<b>{clean_c}</b>" if is_head else clean_c, table_header_style if is_head else table_cell_style)
                        row_data.append(c_p)
                    table_data.append(row_data)

                pdf_table = Table(table_data, colWidths=[col_width] * num_cols)
                t_style = [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E293B")),
                    ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                    ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ("LEFTPADDING", (0, 0), (-1, -1), 5),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ]
                for r_i in range(1, len(rows)):
                    if r_i % 2 == 1:
                        t_style.append(("BACKGROUND", (0, r_i), (-1, r_i), colors.HexColor("#F8FAFC")))
                pdf_table.setStyle(TableStyle(t_style))
                story.append(Spacer(1, 3))
                story.append(pdf_table)
                story.append(Spacer(1, 6))

    if output_path.exists():
        backup_path = output_path.with_suffix(".pdf.bak")
        try:
            import shutil
            shutil.copy2(output_path, backup_path)
        except Exception:
            pass

    try:
        pdf.build(story, canvasmaker=NumberedCanvas)
        print(f"PDF Report created successfully at: {output_path}")
    except PermissionError:
        print(f"ERROR: Permission denied saving '{output_path}'. If open in a PDF viewer, please close it and re-run.", file=sys.stderr)
        raise


def count_pdf_pages(pdf_path):
    """Counts actual pages in the generated PDF file."""
    with open(pdf_path, "rb") as f:
        content = f.read()
    # Count /Type /Page occurrences (standard PDF marker)
    pages = len(re.findall(rb"/Type\s*/Page\b", content)) - len(re.findall(rb"/Type\s*/Pages\b", content))
    return max(pages, 1)


def main():
    root = Path(__file__).resolve().parent.parent.parent
    sub_dir = root / "backend" / "submission"
    md_path = sub_dir / "ACADEMIC_REPORT_DRAFT.md"
    docx_path = sub_dir / "SchemaSense_AI_AAT1_Report.docx"
    pdf_path = sub_dir / "SchemaSense_AI_AAT1_Report_Preview.pdf"

    if not md_path.exists():
        print(f"Error: {md_path} does not exist!")
        sys.exit(1)

    print(f"Reading markdown source from: {md_path}")
    with open(md_path, "r", encoding="utf-8") as f:
        md_text = f.read()

    blocks = parse_markdown_blocks(md_text)
    print(f"Parsed {len(blocks)} markdown blocks.")

    figures_dir = sub_dir / "figures"

    # 1. Generate DOCX
    build_docx_report(blocks, docx_path, figures_dir=figures_dir)

    # 2. Generate PDF
    build_pdf_report(blocks, pdf_path, figures_dir=figures_dir)

    # 3. Check page count
    pages = count_pdf_pages(pdf_path)
    print(f"\n==================================================")
    print(f"REPORT GENERATION REPORT:")
    print(f"- DOCX Deliverable: {docx_path} ({docx_path.stat().st_size:,} bytes)")
    print(f"- PDF Deliverable:  {pdf_path} ({pdf_path.stat().st_size:,} bytes)")
    print(f"- Verified Rendered Page Count: {pages} pages")
    print(f"- Academic Page Requirement: >= 10 pages -> {'PASSED' if pages >= 10 else 'FAILED'}")
    print(f"==================================================\n")


if __name__ == "__main__":
    main()
