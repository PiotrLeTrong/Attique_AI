import os, json
import pandas as pd
import numpy as np

from datetime import datetime, timezone
from tenacity import retry, stop_after_attempt, wait_exponential
from openai import OpenAI

path = "C:\\Users\\wb506337\\OneDrive - WBG\\AI_Bready_2026"
os.chdir(path)

## The idea was to convert the csv into data frame and that into a JSON element that can be appended on a 1 row at a time instance. 
## I had also had the idea to do it in list. 
## somehow I can't get past looping the JSON into the API

print(os.getenv("OPENAI_API_KEY"))
#client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

csv_path = "./01_data/02_inter/WBL_Labor_survey_output.csv"
out_path = "./01_data/02_inter/WBL_Labor_survey_output_AI_Answers_USA.csv"

WBL_dataframe = pd.read_csv(csv_path)

WBL_dataframe = WBL_dataframe[(WBL_dataframe.uncertainty_flag == False)]
WBL_dataframe = WBL_dataframe.fillna("")

data = WBL_dataframe.to_json(orient="records", indent=2, force_ascii=False)

data = json.loads(data)
SYSTEM = """
    You are an expert legal research assistant in the field of Women in relation to business and law. You focus on how how laws, regulations, policies, precendents, and their implementation affect women as economic actors. This approach considers barriers and enablers that all women encounter at different stages of their working lives, with a focus on those applicable to women employees and entrepreneurs. 
    Specifically on  how laws, regulations, and policies and their implementation (or lack thereof) affect women throughout their working lives. The chosen 10 topics consider women’s interactions with the law as economic actors at different stages of their lives, with a focus on women employees and entrepreneurs as they begin, progress through, and end their careers:
        1. Safety, 
        2. Mobility, 
        3. Workplace, 
        4. Pay, 
        5. Marriage, 
        6. Parenthood, 
        7. Childcare, 
        8. Entrepreneurship, 
        9. Assets, 
        10. Pension.
    Jurisdiction: United States law with a focus on California. Where relevant, consider Los Angeles County/City. 
    Apply preemption: U.S. federal > state > local. Judicial hierarchy: SCOTUS > federal appellate > district > state courts.
       
    You will be provided a dataframe file, the only columns needed for this are: "question_section_text", "question_main_text", "question_supplementary_text"
    There are 2 cases of questions to be anserwed. Your job is to answer specific, narrow yes/no legal questions derived from labor and anti-discrimination law for a specified country and (when provided) sub-jurisdiction.
Non-advisory: Provide public legal information and citations only. Do not give legal advice; include a brief disclaimer.


        Research requirements

        - ONLY CONSULT THE MOST RECENT PRIMARY SOURCES available online (statutes, consolidated acts, regulations, official gazettes) and authoritative secondary sources (government websites, ILO, OECD, official law-reform commissions).

        - If there is any chance the law has changed since June 2024, verify with current sources.

        - ALWAYS INCLUDE CITATIONS IN BLUEBOOK FORMAT (law title, section/article, jurisdiction, and enactment/amendment date). When possible, include the last consolidated date.
         
        Scope & definitions

        - Answer ONLY the question asked (e.g., “Does the law prohibit discrimination in recruitment based on marital status?”) in a YES or NO manner.

        - “Recruitment” includes job advertisements, application screening, interviews, and selection, unless the statute uses a narrower definition—follow the statute’s definition if it exists.

        - “Prohibit” means the law expressly forbids or makes unlawful; if the law is silent, answer No/Not explicit and explain any analogous provisions.
        
        - IN CASES OF UNCERTAINTY GREATER THAN REASONABLE DOUBT EXPRESS A "NOT SURE" 
        
        - If sources conflict, state the conflict and prefer newer and primary sources.
        OUTPUT TARGET (to be enforced by JSON schema):
        - AI_Answer: "Yes" | "No" | "Not sure"
        - AI_Legal_Basis: list of Bluebook-formatted citations (strings)
        - AI_Reasoning: 2–6 sentences explaining reasoning and any conflicts/exceptions (BFOQ, etc.)
        - AI_Confidence: float 0.0–1.0 (0=guess, 1=beyond reasonable doubt)
        - Echo back the inputs for traceability.
        
"""


schema = {
    "type": "object",
    "properties": {
        "AI_Answer": {"type": "string", "enum": ["Yes", "No", "Not sure"]},
        "AI_Legal_Basis": {"type": "array", "items": {"type": "string"}},
        "AI_Reasoning": {"type": "string"},
        "AI_Confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0}
    },
    "required": ["AI_Answer", "AI_Legal_Basis", "AI_Reasoning", "AI_Confidence"]
}


def build_user_message(q):
    """
    Build a clean natural-language prompt from one JSON record.
    Uses supplementary question if available, otherwise main question.
    """
    question_text = q["question_supplementary_text"] or q["question_main_text"]

    return f"""
Section: {q['question_section_text']}

Question:
{question_text}

Task: Answer only the supplementary question, based on general legal principles.
Return only valid JSON.
"""



# -------------------------------
# Loop through questions and query GPT-5-mini
# -------------------------------
updated_records = []
for idx, q in enumerate(data, start=1):
    user_prompt = build_user_message(q)

    try:
        response = client.chat.completions.create(
            model="gpt-5-mini",
            messages=[
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": user_prompt}
            ],
            store = True,
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "AI_Legal_Answer_Schema",
                    "schema": schema
                }
            }
        )

        # Parse model output
        ai_output = json.loads(response.choices[0].message.content)

        # Append model output to your record
        q["AI_Output"] = ai_output

        print(f"✅ Processed {idx}/{len(data)}: page {q['page']}")

    except Exception as e:
        print(f"❌ Error on record {idx} (page {q['page']}): {e}")
        q["AI_Output"] = {"error": str(e)}  # Keep traceability


    # Optional: small delay between calls to avoid rate limits


    updated_records.append(q)

# -------------------------------
# Save the augmented dataset
# -------------------------------
with open("questions_with_ai.json", "w", encoding="utf-8") as f:
    json.dump(updated_records, f, indent=2, ensure_ascii=False)

print("\n✅ All done! New file: questions_with_ai.json")