import os
import psycopg2
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  

DATABASE_URL = os.getenv("DATABASE_URL")

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
    # Receives product info, creates a job, and generates output.
    data = request.get_json()
    product_name = data.get('product_name')
    product_description = data.get('product_description')

    conn = get_db_connection()
    cur = conn.cursor()

    # 1. Insert initial job with status 'pending'
    cur.execute(
        "INSERT INTO jobs (product_name, product_description, status) VALUES (%s, %s, 'pending') RETURNING id;",
        (product_name, product_description)
    )
    job_id = cur.fetchone()[0]
    conn.commit()

    # 2. Turn product info into a prompt & mock image output (as permitted)
    prompt = f"Studio product advertisement of {product_name}: {product_description}"
    placeholder_image = f"https://picsum.photos/seed/{job_id}/400/300"

    # 3. Update database record to 'completed'
    cur.execute(
        "UPDATE jobs SET prompt = %s, status = 'completed', result_url = %s WHERE id = %s;",
        (prompt, placeholder_image, job_id)
    )
    conn.commit()
    cur.close()
    conn.close()

    return jsonify({
        "job_id": job_id,
        "status": "completed",
        "prompt": prompt,
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