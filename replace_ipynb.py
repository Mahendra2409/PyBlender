import json

with open(r'm:\Order-to-PC\PyBlender\Colormap_Catloge_Website\Script\gcs_to_drive_transfer.ipynb', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace("pyblender-e37593034bc1.json", "gcs_service_account.json")
content = content.replace("pyblender.json", "gcs_service_account.json")

with open(r'm:\Order-to-PC\PyBlender\Colormap_Catloge_Website\Script\gcs_to_drive_transfer.ipynb', 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated gcs_to_drive_transfer.ipynb")
