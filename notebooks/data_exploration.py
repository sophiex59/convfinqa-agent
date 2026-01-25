# %% [markdown]
# # ConvFinQA Data Exploration
#
# This notebook explores the structure and content of the ConvFinQA dataset
# to understand how to approach answering financial document questions.

# %%
import json
from pathlib import Path
from pprint import pprint

# Load the dataset
data_path = Path("data/convfinqa_dataset.json")
with open(data_path) as f:
    data = json.load(f)

print(f"Dataset keys: {data.keys()}")
print(f"Train records: {len(data['train'])}")
print(f"Dev records: {len(data['dev'])}")

# %% [markdown]
# ## Sample Record Structure
#
# Let's look at a single record to understand its structure.

# %%
# Pick a sample record
sample = data["dev"][0]

print("=" * 60)
print(f"Record ID: {sample['id']}")
print("=" * 60)

print("\n📄 DOCUMENT STRUCTURE:")
print(f"  pre_text length: {len(sample['doc']['pre_text'])} chars")
print(f"  post_text length: {len(sample['doc']['post_text'])} chars")
print(f"  table rows: {len(sample['doc']['table'])}")

print("\n💬 DIALOGUE:")
print(f"  Number of questions: {len(sample['dialogue']['conv_questions'])}")
for i, q in enumerate(sample["dialogue"]["conv_questions"]):
    print(f"  Q{i+1}: {q}")

print("\n🎯 ANSWERS:")
for i, (ans, exe) in enumerate(zip(
    sample["dialogue"]["conv_answers"],
    sample["dialogue"]["executed_answers"]
)):
    print(f"  A{i+1}: {ans} (executed: {exe})")

print("\n📊 FEATURES:")
pprint(sample["features"])

# %% [markdown]
# ## Document Content
#
# Let's see the actual text and table content.

# %%
print("=" * 60)
print("PRE-TEXT (before table):")
print("=" * 60)
print(sample["doc"]["pre_text"][:1500])
print("..." if len(sample["doc"]["pre_text"]) > 1500 else "")

# %%
print("=" * 60)
print("TABLE:")
print("=" * 60)
table = sample["doc"]["table"]
for row_name, row_data in list(table.items())[:10]:
    print(f"\n{row_name}:")
    if isinstance(row_data, dict):
        for col, val in row_data.items():
            print(f"  {col}: {val}")

# %%
print("=" * 60)
print("POST-TEXT (after table):")
print("=" * 60)
print(sample["doc"]["post_text"][:1000] if sample["doc"]["post_text"] else "(empty)")

# %% [markdown]
# ## Question Analysis
#
# Let's analyze the types of questions and their answers.

# %%
# Look at dialogue patterns
print("DIALOGUE BREAKDOWN:")
print("-" * 40)
for i, (q, a, exe, prog) in enumerate(zip(
    sample["dialogue"]["conv_questions"],
    sample["dialogue"]["conv_answers"],
    sample["dialogue"]["executed_answers"],
    sample["dialogue"]["turn_program"]
)):
    print(f"\nTurn {i+1}:")
    print(f"  Question: {q}")
    print(f"  Answer: {a}")
    print(f"  Executed: {exe}")
    print(f"  Program: {prog}")

# %% [markdown]
# ## Multiple Records Comparison
#
# Let's look at a few records to understand variety.

# %%
print("SAMPLE OF DEV RECORDS:")
print("=" * 60)
for record in data["dev"][:5]:
    features = record["features"]
    print(f"\n📁 {record['id']}")
    print(f"   Questions: {features['num_dialogue_turns']}")
    print(f"   Type II (hybrid): {features['has_type2_question']}")
    print(f"   Q1: {record['dialogue']['conv_questions'][0][:60]}...")

# %% [markdown]
# ## Human Reasoning Exercise
#
# Pick a record and try to answer the questions yourself to understand the task.

# %%
# Pick a specific record to analyze manually
test_record = data["dev"][3]  # Change index to explore different records

print("=" * 60)
print(f"TRY TO ANSWER: {test_record['id']}")
print("=" * 60)

print("\n📄 DOCUMENT:")
print("-" * 40)
print("PRE-TEXT:")
print(test_record["doc"]["pre_text"])
print("\nTABLE:")
for row_name, row_data in test_record["doc"]["table"].items():
    print(f"  {row_name}: {row_data}")
print("\nPOST-TEXT:")
print(test_record["doc"]["post_text"] or "(none)")

print("\n\n💬 QUESTIONS (try to answer before looking at gold):")
print("-" * 40)
for i, q in enumerate(test_record["dialogue"]["conv_questions"]):
    print(f"\nQ{i+1}: {q}")
    input("  Your answer: ")  # Interactive in Jupyter

print("\n\n🎯 GOLD ANSWERS:")
print("-" * 40)
for i, (q, a, exe) in enumerate(zip(
    test_record["dialogue"]["conv_questions"],
    test_record["dialogue"]["conv_answers"],
    test_record["dialogue"]["executed_answers"]
)):
    print(f"Q{i+1}: {q}")
    print(f"  → {a} (executed: {exe})")

# %% [markdown]
# ## Statistics

# %%
# Compute some statistics
all_records = data["train"] + data["dev"]

total_questions = sum(r["features"]["num_dialogue_turns"] for r in all_records)
type2_count = sum(1 for r in all_records if r["features"]["has_type2_question"])
avg_turns = total_questions / len(all_records)

doc_lengths = [
    len(r["doc"]["pre_text"]) + len(r["doc"]["post_text"])
    for r in all_records
]

print("DATASET STATISTICS:")
print("-" * 40)
print(f"Total records: {len(all_records)}")
print(f"Total questions: {total_questions}")
print(f"Average turns per conversation: {avg_turns:.1f}")
print(f"Type II (hybrid) conversations: {type2_count} ({100*type2_count/len(all_records):.1f}%)")
print(f"Document text length - min: {min(doc_lengths)}, max: {max(doc_lengths)}, avg: {sum(doc_lengths)/len(doc_lengths):.0f}")

# %% [markdown]
# ## Answer Format Analysis
#
# Understanding what format the answers take helps design the evaluation.

# %%
# Analyze answer formats
numeric_absolute = 0
numeric_ratio = 0  # Values between -2 and 2 (likely percentages/ratios)
negative_count = 0
text_answers = 0
total_answers = 0

sample_ratios = []
sample_absolutes = []

for record in all_records:
    for ans in record["dialogue"]["executed_answers"]:
        total_answers += 1
        if isinstance(ans, (int, float)):
            if ans < 0:
                negative_count += 1
            if -2 < ans < 2:
                numeric_ratio += 1
                sample_ratios.append(ans)
            else:
                numeric_absolute += 1
                sample_absolutes.append(ans)
        else:
            print("non-numeric answer: ", ans)
            text_answers += 1

print("ANSWER FORMAT ANALYSIS:")
print("-" * 40)
print(f"Total answers: {total_answers}")
print(f"Numeric (absolute, >2 or <-2): {numeric_absolute} ({100*numeric_absolute/total_answers:.1f}%)")
print(f"Numeric (ratio/percent, -2 to 2): {numeric_ratio} ({100*numeric_ratio/total_answers:.1f}%)")
print(f"Negative values: {negative_count} ({100*negative_count/total_answers:.1f}%)")
print(f"Non-numeric: {text_answers} ({100*text_answers/total_answers:.1f}%)")

print("\n📊 IMPLICATION FOR EVALUATION:")
print(f"  • {100*(numeric_absolute+numeric_ratio)/total_answers:.0f}% of answers are numeric")
print(f"  • {100*numeric_ratio/total_answers:.0f}% are ratios/percentages (need format handling)")
print(f"  • {100*negative_count/total_answers:.0f}% are negative (watch for sign errors)")

# %%
# Sample some ratio answers to see patterns
print("\nSAMPLE RATIO ANSWERS (likely percentages):")
for ans in sample_ratios[:10]:
    print(f"  {ans} → as percent: {ans*100:.2f}%")

print("\nSAMPLE ABSOLUTE ANSWERS:")
for ans in sample_absolutes[:10]:
    print(f"  {ans}")

