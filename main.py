import os
import platform
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox
from extract_robinhood_trades import extract_trades
from fill_form_8949 import fill_form

def open_file(file_path):
    """Open a file using the default program, depending on the OS."""
    try:
        system = platform.system()
        if system == "Windows":
            os.startfile(file_path)
        elif system == "Darwin":  # macOS
            subprocess.call(["open", file_path])
        else:  # Linux and others
            subprocess.call(["xdg-open", file_path])
    except Exception as e:
        messagebox.showerror("Error", f"Could not open file: {file_path}\n{e}")


def run_process(pdf_file, name, ssn):
    try:
        # Run the extraction process using the selected PDF file.
        extract_trades(pdf_path=pdf_file)

        # Run the form-filling process which reads from the generated CSV.
        fill_form(name, ssn)

        messagebox.showinfo("Success", "Process completed successfully!")

        # Automatically open the filled PDF.
        filled_pdf_path = "f8949_filled.pdf"
        open_file(filled_pdf_path)
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred:\n{e}")


def select_file():
    # Open a file dialog to select the Robinhood summary PDF.
    file_path = filedialog.askopenfilename(
        title="Select Robinhood 1099 PDF",
        filetypes=[("PDF Files", "*.pdf")]
    )
    if file_path:
        user_name = name_entry.get().strip()
        user_ssn = ssn_entry.get().strip()
        run_process(file_path, user_name, user_ssn)


def main():
    global name_entry, ssn_entry  # Declare as globals so select_file can access them

    root = tk.Tk()
    root.title("Robinhood 1099 to 8949")
    root.geometry("500x250")

    # Name label and entry
    tk.Label(root, text="NAME: (Optional)").pack(pady=(20, 0))
    name_entry = tk.Entry(root, width=40)
    name_entry.pack(pady=5)

    # SSN label and entry
    tk.Label(root, text="SSN: (Optional)").pack(pady=(10, 0))
    ssn_entry = tk.Entry(root, width=40)
    ssn_entry.pack(pady=5)

    # Button to select the PDF file
    tk.Button(root, text="Select Robinhood 1099 PDF", command=select_file).pack(pady=20)

    root.mainloop()


if __name__ == "__main__":
    main()
