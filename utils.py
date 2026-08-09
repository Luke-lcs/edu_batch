import os
import csv

from logging_config import get_logger

logger = get_logger()

def rename_files_in_directory(directory="files_to_send"):
    if not os.path.exists(directory):
        logger.error(f"Error: Directory '{directory}' does not exist.")
        return

    successful_renames = 0
    failed_renames = 0

    for filename in os.listdir(directory):
        try:
            parts = filename.split(" - ")

            if len(parts) > 1:
                new_filename = parts[0]
                file_extension = os.path.splitext(filename)[1]
                new_filename_with_ext = new_filename + file_extension
                old_path = os.path.join(directory, filename)
                new_path = os.path.join(directory, new_filename_with_ext)

                os.rename(old_path, new_path)
                logger.info(f"Renamed: {filename} -> {new_filename_with_ext}")
                successful_renames += 1
            else:
                logger.warning(f"Skipped: {filename} (no ' - ' found)")
                failed_renames += 1

        except Exception as e:
            logger.error(f"Error renaming {filename}: {e}")
            failed_renames += 1

    logger.info("Rename Summary:")
    logger.info(f"Successful renames: {successful_renames}")
    logger.info(f"Skipped files: {failed_renames}")

def rename_files_with_csv(csv_path="./files_to_send.csv", directory="files_to_send"):
    if not os.path.exists(csv_path):
        logger.error(f"Error: CSV file '{csv_path}' does not exist.")
        return

    if not os.path.exists(directory):
        logger.error(f"Error: Directory '{directory}' does not exist.")
        return

    id_mapping = {}
    try:
        with open(csv_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            if 'ID' not in reader.fieldnames or 'EXTERNAL_ID' not in reader.fieldnames:
                logger.error("Error: CSV must contain 'ID' and 'EXTERNAL_ID' columns.")
                return
            for row in reader:
                external_id = row['EXTERNAL_ID'].strip()
                new_id = row['ID'].strip()
                id_mapping[external_id] = new_id
    except Exception as e:
        logger.error(f"Error reading CSV file: {e}")
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
                logger.info(f"Renamed: {filename} -> {new_filename}")
                successful_renames += 1
            else:
                logger.warning(f"Skipped: {filename} (no matching EXTERNAL_ID found)")
                skipped_files += 1
        except Exception as e:
            logger.error(f"Error renaming {filename}: {e}")
            errors += 1

    logger.info("Rename Summary:")
    logger.info(f"Successful renames: {successful_renames}")
    logger.info(f"Skipped files: {skipped_files}")
    logger.error(f"Errors: {errors}")

def delete_sent_files(csv_filepath, folder_path, dry_run=False):
    student_ids = set()
    try:
        with open(csv_filepath, 'r', encoding='utf-8') as csvfile:
            csv_reader = csv.DictReader(csvfile)
            if "ID do Aluno" not in csv_reader.fieldnames:
                logger.error(f"CSV file is missing 'ID do Aluno' column. Available columns: {csv_reader.fieldnames}")
                return
            for row in csv_reader:
                student_id = row["ID do Aluno"].strip()
                if student_id:
                    student_ids.add(student_id)
        logger.info(f"Read {len(student_ids)} unique student IDs from CSV")
    except FileNotFoundError:
        logger.error(f"Error: CSV file '{csv_filepath}' not found.")
        return
    except Exception as e:
        logger.error(f"Error reading CSV file: {e}")
        return

    if not student_ids:
        logger.info("No valid student IDs found in the CSV. Exiting.")
        return

    if dry_run:
        logger.info("DRY RUN - No files will be deleted")
        logger.info("Files that would be deleted:")
        for filename in os.listdir(folder_path):
            file_id = os.path.splitext(filename)[0]
            if file_id in student_ids:
                logger.info(f"  - {filename}")
        return

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
                    if file_id in not_found_ids:
                        not_found_ids.remove(file_id)
                    logger.info(f"Deleted: {filename}")
                except Exception as e:
                    logger.error(f"Error deleting {filename}: {e}")

        logger.info("Summary:")
        logger.info(f"- Total student IDs in CSV: {len(student_ids)}")
        logger.info(f"- Files deleted: {len(deleted_files)}")
        if not_found_ids:
            logger.info(f"- Student IDs with no matching files: {len(not_found_ids)}")

    except FileNotFoundError:
        logger.error(f"Error: Folder '{folder_path}' not found.")
    except Exception as e:
        logger.error(f"Error processing files: {e}")
