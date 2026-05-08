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

GCS_KEY_PATH = '/tmp/pyblender-e37593034bc1.json'

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


# %% ==================== CELL 4: Transfer All Files (FAST) ====================
import os
import time
import shutil
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from google.cloud import storage
from collections import defaultdict

# ─── Configuration ───────────────────────────────────────────
GCS_KEY_PATH = '/tmp/pyblender-e37593034bc1.json'
BUCKET_NAME = 'pyblender-render-farm'
GCS_BASE_PATH = 'RenderImages'  # Root prefix in the bucket
DRIVE_BASE_PATH = '/content/drive/MyDrive/PyBlender/Compare'
LOCAL_TEMP_DIR = '/content/temp_gcs_download'  # Fast local SSD staging area

# Set True to re-download files that already exist on Drive
FORCE_OVERWRITE = False

# Concurrent download threads (GCS is network-bound, more threads = faster)
MAX_WORKERS = 32
# ─────────────────────────────────────────────────────────────

def sizeof_fmt(num_bytes):
    """Human-readable file size."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if abs(num_bytes) < 1024.0:
            return f"{num_bytes:.1f} {unit}"
        num_bytes /= 1024.0
    return f"{num_bytes:.1f} TB"


# Thread-safe progress counter
class ProgressTracker:
    def __init__(self, total):
        self.total = total
        self.transferred = 0
        self.skipped = 0
        self.failed = 0
        self.bytes_transferred = 0
        self.lock = threading.Lock()
        self.failed_files = []
        self.start_time = time.time()

    def record_transfer(self, size):
        with self.lock:
            self.transferred += 1
            self.bytes_transferred += size
            self._maybe_print()

    def record_skip(self):
        with self.lock:
            self.skipped += 1
            self._maybe_print()

    def record_fail(self, path, error):
        with self.lock:
            self.failed += 1
            self.failed_files.append((path, error))
            print(f"   ✗ FAILED: {path} — {error}")

    def _maybe_print(self):
        done = self.transferred + self.skipped + self.failed
        if done % 50 == 0 or done == self.total:
            elapsed = time.time() - self.start_time
            rate = self.transferred / elapsed if elapsed > 0 else 0
            remaining = self.total - done
            eta = remaining / rate if rate > 0 else 0
            print(
                f"   [{done}/{self.total}] "
                f"✓ {self.transferred} downloaded, ⏭ {self.skipped} skipped, ✗ {self.failed} failed "
                f"| {sizeof_fmt(self.bytes_transferred)} | {rate:.1f} files/s | ETA: {eta:.0f}s"
            )


def download_blob(blob, local_path, drive_path, tracker):
    """Download a single blob to local SSD (called by thread pool)."""
    relative_path = blob.name[len(GCS_BASE_PATH) + 1:]

    # Skip if already on Drive (unless overwrite)
    if not FORCE_OVERWRITE and os.path.exists(drive_path):
        tracker.record_skip()
        return

    try:
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        blob.download_to_filename(local_path)
        tracker.record_transfer(blob.size or 0)
    except Exception as e:
        tracker.record_fail(relative_path, str(e))


def transfer_gcs_to_drive():
    """
    FAST transfer: GCS → Local SSD (concurrent) → Drive (batch copy).
    
    Why two steps?
      - GCS → Local SSD: Network-bound, parallelizable with 32 threads
      - Local SSD → Drive: FUSE mount has per-file overhead, but
        shutil.copytree is still much faster than downloading over
        network directly to the FUSE mount
    """

    # ── 1. Connect to GCS ────────────────────────────────────
    print("🔗 Connecting to GCS...")
    client = storage.Client.from_service_account_json(GCS_KEY_PATH)
    bucket = client.bucket(BUCKET_NAME)

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

    # ── 4. Prepare local staging directory ───────────────────
    if os.path.exists(LOCAL_TEMP_DIR):
        shutil.rmtree(LOCAL_TEMP_DIR)
    os.makedirs(LOCAL_TEMP_DIR, exist_ok=True)
    os.makedirs(DRIVE_BASE_PATH, exist_ok=True)

    # ── 5. PHASE 1: Concurrent download GCS → Local SSD ─────
    print(f"\n🚀 PHASE 1: Downloading from GCS → local SSD ({MAX_WORKERS} threads)...\n")

    tracker = ProgressTracker(len(all_blobs))

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = []
        for blob in all_blobs:
            relative_path = blob.name[len(GCS_BASE_PATH) + 1:]
            local_path = os.path.join(LOCAL_TEMP_DIR, relative_path)
            drive_path = os.path.join(DRIVE_BASE_PATH, relative_path)
            futures.append(
                executor.submit(download_blob, blob, local_path, drive_path, tracker)
            )

        # Wait for all downloads to complete
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f"   ✗ Unexpected thread error: {e}")

    phase1_elapsed = time.time() - tracker.start_time
    print(f"\n   Phase 1 done: {tracker.transferred} files downloaded in {phase1_elapsed:.1f}s")

    if tracker.transferred == 0:
        print("   Nothing new to copy to Drive (all files skipped or failed).")
        shutil.rmtree(LOCAL_TEMP_DIR, ignore_errors=True)
        return tracker.transferred, tracker.skipped, tracker.failed

    # ── 6. PHASE 2: Batch copy Local SSD → Drive ────────────
    print(f"\n📦 PHASE 2: Copying {tracker.transferred} files to Google Drive...")
    phase2_start = time.time()

    copied = 0
    copy_failed = 0
    for root, dirs, files in os.walk(LOCAL_TEMP_DIR):
        for f in files:
            src = os.path.join(root, f)
            relative = os.path.relpath(src, LOCAL_TEMP_DIR)
            dst = os.path.join(DRIVE_BASE_PATH, relative)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            try:
                shutil.copy2(src, dst)
                copied += 1
                if copied % 100 == 0:
                    print(f"   Copied {copied}/{tracker.transferred} files to Drive...")
            except Exception as e:
                copy_failed += 1
                print(f"   ✗ Copy failed: {relative} — {e}")

    phase2_elapsed = time.time() - phase2_start
    print(f"   Phase 2 done: {copied} files copied in {phase2_elapsed:.1f}s")

    # ── 7. Cleanup local temp ────────────────────────────────
    shutil.rmtree(LOCAL_TEMP_DIR, ignore_errors=True)

    # ── 8. Summary ───────────────────────────────────────────
    total_elapsed = time.time() - tracker.start_time
    sep = '=' * 60
    print(f"\n{sep}")
    print(f"✅ TRANSFER COMPLETE")
    print(f"{sep}")
    print(f"   Downloaded  : {tracker.transferred} files ({sizeof_fmt(tracker.bytes_transferred)})")
    print(f"   Copied      : {copied} files to Drive")
    print(f"   Skipped     : {tracker.skipped} files (already on Drive)")
    print(f"   Failed      : {tracker.failed} download + {copy_failed} copy failures")
    print(f"   Phase 1     : {phase1_elapsed:.1f}s (GCS → local, {MAX_WORKERS} threads)")
    print(f"   Phase 2     : {phase2_elapsed:.1f}s (local → Drive)")
    print(f"   Total time  : {total_elapsed:.1f}s ({total_elapsed/60:.1f} min)")
    if total_elapsed > 0 and tracker.transferred > 0:
        print(f"   Avg speed   : {tracker.transferred/total_elapsed:.1f} files/s")
    print(f"   Drive path  : {DRIVE_BASE_PATH}")
    print(f"{sep}")

    if tracker.failed_files:
        print(f"\n⚠ Failed downloads:")
        for path, error in tracker.failed_files:
            print(f"   • {path}: {error}")

    return tracker.transferred, tracker.skipped, tracker.failed


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

GCS_KEY_PATH = '/tmp/pyblender-e37593034bc1.json'
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
