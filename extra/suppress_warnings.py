"""
Suppress deprecation warnings for face_recognition
"""
import warnings
import os

# Suppress specific warnings
warnings.filterwarnings("ignore", category=UserWarning, module="face_recognition_models")
warnings.filterwarnings("ignore", message=".*pkg_resources is deprecated.*")

# Set environment variable to suppress setuptools warnings
os.environ['PYTHONWARNINGS'] = 'ignore::UserWarning:face_recognition_models'