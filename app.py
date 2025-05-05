from flask import Flask, render_template, request
import os
from PyPDF2 import PdfReader

app = Flask(__name__)

# Configure upload folder
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure upload folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'resume' not in request.files:
        return 'No file uploaded', 400
    file = request.files['resume']
    if file.filename == '':
        return 'No file selected', 400
    if file and file.filename.endswith('.pdf'):
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filepath)
        # Extract text from PDF
        try:
            reader = PdfReader(filepath)
            text = ''
            for page in reader.pages:
                text += page.extract_text() or ''
            return f'File uploaded successfully! Extracted text: {text[:500]}...'  # Show first 500 chars
        except Exception as e:
            return f'Error processing PDF: {str(e)}', 500
    return 'Invalid file type', 400

if __name__ == '__main__':
    app.run(debug=True)