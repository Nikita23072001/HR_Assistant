#  import PyPDF2 # remember to install PyPDF2 (i. e. by using pip install...)
#
# !!!NOTE!!!
# Got errors with PyPDF2 like 'DeprecationError: PdfFileReader is deprecated and was removed in PyPDF2 3.0.0. Use PdfReader instead.'
# Fixed with the following command 'pip install 'PyPDF2<3.0''


# from googletrans import Translator    # Text transaltions, requires installing with the following command $ pip install googletrans==4.0.0-rc1
# from langdetect import detect         # Language detection, requires installing with the following command $ pip install langdetect
import PyPDF2  # PDF toolkit
import glob  # Allows to find all the pathnames matching a specified pattern, might require entering the following command $ pip install glob2
import os  # Module with methods for interacting with the operating system
import pandas as pd  # Library to work with xlsx files
import methods  # Myself library which containts usefull methods

# import requests                       # A library for making HTTP requests

import openai  # $ pip install openai

openai.api_key = "openai-api-key"


# I had to split the text into chunks as model didn't translate the whole text provided to it
def openai_translate(text: str) -> str:
    # Split the input text into chunks of maximum length 500 characters
    chunk_size: int = 500
    chunks: list[str] = [
        text[i : i + chunk_size] for i in range(0, len(text), chunk_size)
    ]

    translated_chunks: list[str] = []
    for chunk in chunks:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "Translate the following text into English:",
                },
                {"role": "user", "content": chunk},
            ],
            max_tokens=60,
            temperature=0.7,
        )
        translated_chunks.append(response.choices[0].message["content"].strip())

    # Concatenate the translated chunks into a single translated text
    translated_text: str = " ".join(translated_chunks)
    return translated_text


def openai_resume_summarise(text: str) -> str:
    prompt = f"""
    Summarize the content of the following resume:\n\n{text}\n\n. 
    
    Return the summary of the provided resume in 3-4 sentences.    
    """
    response = openai.Completion.create(
        engine="gpt-3.5-turbo-instruct", prompt=prompt, temperature=0.6, max_tokens=150
    )

    return response.choices[0].text.strip()


def extract_entities_with_openai(text: str) -> str:
    prompt = f"""
    Extract entites from the following resume:\n\n{text}\n\n. 
    
    Return the result in the format shown below:

    Job Title: ...\n
    years of experience: ... 
    education: ... 
    language skills: ... 
    Key skills: ...

    if years of experience are '2010 - Current' or '1996 - 2013' please add them up and return the number
    do not mention trainigs or certificates as education
    only languages and language levels as lenguage skillss
    if no data return 'No data'
    """
    response = openai.Completion.create(
        engine="gpt-3.5-turbo-instruct", prompt=prompt, temperature=0.1, max_tokens=150
    )

    return response.choices[0].text.strip()


def write_to_xlsx(resume_text: str, filename: str) -> None:
    entities_text = extract_entities_with_openai(resume_text)
    entities = dict(
        item.split(": ", 1) for item in entities_text.split("\n") if ": " in item
    )
    entities.update({"Filename": filename})
    # Standardize keys to lowercase and clean the dictionary keys
    cleaned_data_dict: dict = clean_dict_keys(entities)
    xp_years: int = extract_number_from_string(cleaned_data_dict["years of experience"])
    cleaned_data_dict.update({"years of experience": xp_years})
    strings_to_replace: list[str] = [
        "",
        "N/A",
        "None",
        "None mentioned",
        "No data",
        "None listed",
    ]
    replacement: str = "No data"
    standardized_data_dict: dict = standardize_dict_values(
        cleaned_data_dict, strings_to_replace, replacement
    )
    print(standardized_data_dict)
    append_dict_to_xlsx(standardized_data_dict, "xlsx_report.xlsx")
    return None


def translate_text_to_eng(text: str) -> str:
    translator = Translator()
    translation = translator.translate(text, dest="en")
    return translation.text


def extract_text_from_pdf(filename: str) -> str:
    text: str = ""
    file = open(filename, "rb")
    pdf_reader = PyPDF2.PdfFileReader(file)
    # the loop checks all the pages in a file and extracts the text from them
    for page_num in range(pdf_reader.numPages):
        text += pdf_reader.getPage(page_num).extract_text()
    file.close()
    return text


def modify_resume_with_openai(resume_file: str, vacancy_file: str) -> str:
    resume_text = resume_file

    with open(vacancy_file, "r", encoding="utf-8") as vacancy_f:
        vacancy_text = vacancy_f.read()

    prompt = f"Given the following resume:\n{resume_text}\n\nAnd the requirements of the vacancy:\n{vacancy_text}\n\nPlease modify the resume to better fit the vacancy:"

    response = openai.Completion.create(
        engine="gpt-3.5-turbo-instruct", prompt=prompt, temperature=0.5, max_tokens=200
    )

    modified_resume = response.choices[0].text.strip()
    return modified_resume


def standardize_dict_values(
    dict_data: dict, strings_to_replace: list[str], replacement: str
) -> dict:
    standardized_dict = {}
    for key, value in dict_data.items():
        if value in strings_to_replace:
            standardized_dict[key] = replacement
        else:
            standardized_dict[key] = value
    return standardized_dict


def clean_dict_keys(data_dict: dict) -> dict:
    """
    Remove leading and trailing whitespaces from dictionary keys
    and standardize keys to lowercase.
    """
    cleaned_dict = {key.strip().lower(): value for key, value in data_dict.items()}
    return cleaned_dict


def append_dict_to_xlsx(cleaned_data_dict: dict, filename: str) -> None:
    try:
        # Read existing data from the Excel file, if it exists
        try:
            existing_df = pd.read_excel(filename)
        except FileNotFoundError:
            existing_df = (
                pd.DataFrame()
            )  # Create an empty DataFrame if the file doesn't exist

        # Convert the cleaned dictionary data into a DataFrame
        new_row = pd.DataFrame(
            [cleaned_data_dict.values()], columns=cleaned_data_dict.keys()
        )

        # Concatenate the existing DataFrame with the new row
        updated_df = pd.concat([existing_df, new_row], ignore_index=True)

        # Write the updated DataFrame to the Excel file
        updated_df.to_excel(filename, index=False)

        print("Data appended successfully to", filename)
    except Exception as e:
        print("An error occurred:", e)

    return None


def extract_number_from_string(text: str) -> int:
    extracted_number = ""
    for char in text:
        if char.isdigit():
            extracted_number += char
    extracted_number = int(extracted_number)
    return extracted_number


### didn't work with DA andf LinkedIN pages. When I try to copy webpage using the script it doesn't have the content needed ###
# def get_webpage_source(url):
#     try:
#         response = requests.get(url)
#         if response.status_code == 200:
#             return response.text
#         else:
#             print(f"Failed to retrieve webpage. Status code: {response.status_code}")
#             return None
#     except requests.RequestException as e:
#         print(f"An error occurred: {e}")
#         return None


# def create_html_file(html_content, filename):
#     try:
#         with open(filename, 'w', encoding='utf-8') as file:
#             file.write(html_content)
#         print(f"HTML file '{filename}' created successfully.")
#     except Exception as e:
#         print(f"An error occurred while creating the HTML file: {e}")


def check_non_eng_files(path: str) -> list:
    non_eng_files: list[str] = []
    for filename in glob.glob(
        os.path.join(path, "*.pdf")
    ):  # in this case glob is used to match pdf files only
        text = extract_text_from_pdf(filename)
        try:
            src_lang = detect(text)
        except:
            print("The file " + filename + " threw an exception")
        if src_lang != "en":
            non_eng_files.append(filename)
            pass
    return non_eng_files


def count_files_in_directory(directory_path: str) -> None:
    try:
        # List all files in the directory
        files = os.listdir(directory_path)
        # Filter only files (exclude directories)
        files = [
            file for file in files if os.path.isfile(os.path.join(directory_path, file))
        ]
        # Count the number of files
        file_count = len(files)

        return file_count
    except Exception as e:
        print(f"An error occurred: {e}")
        return None


### MAIN ###

# path = 'C:/Users/anton/OneDrive/Desktop/AI learning course tasks/5t9wq456389.pdf'
# print(count_files_in_directory(path))
# filelist = check_non_eng_files(path)
# print(filelist)
# print(extract_text_from_pdf('C:/Users/anton/OneDrive/Desktop/AI learning course tasks/3547447.pdf'))

path = "C:/Users/anton/OneDrive/Desktop/AI learning course tasks/sample_dataset"

### CHECKS FOLDER FOR PDF FILES AND EXTRACTS THE TEXT DATA FROM THEM ###
for filename in glob.glob(
    os.path.join(path, "*.pdf")
):  # glob is used to match .pdf files only
    f = open(filename, "rb")
    pdf_reader = PyPDF2.PdfFileReader(f)
    text = pdf_reader.getPage(0).extractText()  # text extraction
    entities = extract_entities_with_openai(text)
    write_to_xlsx(entities, filename)


# summarry = openai_resume_summarise(response)
# print(summarry)
# response = openai_translate(text)
# entities = extract_entities_with_openai(response)

# vacancy_file = './Sample vacancy.txt'
# resume_file = response

# modified_resume = modify_resume_with_openai(resume_file, vacancy_file)

# print(modified_resume)


# html_content = get_webpage_source("https://www.linkedin.com/jobs/search/?currentJobId=3833692251&f_C=10882&geoId=92000000&origin=COMPANY_PAGE_JOBS_CLUSTER_EXPANSION&originToLandingJobPostings=3833692251%2C3826067551%2C3817608877%2C3813323341%2C3834077396#HYM")
# filename = "vacancy.html"
# create_html_file(html_content, filename)
# src_lang = detect(text) # language detection
# print(src_lang)
#
# src_lang = translator.detect(text) # language detection
# print(src_lang == 'en')
# print(src_lang)
# translation = translate_text_to_eng(text)
# print(translation)
