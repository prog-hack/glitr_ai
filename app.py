import os
import psycopg2
from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai

app = Flask(__name__)
CORS(app)  

DATABASE_URL = os.getenv("DATABASE_URL")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Configure Gemini API
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    # Using the standard model for text generation
    model = genai.GenerativeModel('gemini-1.5-flash') 

def get_db_connection():
    # connectng to db
    return psycopg2.connect(DATABASE_URL)
    
# end point 1
# get/health
@app.route('/health', methods=['GET'])
def health_check():
    # health check end point
    return jsonify({"status": "healthy"}), 200

# endpoint -2 post/gen
@app.route('/generate', methods=['POST'])
def generate_content():
    # Handle form data to match frontend multipart/form-data submission
    product_name = request.form.get('product_name')
    product_description = request.form.get('product_description')
    product_image = request.files.get('product_image') # Receive the file

    if not product_name or not product_description:
        return jsonify({"error": "Missing product_name or product_description"}), 400

    conn = get_db_connection()
    cur = conn.cursor()

    # 1. Insert initial job with status 'pending'
    cur.execute(
        "INSERT INTO jobs (product_name, product_description, status) VALUES (%s, %s, 'pending') RETURNING id;",
        (product_name, product_description)
    )
    job_id = cur.fetchone()[0]
    conn.commit()

    # 2. Turn product info into a prompt via Gemini API
    prompt_text = ""
    try:
        if GEMINI_API_KEY:
            # Instruct Gemini to create an image generation prompt
            llm_instructions = f"Write a highly detailed, creative image-generation prompt for a product advertisement. The product is named '{product_name}' and described as '{product_description}'. Output ONLY the prompt text without any conversational filler."
            response = model.generate_content(llm_instructions)
            prompt_text = response.text.strip()
        else:
            # Fallback if API key is missing
            prompt_text = f"Studio product advertisement of {product_name}: {product_description}"
    except Exception as e:
        print(f"Gemini API error: {e}")
        prompt_text = f"Studio product advertisement of {product_name}: {product_description}"

    # Mock image output (as permitted by the assignment)
    placeholder_image = f"https://picsum.photos/seed/{job_id}/400/300"

    # 3. Update database record to 'completed'
    cur.execute(
        "UPDATE jobs SET prompt = %s, status = 'completed', result_url = %s WHERE id = %s;",
        (prompt_text, placeholder_image, job_id)
    )
    conn.commit()
    cur.close()
    conn.close()

    return jsonify({
        "job_id": job_id,
        "status": "completed",
        "prompt": prompt_text,
        "result_url": placeholder_image
    }), 200

# get/jobid 
@app.route('/jobs/<int:job_id>', methods=['GET'])
def get_job(job_id):
    """Fetches status and details of a specific job by ID."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, product_name, status, result_url, prompt FROM jobs WHERE id = %s;", 
        (job_id,)
    )
    job = cur.fetchone()
    cur.close()
    conn.close()

    if not job:
        return jsonify({"error": "Job not found"}), 404

    return jsonify({
        "id": job[0],
        "product_name": job[1],
        "status": job[2],
        "result_url": job[3],
        "prompt": job[4]
    }), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)