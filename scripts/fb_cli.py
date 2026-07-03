#!/usr/bin/env python3
"""
File Browser CLI - Upload images and create public share links.

Usage:
    python fb_cli.py upload <local_path> [remote_path]
    python fb_cli.py share <file_path> [--expire-days 900]
    python fb_cli.py upload-and-share <local_path> [remote_path] [--expire-days 900]

Examples:
    python fb_cli.py upload ./image.jpg blog/images/
    python fb_cli.py share /blog/images/image.jpg --expire-days 365
    python fb_cli.py upload-and-share ./image.jpg blog/images/ --expire-days 900
"""

import argparse
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import requests

# Configuration from environment
FILEBROWSER_URL = os.getenv('FILEBROWSER_URL', 'https://files.sebastianmorales.sbs')
FILEBROWSER_USER = os.getenv('FILEBROWSER_USER', 'sebas')
FILEBROWSER_PASS = os.getenv('FILEBROWSER_PASS', '')


def login() -> str:
    """Get JWT token from File Browser."""
    resp = requests.post(
        f'{FILEBROWSER_URL}/api/login',
        json={'username': FILEBROWSER_USER, 'password': FILEBROWSER_PASS},
        timeout=10,
    )
    resp.raise_for_status()
    return resp.text.strip().strip('"')


def upload_file(token: str, local_path: str, remote_path: str) -> dict:
    """Upload a file to File Browser."""
    with open(local_path, 'rb') as f:
        resp = requests.put(
            f'{FILEBROWSER_URL}/api/resources/{remote_path}',
            headers={'X-Auth': token},
            data=f,
            timeout=120,
        )
    resp.raise_for_status()
    try:
        return resp.json()
    except:
        return {'path': remote_path, 'status': resp.status_code}


def create_share(token: str, file_path: str, expire_days: int = 900) -> dict:
    """Create a public share link for a file.
    
    Note: File Browser shares may have issues with path handling.
    For public image hosting, use Pollinations.ai URLs directly.
    This function is kept for local storage/backup purposes.
    """
    # Create share with expiration in days (as string)
    resp = requests.post(
        f'{FILEBROWSER_URL}/api/shares',
        headers={
            'X-Auth': token,
            'Content-Type': 'application/json',
        },
        json={
            'path': file_path,
            'type': 'file',
            'expires': str(expire_days),  # Days as string
            'password': '',  # No password
            'units': 0,  # 0 = unlimited downloads
        },
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()


def get_pollinations_url(prompt: str, width: int = 1200, height: int = 675) -> str:
    """Get a Pollinations.ai URL for image generation.
    
    This is the recommended way to get public image URLs for the blog.
    Pollinations.ai is free and doesn't require an API key.
    """
    import urllib.parse
    encoded_prompt = urllib.parse.quote(prompt)
    return f'https://image.pollinations.ai/prompt/{encoded_prompt}?width={width}&height={height}&model=flux&nologo=true'


def get_share_url(share_data: dict) -> str:
    """Get the public URL from share data."""
    share_hash = share_data.get('hash', '')
    return f'{FILEBROWSER_URL}/public/dl/{share_hash}'


def main():
    parser = argparse.ArgumentParser(
        description='File Browser CLI - Upload and share files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Upload command
    upload_parser = subparsers.add_parser('upload', help='Upload a file')
    upload_parser.add_argument('local_path', help='Local file path')
    upload_parser.add_argument('remote_path', help='Remote path in File Browser')
    
    # Share command
    share_parser = subparsers.add_parser('share', help='Create share link')
    share_parser.add_argument('file_path', help='File path in File Browser')
    share_parser.add_argument('--expire-days', type=int, default=900, help='Expiration days (default: 900)')
    
    # Upload and share command
    upload_share_parser = subparsers.add_parser('upload-and-share', help='Upload and create share')
    upload_share_parser.add_argument('local_path', help='Local file path')
    upload_share_parser.add_argument('remote_path', help='Remote path in File Browser')
    upload_share_parser.add_argument('--expire-days', type=int, default=900, help='Expiration days (default: 900)')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List files or shares')
    list_parser.add_argument('--path', default='/', help='Path to list')
    list_parser.add_argument('--shares', action='store_true', help='List shares instead of files')
    
    # Pollinations URL command
    pollinations_parser = subparsers.add_parser('pollinations-url', help='Get Pollinations.ai URL for image')
    pollinations_parser.add_argument('prompt', help='Image prompt')
    pollinations_parser.add_argument('--width', type=int, default=1200, help='Image width (default: 1200)')
    pollinations_parser.add_argument('--height', type=int, default=675, help='Image height (default: 675)')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    try:
        if args.command == 'pollinations-url':
            # Pollinations URL doesn't need authentication
            url = get_pollinations_url(args.prompt, args.width, args.height)
            print(f'Pollinations URL: {url}')
            return
        
        token = login()
        print(f'✓ Logged in to File Browser')
        
        if args.command == 'upload':
            result = upload_file(token, args.local_path, args.remote_path)
            print(f'✓ Uploaded {args.local_path} → {result.get("path")}')
            print(json.dumps(result, indent=2))
        
        elif args.command == 'share':
            result = create_share(token, args.file_path, args.expire_days)
            url = get_share_url(result)
            print(f'✓ Created share link (expires in {args.expire_days} days)')
            print(f'URL: {url}')
            print(json.dumps(result, indent=2))
        
        elif args.command == 'upload-and-share':
            # Upload first
            result = upload_file(token, args.local_path, args.remote_path)
            remote_path = result.get('path', args.remote_path)
            print(f'✓ Uploaded {args.local_path} → {remote_path}')
            
            # Then share
            share_result = create_share(token, remote_path, args.expire_days)
            url = get_share_url(share_result)
            print(f'✓ Created share link (expires in {args.expire_days} days)')
            print(f'URL: {url}')
            print(json.dumps(share_result, indent=2))
        
        elif args.command == 'list':
            if args.shares:
                resp = requests.get(
                    f'{FILEBROWSER_URL}/api/shares',
                    headers={'X-Auth': token},
                    timeout=10,
                )
                resp.raise_for_status()
                data = resp.json()
                print(f'Found {len(data)} shares:')
                print(json.dumps(data, indent=2))
            else:
                resp = requests.get(
                    f'{FILEBROWSER_URL}/api/resources/{args.path}',
                    headers={'X-Auth': token},
                    timeout=10,
                )
                resp.raise_for_status()
                data = resp.json()
                items = data.get('items', [])
                print(f'Found {len(items)} items:')
                for item in items[:20]:
                    print(f'  {item.get("name")} ({item.get("size", 0)} bytes)')
    
    except requests.exceptions.RequestException as e:
        print(f'✗ Error: {e}', file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f'✗ Error: {e}', file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
