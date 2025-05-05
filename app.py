from flask import Flask, render_template, request
import os
from PyPDF2 import PdfReader
import spacy

app = Flask(__name__)

# Configure upload folder
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure upload folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Load SpaCy model
nlp = spacy.load('en_core_web_sm')

def extract_keywords(text):
    """Extract keywords (nouns, proper nouns, entities) from text using SpaCy."""
    doc = nlp(text)
    keywords = []
    for token in doc:
        if token.pos_ in ('NOUN', 'PROPN') or token.ent_type_:
            keywords.append(token.text.lower())
    return set(keywords)  # Remove duplicates

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
            # Prepare response
            result = {
                'matched': list(matched_keywords),
                'missing': list(missing_keywords),
                'resume_text': resume_text[:500]  # Truncate for display
            }
            return render_template('result.html', result=result)
        except Exception as e:
            return f'Error processing PDF: {str(e)}', 500
    return 'Invalid file type', 400

if __name__ == '__main__':
    app.run(debug=True)