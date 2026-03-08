import datetime
import os

# Make sure the data folder exists
if not os.path.exists("data"):
    os.makedirs("data")

# Ask user input
week_number = input("What week number is this?\n")
reflection = input("Paste your weekly reflection here:\n")

# Count words
word_count = len(reflection.split())

# Generate timestamp
timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

# Create file path
filename = f"data/week_{week_number}_{timestamp}.txt"

# Write to file
with open(filename, "w") as file:
    file.write("WEEKLY REFLECTION\n")
    file.write("-----------------\n")
    file.write("Week number: " + week_number + "\n")
    file.write("Timestamp: " + timestamp + "\n")
    file.write("Word count: " + str(word_count) + "\n\n")
    file.write(reflection)

print("\nSaved successfully to:", filename)