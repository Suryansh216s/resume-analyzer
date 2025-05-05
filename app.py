from flask import Flask, render_template, request
import os
from PyPDF2 import PdfReader
import spacy
import google.generativeai as genai
from dotenv import load_dotenv
import json
import re
import logging

app = Flask(__name__)

# Setup logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables
load_dotenv()
gemini_api_key = os.getenv('GEMINI_API_KEY')

# Configure upload folder
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Load SpaCy model for keyword extraction
nlp = spacy.load('en_core_web_sm')

# Initialize Gemini API
genai.configure(api_key=gemini_api_key)
model = genai.GenerativeModel('gemini-1.5-flash')

def extract_keywords(text):
    """Extract alphanumeric keywords (nouns, proper nouns, entities) from text."""
    doc = nlp(text)
    keywords = {token.text.lower() for token in doc 
                if (token.pos_ in ('NOUN', 'PROPN') or token.ent_type_) and token.text.isalnum()}
    return keywords

def extract_resume_details(resume_text):
    """Extract name and skills using Gemini, phone and email with regex fallback."""
    prompt = f"""
    You are a resume parser. From the resume text, extract:
    - Candidate's name (plausible human name, not terms like 'Machine Learning')
    - Skills (technical/relevant skills, e.g., Python, SQL)
    Return as JSON:
    ```json
    {{
        "name": "string or null",
        "skills": ["string", ...]
    }}
    ```
    Resume text:
    '{resume_text[:2000]}'
    """
    try:
        response = model.generate_content(prompt)
        data = json.loads(response.text.strip().replace('```json', '').replace('```', ''))
        details = {
            'name': data.get('name'),
            'phone': None,
            'email': None,
            'skills': data.get('skills', [])
        }
    except Exception as e:
        logging.error(f"Gemini details error: {str(e)}")
        details = {'name': None, 'phone': None, 'email': None, 'skills': []}
    
    # Extract phone and email with regex
    phone_pattern = r'\b(\+?\d{1,3}[-.]?)?\(?\d{3}\)?[-.]?\d{3}[-.]?\d{4}\b'
    if phone_match := re.search(phone_pattern, resume_text):
        details['phone'] = phone_match.group(0)
    
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    if email_match := re.search(email_pattern, resume_text, re.IGNORECASE):
        details['email'] = email_match.group(0).lower()
    
    # Clean skills
    details['skills'] = list(set(skill.lower() for skill in details['skills'] if skill))
    return details

def detect_job_domain(job_description):
    """Detect job domain using Gemini."""
    prompt = f"""
    Identify the industry domain (tech, finance, healthcare, general) from the job description.
    Return a single word.
    Job description:
    '{job_description[:1000]}'
    """
    try:
        response = model.generate_content(prompt)
        domain = response.text.strip().lower()
        return domain if domain in ['tech', 'finance', 'healthcare', 'general'] else 'general'
    except Exception as e:
        logging.error(f"Gemini domain error: {str(e)}")
        return 'general'

def calculate_resume_score(resume_text, matched_keywords, job_keywords):
    """Calculate resume score based on keyword match, length, and formatting."""
    keyword_score = (len(matched_keywords) / len(job_keywords) * 50) if job_keywords else 0

    word_count = len(resume_text.split())
    length_score = 30 if 500 <= word_count <= 1000 else 20 if 300 <= word_count < 500 or 1000 < word_count <= 1500 else 10

    formatting_score = sum(6.67 for section in ['skills', 'experience', 'education'] if section in resume_text.lower())
    formatting_score = min(formatting_score, 20)

    return max(0, min(round(keyword_score + length_score + formatting_score), 100))

def generate_suggestions(missing_keywords, job_description, domain, name):
    """Generate resume analysis using Gemini."""
    domain_guidance = {
        'tech': "Highlight GitHub projects, certifications, or technologies (e.g., Python, AWS).",
        'finance': "Emphasize financial modeling, analytical skills, or certifications (e.g., CFA).",
        'healthcare': "Focus on patient care, clinical skills, or certifications (e.g., RN).",
        'general': "Highlight transferable skills, leadership, and achievements."
    }
    
    prompt = f"""
    You are a career coach for {domain} roles. A job seeker named {name or 'the candidate'} is applying for a role with:
    Job description: '{job_description[:1000]}'
    Missing keywords: {', '.join(missing_keywords)[:1000]}
    Provide a detailed analysis with:
    - Areas of Improvement Summary: 2-3 sentences on key gaps and ATS/recruiter impact.
    - Strengths: 3-5 strengths based on matched keywords or inferred content, with examples.
    - Weaknesses: 3-5 weaknesses based on missing keywords, with explanations.
    - Suggestions for Improvement: 4-6 actionable, domain-specific suggestions, following: {domain_guidance.get(domain, domain_guidance['general'])}.
    - SWOT Analysis: Detailed Strengths, Weaknesses, Opportunities, Threats, tailored to the job.
    Format as:
    ### Areas of Improvement Summary
    [Summary]
    ### Strengths
    - [Strength 1]
    - [Strength 2]
    ...
    ### Weaknesses
    - [Weakness 1]
    - [Weakness 2]
    ...
    ### Suggestions for Improvement
    - [Suggestion 1]
    - [Suggestion 2]
    ...
    ### SWOT Analysis
    **Strengths:** [Strengths]
    **Weaknesses:** [Weaknesses]
    **Opportunities:** [Opportunities]
    **Threats:** [Threats]
    Be concise, professional, and use bullet points for Strengths, Weaknesses, Suggestions.
    """
    try:
        response = model.generate_content(prompt)
        text = response.text.strip()
        logging.debug(f"Gemini response: {text}")
        
        sections = {
            'summary': '',
            'strengths': '',
            'weaknesses': '',
            'suggestions': '',
            'swot': {'strengths': '', 'weaknesses': '', 'opportunities': '', 'threats': ''}
        }
        
        current_section = None
        for line in text.split('\n'):
            line = line.strip()
            if line.startswith('### Areas of Improvement Summary'):
                current_section = 'summary'
            elif line.startswith('### Strengths'):
                current_section = 'strengths'
            elif line.startswith('### Weaknesses'):
                current_section = 'weaknesses'
            elif line.startswith('### Suggestions for Improvement'):
                current_section = 'suggestions'
            elif line.startswith('### SWOT Analysis'):
                current_section = 'swot'
            elif line.startswith('**Strengths:**'):
                sections['swot']['strengths'] = line.replace('**Strengths:**', '').strip()
            elif line.startswith('**Weaknesses:**'):
                sections['swot']['weaknesses'] = line.replace('**Weaknesses:**', '').strip()
            elif line.startswith('**Opportunities:**'):
                sections['swot']['opportunities'] = line.replace('**Opportunities:**', '').strip()
            elif line.startswith('**Threats:**'):
                sections['swot']['threats'] = line.replace('**Threats:**', '').strip()
            elif line and current_section in ['summary', 'strengths', 'weaknesses', 'suggestions']:
                sections[current_section] += f"\n{line}" if sections[current_section] else line
        
        for key in ['summary', 'strengths', 'weaknesses', 'suggestions']:
            sections[key] = sections[key].strip()
        
        return sections
    except Exception as e:
        logging.error(f"Gemini API error: {str(e)}")
        return {
            'summary': 'Unable to generate analysis. Ensure keywords are relevant.',
            'strengths': 'Unable to identify strengths.',
            'weaknesses': 'Unable to identify weaknesses.',
            'suggestions': 'Add missing keywords and quantify achievements.',
            'swot': {'strengths': 'N/A', 'weaknesses': 'N/A', 'opportunities': 'N/A', 'threats': 'N/A'}
        }

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'resume' not in request.files or 'job_description' not in request.form:
        return 'Missing resume or job description', 400
    file = request.files['resume']
    job_description = request.form['job_description']
    if file.filename == '' or not job_description.strip():
        return 'No file selected or empty job description', 400
    if file and file.filename.endswith('.pdf'):
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filepath)
        try:
            reader = PdfReader(filepath)
            resume_text = ''.join(page.extract_text() or '' for page in reader.pages)
            resume_keywords = extract_keywords(resume_text)
            job_keywords = extract_keywords(job_description)
            matched_keywords = resume_keywords.intersection(job_keywords)
            missing_keywords = job_keywords - resume_keywords
            resume_score = calculate_resume_score(resume_text, matched_keywords, job_keywords)
            domain = detect_job_domain(job_description)
            details = extract_resume_details(resume_text)
            suggestions = generate_suggestions(missing_keywords, job_description, domain, details.get('name'))
            result = {
                'matched': list(matched_keywords),
                'missing': list(missing_keywords),
                'details': details,
                'suggestions': suggestions,
                'resume_score': resume_score,
                'matched_json': json.dumps(list(matched_keywords)),
                'missing_json': json.dumps(list(missing_keywords)),
                'domain': domain
            }
            logging.debug(f"Result: {result}")
            return render_template('result.html', result=result)
        except Exception as e:
            logging.error(f"PDF error: {str(e)}")
            return f'Error processing PDF: {str(e)}', 500
    return 'Invalid file type', 400

if __name__ == '__main__':
    app.run(debug=True)