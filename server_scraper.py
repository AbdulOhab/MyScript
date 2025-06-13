import os
import time
import random
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re

BASE_URL = "https://www.perspectivebd.com/"  # 🔁 এখানে আপনার আসল URL দিন
DOWNLOAD_DIR = "downloaded_site"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

visited_urls = set()  # URL পুনরাবৃত্তি এড়াতে

# এই ফোল্ডারগুলো এড়িয়ে যাওয়া হবে
EXCLUDED_FOLDERS = ['vendor', 'vendors', 'node_modules', 'assets/vendor', 'js/vendor', 'css/vendor', 'storage/logs','storage/framework', 'storage/debugbar',  ]

def sanitize_filename(filename):
    """ফাইলনেম থেকে অবৈধ ক্যারেক্টার সরানো"""
    # Windows/Linux এর জন্য অবৈধ ক্যারেক্টার সরানো
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # একাধিক ডট সরানো (শুধু শেষের এক্সটেনশন রাখা)
    if filename.count('.') > 1:
        parts = filename.split('.')
        filename = '_'.join(parts[:-1]) + '.' + parts[-1]
    return filename

def get_filename_from_url(url):
    """URL থেকে সঠিক ফাইলনেম বের করা"""
    parsed = urlparse(url)
    path = parsed.path
    
    # যদি পাথ '/' দিয়ে শেষ হয় তাহলে index.html ব্যবহার করুন
    if path.endswith('/') or path == '':
        return 'index.html'
    
    # ফাইলনেম বের করুন
    filename = os.path.basename(path)
    
    # যদি কোন এক্সটেনশন না থাকে এবং এটি একটি পেজ হয়, তাহলে .html যোগ করুন
    if '.' not in filename and not filename.endswith('/'):
        filename += '.html'
    
    return sanitize_filename(filename)

def create_directory_structure(url, base_dir):
    """URL অনুযায়ী ডিরেক্টরি স্ট্রাকচার তৈরি করা"""
    parsed = urlparse(url)
    path_parts = [part for part in parsed.path.split('/') if part]
    
    current_dir = base_dir
    # শেষ অংশ বাদে বাকি অংশগুলো ডিরেক্টরি হিসেবে তৈরি করুন
    for part in path_parts[:-1]:
        current_dir = os.path.join(current_dir, sanitize_filename(part))
        os.makedirs(current_dir, exist_ok=True)
    
    return current_dir

def download_file(url, dest_path):
    """একটি ফাইল ডাউনলোড করা"""
    try:
        print(f"⬇️ Downloading: {url}")
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        with open(dest_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print(f"✅ Downloaded: {dest_path}")
        return True
    except Exception as e:
        print(f"❌ Failed to download {url}: {e}")
        return False

def should_exclude_url(url):
    """URL টি এক্সক্লুড করা হবে কিনা চেক করা"""
    parsed = urlparse(url)
    path = parsed.path.lower()
    
    for excluded in EXCLUDED_FOLDERS:
        if f'/{excluded}/' in path or path.endswith(f'/{excluded}') or path.startswith(f'/{excluded}/'):
            return True
    return False

def download(url, dest_dir):
    """মূল ডাউনলোড ফাংশন"""
    # URL ইতিমধ্যে ভিজিট করা হয়েছে কিনা চেক করুন
    if url in visited_urls:
        return
    
    # vendor ফোল্ডার এড়িয়ে যান
    if should_exclude_url(url):
        print(f"⏭️ Skipping vendor folder: {url}")
        return
    
    visited_urls.add(url)
    print(f"🔍 Scanning: {url}")
    
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"❌ Error accessing {url}: {e}")
        return

    # HTML পেজ সেভ করুন
    dir_path = create_directory_structure(url, dest_dir)
    filename = get_filename_from_url(url)
    file_path = os.path.join(dir_path, filename)
    
    if not os.path.exists(file_path):
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(r.text)
            print(f"💾 Saved HTML: {file_path}")
        except Exception as e:
            print(f"❌ Failed to save HTML {url}: {e}")

    # HTML পার্স করুন এবং লিংক খুঁজুন
    soup = BeautifulSoup(r.text, "html.parser")
    
    # সব ধরনের রিসোর্স ডাউনলোড করুন
    resources = []
    
    # CSS ফাইল
    for link in soup.find_all('link', href=True):
        if link.get('rel') and 'stylesheet' in link.get('rel'):
            resources.append(link['href'])
    
    # JavaScript ফাইল
    for script in soup.find_all('script', src=True):
        resources.append(script['src'])
    
    # ছবি
    for img in soup.find_all('img', src=True):
        resources.append(img['src'])
    
    # অন্যান্য লিংক
    for link in soup.find_all('a', href=True):
        href = link['href']
        # শুধুমাত্র একই ডোমেইনের লিংক
        full_url = urljoin(url, href)
        if BASE_URL in full_url and full_url not in visited_urls:
            resources.append(href)
    
    # রিসোর্স ডাউনলোড করুন
    for resource in resources:
        if not resource or resource in ['/', '#', 'javascript:void(0)']:
            continue
            
        full_resource_url = urljoin(url, resource)
        
        # একই ডোমেইন চেক করুন
        if not full_resource_url.startswith(BASE_URL):
            continue
        
        # vendor ফোল্ডার এড়িয়ে যান
        if should_exclude_url(full_resource_url):
            print(f"⏭️ Skipping vendor resource: {full_resource_url}")
            continue
        
        # ফাইলের জন্য ডিরেক্টরি তৈরি করুন
        resource_dir = create_directory_structure(full_resource_url, dest_dir)
        resource_filename = get_filename_from_url(full_resource_url)
        resource_path = os.path.join(resource_dir, resource_filename)
        
        if not os.path.exists(resource_path):
            if download_file(full_resource_url, resource_path):
                # র‍্যান্ডম বিরতি
                delay = random.uniform(1.5, 4.0)
                print(f"⏱️ Sleeping for {delay:.2f} seconds...")
                time.sleep(delay)
        
        # যদি এটি একটি HTML পেজ হয়, তাহলে রিকার্সিভভাবে ডাউনলোড করুন
        if (resource_filename.endswith('.html') or 
            resource_filename == 'index.html' or 
            '.' not in resource_filename):
            download(full_resource_url, dest_dir)

# ডাউনলোড শুরু করুন
print(f"🚀 Starting download from: {BASE_URL}")
print(f"📁 Download directory: {DOWNLOAD_DIR}")
download(BASE_URL, DOWNLOAD_DIR)
print("🎉 Download completed!")