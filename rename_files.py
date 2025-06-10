import os

def rename_files_in_directory():
    directory = "files_to_send"

    if not os.path.exists(directory):
        print(f"Error: Directory '{directory}' does not exist.")
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

                print(f"Renamed: {filename} → {new_filename_with_ext}")
                successful_renames += 1
            else:
                print(f"Skipped: {filename} (no ' - ' found)")
                failed_renames += 1

        except Exception as e:
            print(f"Error renaming {filename}: {e}")
            failed_renames += 1

    print("\nRename Summary:")
    print(f"Successful renames: {successful_renames}")
    print(f"Skipped files: {failed_renames}")


rename_files_in_directory()
