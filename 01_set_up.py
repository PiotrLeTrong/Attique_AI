# -*- coding: utf-8 -*-
"""
Created on Tue Nov  4 10:02:59 2025

@author: wb506337
"""
import os
from pathlib import Path
import pdfplumber, json, pandas as pd
path = "C:\\Users\\wb506337\\OneDrive - WBG\\AI_Bready_2026"
os.chdir(path)
from openai import OpenAI

print(os.getenv("OPENAI_API_KEY"))
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def extract_text_from_pdf(pdf_path):
    import pdfplumber
    all_text = []
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            text = page.extract_text()
            if text:
                all_text.append(f"Page {i}\n{text}")
    return all_text


pdf_path = "./01_data/01_raw/WBL_2026_Labor_Questionnaire2.pdf"
pages = extract_text_from_pdf(pdf_path)

SYSTEM = """
    You are an expert in data extraction assistant specialized in survey data preparation. You take the question inputs from a a raw text (extracted from a pdf file) and convert them into plain text. 
    The file was extracted pagewise and then combined into 1 dataset containing all of the text needed for the process. 
    Output rules:
        1. DO NOT MAKE ANY CHANGES TO THE TEXT, REPLICATE THE TEXT AS FAITHFULLY AS POSSIBLE. TRANSCRIBE DIRECTLY. PRESERVE ORGINAL WORDING AND ORDER.
        2. Everything needing to be extracted begins with a numerical notation. There are 3 elements to draw data from:
            a. Section          - Always begins with "Section. [0-9]. TEXT". 
            b. Main Question    - Always begins with "[0-9]+.[0-9]+. TEXT". It stands alone or has a supplementary set of questions after. Always associated with a Section
            b. Supplementary Question    - Always begins with "[0-9]+.[0-9]+.[0-9]+. TEXT". It never stands alone. Always attached to a Section and Main question.
            eg. Supplemenatry Question "3.1.4. What percentage of earnings is received during maternity leave?" is associated with Main Question "3.1. Is there paid leave available to mothers?", both belong to Section "Section 3. Parenthood".      
        3. Output ONLY valid CSV (UTF-8).UT 
            Each row must contain the columns:
            page,question_section_text,question_main_text,question_supplementary_text,uncertainty_flag,uncertainty_note  
            "question_section_text": string,             // e.g, "Section 1. Work", "Section. 2. Pay". 
            "question_main_text": string,                // e.g, "1.1. Does the law prohibit discrimination in recruitment based on marital status, parental status, or age?", "1.2. Does the law prohibit discrimination in employment based on gender". 
            "question_supplementary_text": string,       // e.g., "1.1.1. Does the law prohibit discrimination in recruitment based on marital status?", "1.1.2. Does the law prohibit discrimination in recruitment based on parental status". 
            "uncertainty_flag": boolean,                   // true if you had to infer any structure or content. Do not use "" marks when inserting answers. 
            "uncertainty_note": string | null              // short note if uncertain
            Extraction logic:
        - “Use double quotes around every field. Do not include commas outside of quoted fields.”        
        - Only extract lines that begin with a numerical sequence.
          a. Section: starts with “Section [0-9].” followed by text.
          b. Main question: starts with “[0-9]+.[0-9]+.” followed by text. Include text following the "ⓘ" symbol if available, otherwise skip.
          c. Supplementary question: starts with “[0-9]+.[0-9]+.[0-9]+.” followed by text. 
        - Each "question_supplementary_text"  must link to its parent "question_main_text" and section context (if detectable) on the same line of data.
        - "question_supplementary_text" should never be in the "question_main_text" column.
        - If any level is missing, set the missing field to null and mark uncertainty_flag = true with an explanatory note.
        - Do NOT summarize, reword, or correct text. Transcribe exactly, preserving original wording and order.
        - Merge multi-line questions into a single line (replace internal line breaks with spaces).
        - Omit irrelevant content (headers, footers, metadata)
        4. If a page contains metadata or irrelevant content (headers, page numbers, footers), omit it.
        5. Do not summarize; transcribe exactly, preserving original wording and order.
        6. Handle multi-line questions or answers gracefully (merge into a single cell with no line breaks).
        7. DO NOT SKIP QUESTIONS.
      If formatting is ambiguous:
    - Make your best structured guess but clearly label uncertain entries with “UNCERTAIN” in a separate column. CLEARLY DENOTE ANY UNCERTAINTIES
    - Preserve all content, even if incomplete.
    Output should begin with a single header row, then rows of data.
    Example:
    
    question_section_text,question_main_text,question_supplementary_text
    "Section 1. Work", "1.1. Does the law prohibit discrimination in recruitment based on marital status, parental status, or age? Select “Yes” if the law explicitly prohibits employers from discriminating based on marital status, parental status, or age in recruitment. Also select “Yes” if the law mandates a broad prohibition of discrimination based on marital status, parental status, or age and a general prohibition of discrimination in recruitment."
    ,"1.1.1. Does the law prohibit discrimination in recruitment based on marital status?"

"""

#subset_pages = pages [9:12]
subset_pages = [''.join(pages[9:34])]
first_page = True

out_path = "./01_data/02_inter/WBL_Labor_survey_output.csv"
with open(out_path, "w", encoding="utf-8") as f:
    for i, page_text in enumerate(subset_pages, start=1):
        print(f"Processing chunk {i} of {len(subset_pages)}...")

        response = client.responses.create(
            model="gpt-5-mini",
            input=[
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": f"Convert this to CSV:\n{page_text}"}
            ],
            store = True
        )

        page_csv = response.output_text.strip()
        lines = page_csv.splitlines()

        if first_page:
            f.write(page_csv + "\n")
            first_page = False
        else:
            f.write("\n".join(lines[1:]) + "\n")

print(f"✅ Combined CSV saved to: {out_path}")

print("Used model:", response.model)  




# Token accounting
usage = response.usage
print("Prompt tokens:", usage.input_tokens)
print("Output tokens:", usage.output_tokens)
print("Total tokens:", usage.total_tokens)
