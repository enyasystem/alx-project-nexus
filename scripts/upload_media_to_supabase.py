"""Upload local mediafiles to a Supabase Storage bucket preserving directory structure.

Usage:
  Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY in your shell (service role key for uploads).
  Then run:
    python scripts/upload_media_to_supabase.py --bucket your-bucket-name --local-dir mediafiles

This script requires the 'supabase' Python package: pip install supabase

It will upload files and print a few sample public URLs. For public access, ensure the bucket is public
or use signed URLs (this script prints public URLs for public buckets).
"""
import os
import sys
import argparse
from pathlib import Path

try:
    from supabase import create_client
except Exception as e:
    print("supabase package is required. Install with: pip install supabase")
    raise


def upload_dir(supabase_url, supabase_key, bucket, local_dir):
    client = create_client(supabase_url, supabase_key)
    base = Path(local_dir)
    uploaded = []
    for root, dirs, files in os.walk(base):
        for fname in files:
            local_path = Path(root) / fname
            rel_path = str(local_path.relative_to(base)).replace('\\', '/')
            dest_path = rel_path  # keep same relative path in bucket
            print(f"Uploading {local_path} -> {dest_path}")
            with open(local_path, 'rb') as f:
                data = f.read()
            try:
                res = client.storage.from_(bucket).upload(dest_path, data)
            except Exception as e:
                print(f"Failed to upload {local_path}: {e}")
                continue
            uploaded.append(dest_path)
    return uploaded


def print_sample_urls(supabase_url, bucket, paths, sample=10):
    base = f"{supabase_url}/storage/v1/object/public/{bucket}"
    print('\nSample public URLs:')
    for p in paths[:sample]:
        print(f"{base}/{p}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--bucket', required=True, help='Supabase storage bucket name')
    parser.add_argument('--local-dir', default='mediafiles', help='Local media directory to upload')
    args = parser.parse_args()

    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    if not supabase_url or not supabase_key:
        print('Please set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY in your environment')
        return 2

    paths = upload_dir(supabase_url, supabase_key, args.bucket, args.local_dir)
    if not paths:
        print('No files uploaded')
        return 1
    print_sample_urls(supabase_url, args.bucket, paths)
    print('\nDone.')
    return 0


if __name__ == '__main__':
    rc = main()
    sys.exit(rc)
