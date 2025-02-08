import pdfplumber
import csv
from dateutil.parser import parse
import re


def is_text(value):
    try:
        parse(value, fuzzy=False)  # Try parsing as a date.
        return False  # It's a date.
    except ValueError:
        return True   # It's text.


def clean_description(text):
    return re.sub(r'/ Symbol:|.000', '', text, flags=re.IGNORECASE).strip()


def process_trade_line(line, current_symbol):
    """
    Processes a line from a trade section and returns a tuple:
    (trade_record or None, updated_current_symbol).

    - If the line is a symbol line, it updates the current symbol and returns (None, new_symbol).
    - Otherwise, it extracts the trade record and returns (record, current_symbol).
    """
    parts = line.split()
    if len(parts) <= 5:
        return None, current_symbol

    # If the first token is text (e.g., a symbol line), update the current symbol.
    if is_text(parts[0]):
        return None, line

    try:
        date_disposed = parts[0]
        quantity = parts[1]
        proceeds = parts[2]
        date_acquired = parts[3]
        cost_basis = parts[4]

        if parts[5] == "...":
            amount_of_adjustment, code, gain_loss = " ", " ", parts[6]
        else:
            amount_of_adjustment, code, gain_loss = parts[5], parts[6], parts[7]

        description_of_property = clean_description(f"{quantity} sh. {current_symbol}")
        record = [
            description_of_property,
            date_acquired,
            date_disposed,
            proceeds,
            cost_basis,
            code,
            amount_of_adjustment,
            gain_loss
        ]
        return record, current_symbol
    except IndexError:
        # If expected parts are missing, skip this line.
        return None, current_symbol


def extract_trades_from_section(lines, section_header, detection_keywords, all_section_headers):
    """
    Processes lines to extract trade data from a given section.

    :param lines: List of text lines from the PDF.
    :param section_header: The header string that signals the start of this section.
    :param detection_keywords: A list of keywords to detect lines that contain trade data.
    :param all_section_headers: A list of all section header strings (used to detect section termination).
    :return: A list of extracted trade records.
    """
    trades = []
    found_section = False
    current_symbol = ""

    for line in lines:
        # If in the section and we encounter a new section header (other than the one we're processing), break.
        if found_section and any(h in line for h in all_section_headers if h != section_header):
            break

        # Detect the start of the desired section.
        if section_header in line:
            found_section = True
            continue  # Skip the header line itself.

        # Once the section is active, process lines that contain one of the detection keywords.
        if found_section and any(keyword in line for keyword in detection_keywords):
            record, current_symbol = process_trade_line(line, current_symbol)
            if record:
                trades.append(record)
    return trades


def write_csv(csv_output, data):
    with open(csv_output, mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow([
            "Description of Property", "Date Acquired", "Date Disposed",
            "Proceeds", "Cost Basis", "Code", "Amount of Adjustment", "Gain/Loss"
        ])
        writer.writerows(data)
    print(f"Trade data has been extracted and saved to {csv_output}")


def extract_trades(pdf_path):
    # Define the section headers.
    section_headers = [
        "SHORT TERM TRANSACTIONS FOR COVERED TAX LOTS",
        "SHORT TERM TRANSACTIONS FOR NONCOVERED TAX LOTS",
        "LONG TERM TRANSACTIONS FOR COVERED TAX LOTS",
        "LONG TERM TRANSACTIONS FOR NONCOVERED TAX LOTS",
    ]

    detection_keywords = ["Symbol", "Sale", "Total of"]

    # Read and accumulate all lines from the PDF pages.
    all_lines = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                all_lines.extend(text.split("\n"))

    # Map each section header to an output CSV filename.
    sections = {
        "SHORT TERM TRANSACTIONS FOR COVERED TAX LOTS": "short_term_covered.csv",
        "SHORT TERM TRANSACTIONS FOR NONCOVERED TAX LOTS": "short_term_uncovered.csv",
        "LONG TERM TRANSACTIONS FOR COVERED TAX LOTS": "long_term_covered.csv",
        "LONG TERM TRANSACTIONS FOR NONCOVERED TAX LOTS": "long_term_uncovered.csv",
    }

    # Loop through each section and process its trades.
    for header, filename in sections.items():
        trades = extract_trades_from_section(all_lines, header, detection_keywords, section_headers)
        write_csv(filename, trades)
