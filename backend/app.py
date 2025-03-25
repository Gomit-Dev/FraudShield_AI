from flask import Flask, request, jsonify
import numpy as np
import joblib
import requests
import logging
from datetime import datetime

app = Flask(__name__)

# Load pre-trained fraud detection model
model = joblib.load('fraud_detection_model.pkl')

# Enable logging for fraud alerts
logging.basicConfig(filename='fraud_alerts.log', level=logging.INFO, format='%(asctime)s - %(message)s')

def log_fraud_alert(transaction_id, amount, location):
    """Log fraud alerts for unusual transactions"""
    alert_message = f"Fraud Alert: Transaction ID {transaction_id} | Amount: ${amount} | Location: {location}"
    logging.info(alert_message)
    return alert_message

@app.route('/predict', methods=['POST'])
def predict():
    """Predict if a transaction is fraudulent and provide confidence score"""
    try:
        data = request.json
        features = np.array(data['features']).reshape(1, -1)
        prediction = model.predict(features)
        probability = model.predict_proba(features)[0][1]  # Probability of fraud
        result = "Fraudulent" if prediction[0] == 1 else "Legitimate"
        response = {"prediction": result, "confidence": f"{probability:.2f}"}
        
        # Log fraud alerts
        if prediction[0] == 1:
            alert_msg = log_fraud_alert(data.get('transaction_id', 'Unknown'), data.get('amount', 'Unknown'), data.get('location', 'Unknown'))
            response["alert"] = alert_msg
        
        return jsonify(response)
    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == '__main__':
    app.run(debug=True)
