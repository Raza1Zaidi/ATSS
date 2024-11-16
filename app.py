from flask import Flask, request, render_template
import openai
import pdfplumber
from werkzeug.utils import secure_filename
import os

# Set up OpenAI API key
openai.api_key = "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"  # Replace with your actual API key

# Create Flask app
app = Flask(__name__)

# Configure the folder for file uploads
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'pdf'}

# Function to check file extension
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# Function to extract text from PDF
def extract_text_with_structure_handling(pdf_path):
    text = ''
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text(x_tolerance=2, y_tolerance=2)
            if page_text:
                page_text = page_text.replace('\n', ' ').replace('  ', ' ')
                text += page_text + '\n\n'
    return text

# Function to get GPT-3/4 response
def get_gpt_response(prompt):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",  # Adjust based on your model
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1000,
            temperature=0.7
        )
        return response['choices'][0]['message']['content']
    except Exception as e:
        return f"Error: {str(e)}"

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Handle file upload
        if 'resume' not in request.files:
            return "Please upload a resume."
        
        file = request.files['resume']
        if file.filename == '' or not allowed_file(file.filename):
            return "Invalid file type. Please upload a PDF."

        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        # Extract resume text from PDF
        resume_text = extract_text_with_structure_handling(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        # Get job description from the form
        job_description = request.form['job_description']

        # Construct prompt
        scoring_criteria = """
        Scoring Criteria for ATS:
        1. Impact-Driven Achievements (30% of total score)
           - Quantifiable Results (20%)
           - Scale of Impact (10%)
        2. Exact Experience Matching (25% of total score)
           - Total Years of Relevant Experience (15%)
           - Recent Experience Weighting (10%)
        3. Initiative and Project-Based Scoring (20% of total score)
           - Self-Initiated Projects (10%)
           - Leadership and Ownership (10%)
        4. Keyword Matching (15% of total score)
           - Skill Matching and Keyword Relevance (15%)
        Additional Notes:
        - Consider slight overqualification or underqualification (within +/- 1 to 2 years) as part of the tolerance range.
        """
        
        prompt = f"""
        You are an expert Resume Reviewer. Analyze the following resume and job description using the provided scoring criteria. 
        Return a 5-line review with scoring and 3 improvements.

        {scoring_criteria}

        Resume:
        {resume_text}

        Job Description:
        {job_description}
        """

        # Get response from GPT
        result = get_gpt_response(prompt)

        # Return the result as HTML with styling
        return render_template('result.html', result=result)

    return render_template('index.html')

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Default to 5000 if PORT is not set
    app.run(host="0.0.0.0", port=port, debug=True)

