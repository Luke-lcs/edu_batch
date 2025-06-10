import os
import csv
import glob
import argparse


def read_student_ids_from_csv(csv_filepath):
    student_ids = set()
    
    try:
        with open(csv_filepath, 'r', encoding='utf-8') as csvfile:
            csv_reader = csv.DictReader(csvfile)
            
            if "ID do Aluno" not in csv_reader.fieldnames:
                raise ValueError(f"CSV file is missing 'ID do Aluno' column. Available columns: {csv_reader.fieldnames}")
            
            for row in csv_reader:
                student_id = row["ID do Aluno"].strip()
                if student_id:
                    student_ids.add(student_id)
                    
        print(f"Read {len(student_ids)} unique student IDs from CSV")
        return student_ids
        
    except FileNotFoundError:
        print(f"Error: CSV file '{csv_filepath}' not found.")
        return set()
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return set()


def find_and_delete_files(student_ids, folder_path):
    deleted_files = []
    not_found_ids = set(student_ids)
    
    try:
        all_files = os.listdir(folder_path)
        
        for filename in all_files:
            file_path = os.path.join(folder_path, filename)
            
            if os.path.isdir(file_path):
                continue
                
            file_id = os.path.splitext(filename)[0]
            
            if file_id in student_ids:
                try:
                    os.remove(file_path)
                    deleted_files.append(filename)
                    not_found_ids.remove(file_id)
                    print(f"Deleted: {filename}")
                except Exception as e:
                    print(f"Error deleting {filename}: {e}")
        
        return deleted_files, not_found_ids
        
    except FileNotFoundError:
        print(f"Error: Folder '{folder_path}' not found.")
        return [], student_ids
    except Exception as e:
        print(f"Error processing files: {e}")
        return deleted_files, not_found_ids


def main():
    parser = argparse.ArgumentParser(description='Delete files based on student IDs from a CSV file.')
    parser.add_argument('--csv', default='/Users/lucas/Documents/edu_batch/src/Comunicados_Enviados.csv',
                        help='Path to the CSV file (default: /Users/lucas/Documents/edu_batch/src/Comunicados_Enviados.csv)')
    parser.add_argument('--folder', default='/Users/lucas/Documents/edu_batch/src/attachment_files',
                        help='Path to the folder containing files to check (default: /Users/lucas/Documents/edu_batch/src/attachment_files)')
    parser.add_argument('--dry-run', action='store_true',
                        help='Perform a dry run without actually deleting files')
    
    args = parser.parse_args()
    
    student_ids = read_student_ids_from_csv(args.csv)
    
    if not student_ids:
        print("No valid student IDs found in the CSV. Exiting.")
        return
    
    if args.dry_run:
        print("\nDRY RUN - No files will be deleted")
        
    if args.dry_run:
        print(f"\nFiles that would be deleted (if this wasn't a dry run):")
        for filename in os.listdir(args.folder):
            file_id = os.path.splitext(filename)[0]
            if file_id in student_ids:
                print(f"  - {filename}")
    else:
        deleted_files, not_found_ids = find_and_delete_files(student_ids, args.folder)
        
        print("\nSummary:")
        print(f"- Total student IDs in CSV: {len(student_ids)}")
        print(f"- Files deleted: {len(deleted_files)}")
        
        if not_found_ids:
            print(f"- Student IDs with no matching files: {len(not_found_ids)}")
            if len(not_found_ids) <= 10:
                print(f"  Missing IDs: {', '.join(sorted(not_found_ids))}")
            else:
                print(f"  First 10 missing IDs: {', '.join(sorted(list(not_found_ids)[:10]))}")


if __name__ == "__main__":
    main()
    