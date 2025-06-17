import gdown
import zipfile
import os
import re

def download_and_unzip_from_gdrive(link):
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    print(script_dir)

    # Extract file ID from the link
    match = re.search(r'/d/([a-zA-Z0-9_-]+)', link)
    if not match:
        raise ValueError("❌ Invalid Google Drive link format. Expected format: https://drive.google.com/file/d/FILE_ID/view")

    file_id = match.group(1)

    # Set the download path
    output_zip = os.path.join(script_dir, "downloaded_file.zip")

    # Download the file
    print(f"📥 Downloading zip file from Google Drive (ID: {file_id})...")
    gdown.download(id=file_id, output=output_zip, quiet=False)

    # Unzip it in the same directory
    print(f"📦 Extracting to: {script_dir}")
    with zipfile.ZipFile(output_zip, 'r') as zip_ref:
        zip_ref.extractall(script_dir)

    print("✅ Done! Files extracted.")
    os.remove(output_zip)  # Optional: clean up zip file

# Example usage
if __name__ == "__main__":
    google_drive_link = "https://drive.google.com/file/d/1-Je6lepAuIfM9C5AhRyYJuf86TkigIIX/view?usp=drive_link"
    download_and_unzip_from_gdrive(google_drive_link)
