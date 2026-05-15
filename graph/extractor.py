import fitz
import re

# Input PDF
pdf_path = "../raw/Apple-Supply-Chain-2025-Progress-Report.pdf"

# Output cleaned text
output_path = "../raw/cleaned_apple_supply_chain.txt"

# Open PDF
doc = fitz.open(pdf_path)

all_text = []

for page in doc:
    text = page.get_text()

    # Remove excessive whitespace
    text = re.sub(r"\s+", " ", text)

    # Remove weird unicode artifacts
    text = text.encode("ascii", "ignore").decode()

    # Remove repeated tiny fragments
    if len(text.strip()) > 100:
        all_text.append(text)

# Combine everything
final_text = "\n\n".join(all_text)

# Save cleaned text
with open(output_path, "w", encoding="utf-8") as f:
    f.write(final_text)

print("Cleaned text extracted successfully.")
print(f"Saved to: {output_path}")