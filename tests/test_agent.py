"""
Test script for run_agent() — Lab 10 Exercise 2
Run from trip_notes/:  python tests/test_agent.py
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.tools import run_agent

print("=== Agent Test ===")
print("The agent will show [Tool call] and [Tool result] as it works.")
print()

question = input("Your question: ").strip()
if not question:
    print("No question entered. Exiting.")
    sys.exit(0)

print()
result = run_agent(question)
print("\nAgent answer:")
print(result)
