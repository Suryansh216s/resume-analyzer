 A web application that analyzes resumes against job descriptions, providing a resume strength score, keyword analysis, and AI-powered suggestions for improvement. Built with Flask, Gemini AI, SpaCy, and Docker, deployed on Heroku.

 ![Resume Analyzer Screenshot](screenshots/screenshot.png)

 ## Features
 - **Resume Parsing**: Extracts name, email, phone, and skills from PDF resumes.
 - **Keyword Analysis**: Matches and identifies missing keywords from job descriptions.
 - **Resume Score**: Calculates a score (0-100) based on keyword matches, length, and formatting.
 - **AI-Powered Suggestions**: Provides detailed analysis (Summary, Strengths, Weaknesses, Suggestions, SWOT) using Gemini AI.
 - **Interactive UI**: Responsive design with keyword cloud, badges, and score bar.
 - **Dockerized**: Packaged for consistent deployment.
 - **Live Demo**: Try it at [https://resume-analyzer-suryansh.herokuapp.com](https://resume-analyzer-suryansh.herokuapp.com).

 ## Tech Stack
 - **Backend**: Flask, Python
 - **AI/NLP**: Google Gemini AI, SpaCy
 - **Frontend**: Bootstrap, WordCloud.js
 - **PDF Processing**: PyPDF2
 - **Deployment**: Docker, Heroku

 ## Setup Instructions
 ### Prerequisites
 - Python 3.9+
 - Docker
 - Google Gemini API key (get from [Google AI Studio](https://makersuite.google.com/))

 ### Local Setup
 1. Clone the repository:
    ```bash
    git clone https://github.com/Suryansh216s/resume-analyzer.git
    cd resume-analyzer
    ```
 2. Create a virtual environment and install dependencies:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    pip install -r requirements.txt
    python -m spacy download en_core_web_sm
    ```
 3. Create a `.env` file with your Gemini API key:
    ```bash
    echo "GEMINI_API_KEY=your-api-key" > .env
    ```
 4. Run the app:
    ```bash
    python app.py
    ```
 5. Open `http://localhost:5000` in your browser.

 ### Docker Setup
 1. Build the Docker image:
    ```bash
    docker build -t resume-analyzer .
    ```
 2. Run the container:
    ```bash
    docker run -p 5000:5000 --env-file .env resume-analyzer
    ```
 3. Open `http://localhost:5000`.

 ## Deployment to Heroku
 1. Install Heroku CLI and log in:
    ```bash
    heroku login
    ```
 2. Create a Heroku app:
    ```bash
    heroku create resume-analyzer-suryansh
    ```
 3. Push Docker image:
    ```bash
    heroku container:login
    docker tag resume-analyzer registry.heroku.com/resume-analyzer-suryansh/web
    docker push registry.heroku.com/resume-analyzer-suryansh/web
    heroku container:release web --app resume-analyzer-suryansh
    ```
 4. Set environment variables:
    ```bash
    heroku config:set GEMINI_API_KEY=your-api-key --app resume-analyzer-suryansh
    ```

 ## Screenshots
 ![Upload Page](screenshots/upload.png)
 ![Results Page](screenshots/results.png)

 ## Contributing
 Feel free to open issues or submit pull requests on [GitHub](https://github.com/Suryansh216s/resume-analyzer).

 ## License
 MIT License
