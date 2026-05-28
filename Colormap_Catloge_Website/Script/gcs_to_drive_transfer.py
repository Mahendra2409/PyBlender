# ============================================================
# GCS → Google Drive Transfer Script (Google Colab)
# ============================================================
# This script transfers all rendered images from the GCS bucket
# to Google Drive. Run each section as a separate Colab cell.
#
# GCS Bucket : pyblender-render-farm (service account auth)
# Drive Target: MyDrive/PyBlender/Compare/<PC_TYPE>/<colormap>/
# ============================================================


# %% ==================== CELL 1: Mount Google Drive ====================
from google.colab import drive
drive.mount('/content/drive')


# %% ==================== CELL 2: Install Dependencies ====================
# !pip install -q google-cloud-storage


# %% ==================== CELL 3: Load Service Account Key ====================
# Load the GCS service account JSON key from Colab Secrets
from google.colab import userdata
import os

GCS_KEY_PATH = '/tmp/gcs_service_account.json'

# Check if key already exists (from previous cell run)
if os.path.exists(GCS_KEY_PATH):
    print(f"✓ Key already exists at {GCS_KEY_PATH}")
else:
    try:
        # Get the secret named 'GCS_SERVICE_ACCOUNT_KEY'
        key_content = userdata.get('GCS_SERVICE_ACCOUNT_KEY')
        with open(GCS_KEY_PATH, 'w') as f:
            f.write(key_content)
        print(f"✓ Saved secret to {GCS_KEY_PATH}")
    except userdata.SecretNotFoundError:
        print("✗ Secret 'GCS_SERVICE_ACCOUNT_KEY' not found!")
        print("Please add it to the 'Secrets' tab (key icon) on the left sidebar.")


# %% ==================== CELL 4: Transfer All Files ====================
import os
import time
import shutil
from google.cloud import storage
from collections import defaultdict

# ─── Configuration ───────────────────────────────────────────
GCS_KEY_PATH = '/tmp/gcs_service_account.json'
BUCKET_NAME = 'pyblender-render-farm'
GCS_BASE_PATH = 'RenderImages'  # Root prefix in the bucket
DRIVE_BASE_PATH = '/content/drive/MyDrive/PyBlender/Compare'

# Set True to re-download files that already exist on Drive
FORCE_OVERWRITE = False

# Batch size for progress reporting
PROGRESS_INTERVAL = 25
# ─────────────────────────────────────────────────────────────

def sizeof_fmt(num_bytes):
    """Human-readable file size."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if abs(num_bytes) < 1024.0:
            return f"{num_bytes:.1f} {unit}"
        num_bytes /= 1024.0
    return f"{num_bytes:.1f} TB"


def transfer_gcs_to_drive():
    """Main transfer function: GCS bucket → Google Drive."""
    
    # ── 1. Connect to GCS ────────────────────────────────────
    print("🔗 Connecting to GCS...")
    client = storage.Client.from_service_account_json(GCS_KEY_PATH)
    bucket = client.bucket(BUCKET_NAME)
    
    # Verify bucket access
    try:
        next(bucket.list_blobs(max_results=1, prefix=GCS_BASE_PATH + '/'))
        print(f"✓ Connected to bucket: {BUCKET_NAME}")
    except StopIteration:
        print(f"⚠ Bucket '{BUCKET_NAME}' is empty or prefix '{GCS_BASE_PATH}/' has no files")
        return
    except Exception as e:
        print(f"✗ Failed to access bucket: {e}")
        return
    
    # ── 2. List ALL blobs ────────────────────────────────────
    print(f"\n📋 Listing all files under gs://{BUCKET_NAME}/{GCS_BASE_PATH}/...")
    all_blobs = []
    total_size = 0
    
    for blob in bucket.list_blobs(prefix=GCS_BASE_PATH + '/'):
        # Skip "directory" markers
        if blob.name.endswith('/'):
            continue
        all_blobs.append(blob)
        total_size += blob.size or 0
    
    print(f"   Found {len(all_blobs)} files ({sizeof_fmt(total_size)})")
    
    if not all_blobs:
        print("Nothing to transfer!")
        return
    
    # ── 3. Analyze structure ─────────────────────────────────
    pc_types = defaultdict(lambda: defaultdict(int))
    for blob in all_blobs:
        parts = blob.name[len(GCS_BASE_PATH) + 1:].split('/')
        if len(parts) >= 2:
            pc_types[parts[0]][parts[1]] += 1
    
    print(f"\n📂 Point Cloud Types found:")
    for pc_type, colormaps in sorted(pc_types.items()):
        total_files = sum(colormaps.values())
        print(f"   ├── {pc_type}: {len(colormaps)} colormaps, {total_files} files")
    
    # ── 4. Ensure Drive base directory exists ────────────────
    os.makedirs(DRIVE_BASE_PATH, exist_ok=True)
    print(f"\n📁 Drive target: {DRIVE_BASE_PATH}")
    
    # ── 5. Transfer files ────────────────────────────────────
    print(f"\n🚀 Starting transfer...\n")
    
    transferred = 0
    skipped = 0
    failed = 0
    bytes_transferred = 0
    start_time = time.time()
    failed_files = []
    
    for i, blob in enumerate(all_blobs):
        # Build relative path: RenderImages/PC_TYPE/cmap/file.png → PC_TYPE/cmap/file.png
        relative_path = blob.name[len(GCS_BASE_PATH) + 1:]
        drive_path = os.path.join(DRIVE_BASE_PATH, relative_path)
        
        # Skip if already exists (unless FORCE_OVERWRITE)
        if not FORCE_OVERWRITE and os.path.exists(drive_path):
            skipped += 1
            continue
        
        # Create directory structure on Drive
        os.makedirs(os.path.dirname(drive_path), exist_ok=True)
        
        try:
            # Download directly to Drive mount
            blob.download_to_filename(drive_path)
            transferred += 1
            bytes_transferred += blob.size or 0
            
        except Exception as e:
            failed += 1
            failed_files.append((relative_path, str(e)))
            print(f"   ✗ FAILED: {relative_path} — {e}")
            continue
        
        # Progress reporting
        done = transferred + skipped + failed
        if done % PROGRESS_INTERVAL == 0 or done == len(all_blobs):
            elapsed = time.time() - start_time
            rate = transferred / elapsed if elapsed > 0 else 0
            eta = (len(all_blobs) - done) / rate if rate > 0 else 0
            print(
                f"   [{done}/{len(all_blobs)}] "
                f"✓ {transferred} transferred, ⏭ {skipped} skipped, ✗ {failed} failed "
                f"| {sizeof_fmt(bytes_transferred)} | {rate:.1f} files/s | ETA: {eta:.0f}s"
            )
    
    # ── 6. Summary ───────────────────────────────────────────
    elapsed = time.time() - start_time
    print(f"\n{'='*60}")
    print(f"✅ TRANSFER COMPLETE")
    print(f"{'='*60}")
    print(f"   Transferred : {transferred} files ({sizeof_fmt(bytes_transferred)})")
    print(f"   Skipped     : {skipped} files (already on Drive)")
    print(f"   Failed      : {failed} files")
    print(f"   Total time  : {elapsed:.1f}s ({elapsed/60:.1f} min)")
    print(f"   Avg speed   : {transferred/elapsed:.1f} files/s" if elapsed > 0 else "")
    print(f"   Drive path  : {DRIVE_BASE_PATH}")
    print(f"{'='*60}")
    
    if failed_files:
        print(f"\n⚠ Failed files:")
        for path, error in failed_files:
            print(f"   • {path}: {error}")
    
    return transferred, skipped, failed


# Run the transfer
transfer_gcs_to_drive()


# %% ==================== CELL 5: Verify Transfer ====================
import os
from collections import defaultdict

DRIVE_BASE_PATH = '/content/drive/MyDrive/PyBlender/Compare'

print("🔍 Verifying Drive contents...\n")

stats = defaultdict(lambda: defaultdict(int))
total_files = 0
total_size = 0

for root, dirs, files in os.walk(DRIVE_BASE_PATH):
    for f in files:
        fpath = os.path.join(root, f)
        rel = os.path.relpath(fpath, DRIVE_BASE_PATH)
        parts = rel.split(os.sep)
        if len(parts) >= 2:
            stats[parts[0]][parts[1]] += 1
        total_files += 1
        total_size += os.path.getsize(fpath)

print(f"📂 {DRIVE_BASE_PATH}")
print(f"   Total: {total_files} files ({total_size / (1024*1024):.1f} MB)\n")

for pc_type in sorted(stats):
    colormaps = stats[pc_type]
    files_count = sum(colormaps.values())
    print(f"   📁 {pc_type}/")
    print(f"      {len(colormaps)} colormap folders, {files_count} files")

print(f"\n✅ Verification complete!")


# %% ==================== CELL 6 (OPTIONAL): Cross-Check with Bucket ====================
# Run this cell to find any files in GCS that are NOT on Drive
import os
from google.cloud import storage

GCS_KEY_PATH = '/tmp/gcs_service_account.json'
BUCKET_NAME = 'pyblender-render-farm'
GCS_BASE_PATH = 'RenderImages'
DRIVE_BASE_PATH = '/content/drive/MyDrive/PyBlender/Compare'

client = storage.Client.from_service_account_json(GCS_KEY_PATH)
bucket = client.bucket(BUCKET_NAME)

missing = []
matched = 0

for blob in bucket.list_blobs(prefix=GCS_BASE_PATH + '/'):
    if blob.name.endswith('/'):
        continue
    relative_path = blob.name[len(GCS_BASE_PATH) + 1:]
    drive_path = os.path.join(DRIVE_BASE_PATH, relative_path)
    if os.path.exists(drive_path):
        matched += 1
    else:
        missing.append(relative_path)

print(f"✓ Matched on Drive: {matched}")
print(f"✗ Missing from Drive: {len(missing)}")

if missing:
    print(f"\nMissing files:")
    for m in missing[:50]:  # Show first 50
        print(f"   • {m}")
    if len(missing) > 50:
        print(f"   ... and {len(missing) - 50} more")
else:
    print(f"\n✅ ALL bucket files are present on Drive! Nothing left behind.")
