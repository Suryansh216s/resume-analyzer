from flask import Flask, render_template, request
import os
from PyPDF2 import PdfReader
import spacy
import google.generativeai as genai
from dotenv import load_dotenv

app = Flask(__name__)

# Load environment variables
load_dotenv()
gemini_api_key = os.getenv('GEMINI_API_KEY')

# Configure upload folder
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure upload folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Load SpaCy model
nlp = spacy.load('en_core_web_sm')

# Initialize Gemini API
genai.configure(api_key=gemini_api_key)
model = genai.GenerativeModel('gemini-1.5-flash')

def extract_keywords(text):
    """Extract keywords (nouns, proper nouns, entities) from text using SpaCy."""
    doc = nlp(text)
    keywords = []
    for token in doc:
        if token.pos_ in ('NOUN', 'PROPN') or token.ent_type_:
            keywords.append(token.text.lower())
    return set(keywords)

def calculate_resume_score(resume_text, matched_keywords, job_keywords):
    """Calculate a resume strength score (0-100) based on keyword match, length, and formatting."""
    # Keyword match score (50%)
    keyword_match_ratio = len(matched_keywords) / len(job_keywords) if job_keywords else 0
    keyword_score = keyword_match_ratio * 50  # Max 50 points

    # Resume length score (30%)
    word_count = len(resume_text.split())
    if 500 <= word_count <= 1000:
        length_score = 30  # Ideal length
    elif 300 <= word_count < 500 or 1000 < word_count <= 1500:
        length_score = 20  # Slightly off
    else:
        length_score = 10  # Too short or too long

    # Formatting score (20%)
    formatting_score = 0
    key_sections = ['skills', 'experience', 'education']
    resume_lower = resume_text.lower()
    for section in key_sections:
        if section in resume_lower:
            formatting_score += 6.67  # ~20/3 points per section
    formatting_score = min(formatting_score, 20)  # Cap at 20

    # Total score
    total_score = round(keyword_score + length_score + formatting_score)
    return max(0, min(total_score, 100))  # Clamp between 0 and 100

def generate_suggestions(missing_keywords, job_description):
    """Generate resume improvement suggestions using Gemini API."""
    if not missing_keywords:
        return "Your resume aligns well with the job description!"
    prompt = f"""
    You are a career coach. A job seeker is applying for a role with the following job description:
    '{job_description[:500]}'
    Their resume is missing these keywords: {', '.join(missing_keywords)}.
    Provide 2-3 concise suggestions to improve their resume, focusing on incorporating these keywords.
    Format as a bullet list.
    """
    try:
        response = model.generate_content(prompt)
        suggestions = response.text.strip()
        # Ensure bullet points are formatted
        if not suggestions.startswith('-'):
            suggestions = '\n'.join([f"- {line}" for line in suggestions.split('\n') if line.strip()])
        return suggestions or "Could not generate specific suggestions, but consider adding the missing keywords."
    except Exception as e:
        return f"Error generating suggestions: {str(e)}"

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'resume' not in request.files or 'job_description' not in request.form:
        return 'Missing resume or job description', 400
    file = request.files['resume']
    job_description = request.form['job_description']
    if file.filename == '':
        return 'No file selected', 400
    if not job_description.strip():
        return 'Job description is empty', 400
    if file and file.filename.endswith('.pdf'):
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filepath)
        # Extract text from PDF
        try:
            reader = PdfReader(filepath)
            resume_text = ''
            for page in reader.pages:
                resume_text += page.extract_text() or ''
            # Extract keywords
            resume_keywords = extract_keywords(resume_text)
            job_keywords = extract_keywords(job_description)
            # Compare keywords
            matched_keywords = resume_keywords.intersection(job_keywords)
            missing_keywords = job_keywords - resume_keywords
            # Calculate resume score
            resume_score = calculate_resume_score(resume_text, matched_keywords, job_keywords)
            # Generate AI suggestions
            suggestions = generate_suggestions(missing_keywords, job_description)
            # Prepare response
            result = {
                'matched': list(matched_keywords),
                'missing': list(missing_keywords),
                'resume_text': resume_text[:500],
                'suggestions': suggestions,
                'resume_score': resume_score
            }
            return render_template('result.html', result=result)
        except Exception as e:
            return f'Error processing PDF: {str(e)}', 500
    return 'Invalid file type', 400

if __name__ == '__main__':
    app.run(debug=True)