from flask import Flask, request, jsonify, send_from_directory, redirect, url_for
from pymongo import MongoClient
import requests
import datetime

app = Flask(__name__)

# MongoDB connection
client = MongoClient("mongodb+srv://arya:arya@arya.cnth2.mongodb.net/?retryWrites=true&w=majority&appName=arya")
db = client.get_database('chatbot')
users_collection = db.get_collection('users')

# Hugging Face API details
HF_API_URL = "https://api-inference.huggingface.co/models/Arya20032705/asuka"
HF_API_KEY = "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"

def get_bot_response(user_message):
    headers = {
        "Authorization": f"Bearer {HF_API_KEY}"
    }
    payload = {
        "inputs": user_message
    }
    response = requests.post(HF_API_URL, headers=headers, json=payload)

    if response.status_code == 200:
        bot_reply = response.json()[0]['generated_text']
        return bot_reply
    else:
        return "Sorry, can you please wait 10-15 seconds, i am making coffee (BOT is loading)"

@app.route('/')
def serve_name():
    return send_from_directory('static', 'name.html')

@app.route('/chat', methods=['GET', 'POST'])
def serve_chat():
    if request.method == 'POST':
        user_name = request.form.get('name')

        if not user_name:
            return redirect(url_for('serve_name'))

        # Generate the initial message
        initial_message = f"Hey, I am {user_name}"

        # Get bot response using Hugging Face API
        bot_reply = get_bot_response(initial_message)

        # Store the initial message and bot reply in MongoDB
        user_doc = users_collection.find_one({'name': user_name})
        if not user_doc:
            users_collection.insert_one({'name': user_name, 'messages': []})

        users_collection.update_one(
            {'name': user_name},
            {'$push': {'messages': {'timestamp': datetime.datetime.utcnow(), 'user_message': initial_message, 'bot_reply': bot_reply}}}
        )

        # Store the user name in session and redirect to the chat page
        return redirect(url_for('serve_chat', name=user_name))

    user_name = request.args.get('name')
    return send_from_directory('static', 'index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.get_json()
    user_name = data.get('name')
    user_message = data.get('message')

    if not user_name or not user_message:
        return jsonify({'reply': 'Name or message not provided.'}), 400

    # Get bot response using Hugging Face API
    bot_reply = get_bot_response(user_message)

    # Store the message in MongoDB
    user_doc = users_collection.find_one({'name': user_name})
    if not user_doc:
        users_collection.insert_one({'name': user_name, 'messages': []})

    users_collection.update_one(
        {'name': user_name},
        {'$push': {'messages': {'timestamp': datetime.datetime.utcnow(), 'user_message': user_message, 'bot_reply': bot_reply}}}
    )

    return jsonify({'reply': bot_reply})

if __name__ == '__main__':
    app.run(debug=True)
