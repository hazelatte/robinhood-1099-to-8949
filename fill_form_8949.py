import copy
from PyPDF2 import PdfReader, PdfWriter
from PyPDF2.generic import NameObject, TextStringObject
import pandas as pd

# Configuration constants
NUM_FIELDS = 112  # Expected number of fields from f?_3[0] to f?_114[0]
ROWS_PER_PAGE = 14  # CSV rows per PDF page
TEMPLATE_PDF_PATH = "f8949.pdf"


def rename_fields(page, suffix):
    """
    Append a unique suffix to each form field name on the page.
    For example, "f1_3[0]" becomes "f1_3[0]_STC_1" if suffix is "STC_1".
    """
    if "/Annots" in page:
        for annot_ref in page["/Annots"]:
            annot = annot_ref.get_object()
            if "/T" in annot:
                original_name = annot["/T"]
                new_name = f"{original_name}_{suffix}"
                annot.update({NameObject("/T"): TextStringObject(new_name)})


def fill_form_with_trades(csv_path, output_pdf_path, doc_id, name, ssn):
    """
    Fill the PDF template with CSV data and update form fields.

    Additional features:
      - For short-term forms (doc_id starts with "ST"), use the first page of the template
        with field names starting with "f1_" and coverage fields "c1_".
      - For long-term forms (doc_id starts with "LT"), use the second page of the template
        with field names starting with "f2_" and coverage fields "c2_".
      - On the first page, mark the appropriate coverage field:
          * For covered forms (doc_id ends with "C"), mark field <c?_1[0]> with "/1".
          * For uncovered forms, mark field <c?_1[1]> with "/2".
      - On the last page, fill the proceeds sum (from the "Proceeds" CSV column)
        into field <f?_{115}[0]> (using the appropriate prefix).

    Note: The code removes any commas in CSV numbers so that '.' is used as the decimal point.
    """
    # Load CSV data; Pandas uses the first row as header.
    df = pd.read_csv(csv_path)

    # Convert columns to numeric, ignoring commas and treating non-numeric values (like spaces) as 0.
    for col in ["Proceeds", "Cost Basis", "Amount of Adjustment", "Gain/Loss"]:
        df[col] = pd.to_numeric(
            df[col].astype(str).str.replace(",", "", regex=False),
            errors="coerce"
        ).fillna(0)

    proceeds_sum = df["Proceeds"].sum()
    cost_sum = df["Cost Basis"].sum()
    adjustment_sum = df["Amount of Adjustment"].sum()
    gain_sum = df["Gain/Loss"].sum()

    # Flatten the rest of the CSV data (excluding the header row) to fill the form fields.
    flat_data = df.values.flatten()

    # Decide which template page and field prefixes to use.
    if doc_id.startswith("LT"):
        # Use the second page of the template for long-term data.
        sample_page_index = 1
        field_prefix = "f2_"
        coverage_prefix = "c2_"
    else:
        # Use the first page for short-term data.
        sample_page_index = 0
        field_prefix = "f1_"
        coverage_prefix = "c1_"

    # Create the list of form field names based on the chosen prefix.
    # For example, for short-term: f1_3[0], f1_4[0], ..., f1_114[0]
    form_fields = [f"{field_prefix}{i}[0]" for i in range(3, 115)]

    # Determine the number of extra pages required.
    extra_pages = df.shape[0] // ROWS_PER_PAGE

    # Load the PDF template and get the sample page.
    reader = PdfReader(TEMPLATE_PDF_PATH)
    sample_page = reader.pages[sample_page_index]
    writer = PdfWriter()

    # Add the sample page and duplicate it as needed.
    writer.add_page(sample_page)
    for _ in range(extra_pages):
        writer.add_page(copy.deepcopy(sample_page))
    num_pages = len(writer.pages)

    # Process each page.
    for i, page in enumerate(writer.pages):
        suffix = f"{doc_id}_{i + 1}"  # e.g., "STC_1", "STC_2", "LTC_1", etc.
        rename_fields(page, suffix)

        # Determine the slice of CSV data for this page.
        start = NUM_FIELDS * i
        end = NUM_FIELDS * (i + 1)
        page_data = flat_data[start:end]

        # Build a dictionary mapping renamed field names to CSV values.
        field_values = {
            f"{form_fields[j]}_{suffix}": str(page_data[j])
            for j in range(len(page_data))
        }

        # Mark the appropriate coverage field.
        if doc_id.endswith("C"):
            field_values[f"{coverage_prefix}1[0]_{suffix}"] = "/1"
        else:
            field_values[f"{coverage_prefix}1[1]_{suffix}"] = "/2"

        field_values[f"{field_prefix}1[0]_{suffix}"] = name
        field_values[f"{field_prefix}2[0]_{suffix}"] = ssn


        # On the last page, set the sums into the appropriate fields.
        if i == num_pages - 1:
            field_values[f"{field_prefix}115[0]_{suffix}"] = f"{proceeds_sum:.2f}"
            field_values[f"{field_prefix}116[0]_{suffix}"] = f"{cost_sum:.2f}"
            field_values[f"{field_prefix}118[0]_{suffix}"] = f"{adjustment_sum:.2f}"
            field_values[f"{field_prefix}119[0]_{suffix}"] = f"{gain_sum:.2f}"

        writer.update_page_form_field_values(page, field_values)

    # Write the filled PDF.
    with open(output_pdf_path, "wb") as out_pdf:
        writer.write(out_pdf)
    print(f"Filled PDF saved as: {output_pdf_path}")


def merge_pdfs(pdf_paths, output_pdf_path):
    """
    Merge multiple PDFs (specified in pdf_paths) into a single PDF.
    """
    writer = PdfWriter()
    for path in pdf_paths:
        reader = PdfReader(path)
        for page in reader.pages:
            writer.add_page(page)
    with open(output_pdf_path, "wb") as out_pdf:
        writer.write(out_pdf)
    print(f"Combined PDF saved as: {output_pdf_path}")


def fill_form(name, ssn):
    """
    Generate four PDFs for the provided CSV files (with different document IDs)
    and then merge them into one combined PDF.

    The document IDs encode whether the form is 'covered' (ends with C) or
    'uncovered' (ends with U) and whether it's short-term (ST) or long-term (LT).
    """
    pdf_configs = [
        ("short_term_covered.csv", "short_term_covered.pdf", "STC"),
        ("short_term_uncovered.csv", "short_term_uncovered.pdf", "STU"),
        ("long_term_covered.csv", "long_term_covered.pdf", "LTC"),
        ("long_term_uncovered.csv", "long_term_uncovered.pdf", "LTU")
    ]
    pdf_files = []
    for csv_path, output_pdf, doc_id in pdf_configs:
        fill_form_with_trades(csv_path, output_pdf, doc_id, name, ssn)
        pdf_files.append(output_pdf)

    # Merge the generated PDFs into one combined PDF.
    merge_pdfs(pdf_files, "f8949_filled.pdf")
