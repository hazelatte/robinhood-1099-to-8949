# Robinhood 1099 to IRS Form 8949 Converter

This tool automates the process of converting **Robinhood 1099 PDFs** into **IRS Form 8949**. It extracts trade data, categorizes transactions, and fills out the appropriate sections of **Form 8949**, generating a final **merged PDF** with all required tax information.

## 🌟 Why Does This Project Exist?
- I make lots of short-term trades on Robinhood, so my 1099 is a mess.
- I don't want to pay TurboTax—I'm poor.
- I want to reuse the code next year.

## 🛠️ Usage
- Install required Python packages:
```commandline
pip install -r requirements.txt
```
- Run the program:
```commandline
python main.py 
```
- Enter your Name & SSN. (Chill, it's optional—I know it looks sus. But if you don't fill it in, don't forget to add it yourself in the outputted PDF.)
- Select your Robinhood 1099 PDF.
- Wait for the process to complete (takes a few seconds).
- The completed Form 8949 PDF will automatically open.

## 📝 Note
- You can thank ChatGPT for most of the work here.
- This is for **tax year 2024**. The Form 8949 used is also for 2024.