from flask import Flask
from flask_cors import CORS
from config import FFMPEG_PATH, IMAGEMAGICK_PATH, LOCAL_MODEL_PATH, FLAN_MODEL_PATH

app = Flask(__name__)
CORS(app)

app.config['FFMPEG_PATH'] = FFMPEG_PATH
app.config['IMAGEMAGICK_PATH'] = IMAGEMAGICK_PATH
app.config['local_model_path'] = LOCAL_MODEL_PATH
app.config['flan_model_path'] = FLAN_MODEL_PATH

# Register the API blueprint under '/api'
from routes.api import api_bp
app.register_blueprint(api_bp, url_prefix="/api")

# Add a simple root route for the base URL
@app.route('/')
def hello_world():
    return 'Hello, World!'

if __name__ == "__main__":
    app.run(debug=True)
