from flask import Blueprint, request, abort, g, jsonify


# Create a Blueprint instance for the data module
data_bp = Blueprint('data', __name__)
