from flask import Blueprint, jsonify

main = Blueprint('main', __name__)

@main.route('/')
def index():
    return jsonify({'status': 'ok', 'message': 'Ymmo API is running'})