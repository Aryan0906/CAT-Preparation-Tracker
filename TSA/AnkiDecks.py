# Since `genanki` is not available in this environment, I will create CSV files instead.
# These can be easily imported into Anki.

import pandas as pd
import os

# Create data for Quant deck
quant_data = {
    "Front": [
        "Time & Work: Combined Work Rate",
        "Speed, Time & Distance",
        "Profit & Loss",
        "Averages",
        "Simple Interest"
    ],
    "Back": [
        "Work = (A * B) / (A + B) if A and B work together.",
        "Distance = Speed × Time.",
        "Profit% = (Profit / Cost Price) * 100",
        "Average = Sum of Observations / Number of Observations",
        "SI = (P × R × T) / 100"
    ]
}

# Create data for Vocab deck
vocab_data = {
    "Front": [
        "Ephemeral",
        "Ambivalent",
        "Erudite",
        "Obfuscate",
        "Ubiquitous"
    ],
    "Back": [
        "Lasting for a very short time<br><i>Example:</i> The joy of winning was ephemeral.",
        "Having mixed feelings<br><i>Example:</i> He felt ambivalent about moving to a new city.",
        "Having or showing great knowledge<br><i>Example:</i> The professor was known for his erudite lectures.",
        "To make unclear<br><i>Example:</i> The company tried to obfuscate its financial results.",
        "Present everywhere<br><i>Example:</i> Smartphones have become ubiquitous in modern society."
    ]
}

# Create DataFrames
quant_df = pd.DataFrame(quant_data)
vocab_df = pd.DataFrame(vocab_data)

# Create output directory if it doesn't exist
output_dir = "anki_decks"
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# Save as CSVs for Anki import
quant_csv_path = os.path.join(output_dir, "CAT_Quant_Formulas.csv")
vocab_csv_path = os.path.join(output_dir, "CAT_Vocab_Builder.csv")

quant_df.to_csv(quant_csv_path, index=False)
vocab_df.to_csv(vocab_csv_path, index=False)

print(f"Files saved successfully:")
print(f"1. {quant_csv_path}")
print(f"2. {vocab_csv_path}")
