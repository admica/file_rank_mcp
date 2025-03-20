import os
import json
import sys
import re
import ast

from file_rank_simple import FileRankManager, DependencyDetector

# Testing file to demonstrate dependency visualization
manager = FileRankManager()
detector = DependencyDetector()

print("Testing tool functionality")
