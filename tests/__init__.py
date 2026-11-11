"""Tests never start background collection, rebuilding or publishing."""
import os

os.environ['RECONSTRUCTION_AUTO_UPDATE'] = '0'
