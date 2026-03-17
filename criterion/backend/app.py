import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
from concurrent.futures import ThreadPoolExecutor
from backend.core.analyzer import Analyzer
import uuid

app = Flask(__name__)
CORS(app)

# Configuration
UPLOAD_FOLDER = 'sample_data/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# In-memory storage for the session
session_data = {
    "results": [],
    "alerts": []
}

executor = ThreadPoolExecutor(max_workers=5)

# Mock mode driven by environment variable (defaults to True if not explicitly False)
USE_MOCK = os.getenv("USE_MOCK", "True").lower() == "true"
analyzer = Analyzer(mock=USE_MOCK)

@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    agent_name = request.form.get('agent_name', 'Unknown Agent')

    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], f"{uuid.uuid4()}_{filename}")
    file.save(filepath)

    # Process the file
    try:
        result = analyzer.process_file(filepath, agent_name=agent_name)
        session_data["results"].append(result)

        # Check for alerts: Score of 1 on any parameter OR overall low score OR violations
        if result["overall_score"] <= 2.0 or any(v for v in result["violations"]) or any(s == 1 for s in result["parameters"].values()):
            alert_type = "Compliance Violation" if any(v for v in result["violations"]) else "Critical Fail"
            alert = {
                "id": str(uuid.uuid4()),
                "type": alert_type,
                "agent_name": agent_name,
                "conversation_id": result["id"],
                "score": result["overall_score"],
                "timestamp": result["date"]
            }
            session_data["alerts"].append(alert)

        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/batch', methods=['POST'])
def batch_upload():
    if 'files' not in request.files:
        return jsonify({"error": "No files part"}), 400

    files = request.files.getlist('files')
    if len(files) > 20:
        return jsonify({"error": "Maximum 20 files allowed"}), 400

    agent_name = request.form.get('agent_name', 'Multiple Agents')

    def process_and_store(file):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], f"{uuid.uuid4()}_{filename}")
        file.save(filepath)
        result = analyzer.process_file(filepath, agent_name=agent_name)
        return result

    try:
        results = list(executor.map(process_and_store, files))
        for result in results:
            session_data["results"].append(result)
            # Check for alerts in batch
            if result["overall_score"] <= 2.0 or any(v for v in result["violations"]) or any(s == 1 for s in result["parameters"].values()):
                alert = {
                    "id": str(uuid.uuid4()),
                    "type": "Critical Fail" if any(s == 1 for s in result["parameters"].values()) else "Compliance Violation",
                    "agent_name": agent_name,
                    "conversation_id": result["id"],
                    "score": result["overall_score"],
                    "timestamp": result["date"]
                }
                session_data["alerts"].append(alert)
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/results', methods=['GET'])
def get_results():
    return jsonify(session_data["results"])

@app.route('/api/leaderboard', methods=['GET'])
def get_leaderboard():
    # Aggregate results by agent
    agents = {}
    for res in session_data["results"]:
        name = res["agent_name"]
        if name not in agents:
            agents[name] = {
                "name": name,
                "overall_score": 0,
                "communication": 0,
                "problem_solving": 0,
                "efficiency": 0,
                "compliance": 0,
                "calls_processed": 0,
                "trend": res["trend"]
            }

        agents[name]["overall_score"] += res["overall_score"]
        agents[name]["communication"] += res["categories"]["communication"]
        agents[name]["problem_solving"] += res["categories"]["problem_solving"]
        agents[name]["efficiency"] += res["categories"]["efficiency"]
        agents[name]["compliance"] += res["categories"]["compliance"]
        agents[name]["calls_processed"] += 1

    leaderboard = []
    for name, data in agents.items():
        count = data["calls_processed"]
        leaderboard.append({
            "name": name,
            "overall_score": round(data["overall_score"] / count, 1),
            "communication": round(data["communication"] / count, 1),
            "problem_solving": round(data["problem_solving"] / count, 1),
            "efficiency": round(data["efficiency"] / count, 1),
            "compliance": round(data["compliance"] / count, 1),
            "calls_processed": count,
            "trend": data["trend"]
        })

    # Sort by overall score descending
    leaderboard.sort(key=lambda x: x["overall_score"], reverse=True)
    return jsonify(leaderboard)

@app.route('/api/alerts', methods=['GET'])
def get_alerts():
    return jsonify(session_data["alerts"])

@app.route('/api/clear', methods=['POST'])
def clear_session():
    session_data["results"] = []
    session_data["alerts"] = []
    return jsonify({"status": "success"})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
