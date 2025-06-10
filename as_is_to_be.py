import os
import csv

csv_path = "./files_to_send.csv"

def rename_files_with_csv(csv_path):
    directory = "files_to_send"

    if not os.path.exists(csv_path):
        print(f"Error: CSV file '{csv_path}' does not exist.")
        return

    if not os.path.exists(directory):
        print(f"Error: Directory '{directory}' does not exist.")
        return

    id_mapping = {}
    try:
        with open(csv_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)

            if 'ID' not in reader.fieldnames or 'EXTERNAL_ID' not in reader.fieldnames:
                print("Error: CSV must contain 'ID' and 'EXTERNAL_ID' columns.")
                return

            for row in reader:
                external_id = row['EXTERNAL_ID'].strip()
                new_id = row['ID'].strip()
                id_mapping[external_id] = new_id
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return

    successful_renames = 0
    skipped_files = 0
    errors = 0

    for filename in os.listdir(directory):
        try:
            base_name = os.path.splitext(filename)[0]
            file_extension = os.path.splitext(filename)[1]

            if base_name in id_mapping:
                new_filename = id_mapping[base_name] + file_extension

                old_path = os.path.join(directory, filename)
                new_path = os.path.join(directory, new_filename)

                os.rename(old_path, new_path)

                print(f"Renamed: {filename} → {new_filename}")
                successful_renames += 1
            else:
                print(f"Skipped: {filename} (no matching EXTERNAL_ID found)")
                skipped_files += 1

        except Exception as e:
            print(f"Error renaming {filename}: {e}")
            errors += 1

    print("\nRename Summary:")
    print(f"Successful renames: {successful_renames}")
    print(f"Skipped files: {skipped_files}")
    print(f"Errors: {errors}")

rename_files_with_csv(csv_path)