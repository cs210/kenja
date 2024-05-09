import csv


def filter_csv(input_file, output_file):
    with open(input_file, "r", newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        fieldnames = reader.fieldnames
        rows = [
            row
            for row in reader
            if "wanted" not in row["Title"].lower()
            and "wanted" not in row["Description"].lower()
        ]

    with open(output_file, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


if __name__ == "__main__":
    input_file = input("Path to input CSV: ")
    output_file = input("Output file path: ")
    filter_csv(input_file, output_file)
