import os
import re
import json
from typing import Dict, Optional, List
from pathlib import Path
import pytesseract
import cv2
import numpy as np


def preprocess_image(image_path: str) -> np.ndarray:
    """Preprocess image for better OCR accuracy."""
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Could not load image: {image_path}")
    
    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Apply threshold to get black text on white background
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    # Denoise
    kernel = np.ones((1, 1), np.uint8)
    processed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
    
    return processed


def extract_text_from_image(image_path: str) -> str:
    """Extract text from citation image using OCR."""
    try:
        processed_img = preprocess_image(image_path)
        # Use specific OCR config for structured documents
        custom_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz.,/:() '
        text = pytesseract.image_to_string(processed_img, config=custom_config)
        return text.strip()
    except Exception as e:
        print(f"OCR failed for {image_path}: {e}")
        return ""


def parse_citation_data(ocr_text: str) -> Dict:
    """Parse structured data from OCR text."""
    data = {}
    
    # Citation number (from the beginning of text)
    citation_match = re.search(r'^(\d{8})', ocr_text)
    if citation_match:
        data['citation_number'] = citation_match.group(1)
    
    # Date
    date_match = re.search(r'DATE\s*:\s*(\d{2}/\d{2}/\d{4}\s+\d{1,2}:\d{2}\s*[AP]M)', ocr_text, re.IGNORECASE)
    if date_match:
        data['date'] = date_match.group(1)
    
    # Officer
    officer_match = re.search(r'OFFICER\s*:\s*([A-Z0-9\s]+)', ocr_text, re.IGNORECASE)
    if officer_match:
        data['officer'] = officer_match.group(1).strip()
    
    # Beat
    beat_match = re.search(r'BEAT\s*([A-Z0-9]+)', ocr_text, re.IGNORECASE)
    if beat_match:
        data['beat'] = beat_match.group(1).strip()
    
    # Vehicle info
    make_match = re.search(r'MAKE\s*:\s*([A-Z]+)', ocr_text, re.IGNORECASE)
    if make_match:
        data['make'] = make_match.group(1).strip()
    
    model_match = re.search(r'MODEL\s*:\s*([A-Z0-9/\s]+?)(?:\s+COLOR|$)', ocr_text, re.IGNORECASE)
    if model_match:
        data['model'] = model_match.group(1).strip()
    
    color_match = re.search(r'COLOR\s*:\s*([A-Z()]+)', ocr_text, re.IGNORECASE)
    if color_match:
        data['color'] = color_match.group(1).strip()
    
    # Plate info
    plate_match = re.search(r'PLATE/ST\s*:\s*([A-Z0-9]+)\s*/\s*([A-Z]{2})', ocr_text, re.IGNORECASE)
    if plate_match:
        data['plate'] = plate_match.group(1).strip()
        data['plate_state'] = plate_match.group(2).strip()
    
    plate_exp_match = re.search(r'PLATE\s*EXP\s*:\s*(\d+)\s*/\s*(\d{4})', ocr_text, re.IGNORECASE)
    if plate_exp_match:
        data['plate_exp_month'] = plate_exp_match.group(1).strip()
        data['plate_exp_year'] = plate_exp_match.group(2).strip()
    
    # Location info
    location_match = re.search(r'LOCATION\s*:\s*([A-Z0-9\s]+?)(?:\s+DISTRICT|\s+COMPLAINT|\s+VIOLATION|$)', ocr_text, re.IGNORECASE)
    if location_match:
        data['location'] = location_match.group(1).strip()
    
    district_match = re.search(r'DISTRICT\s*:\s*(\d+)', ocr_text, re.IGNORECASE)
    if district_match:
        data['district'] = district_match.group(1).strip()
    
    meter_match = re.search(r'METER\s*[#H]?\s*:\s*(\d+)', ocr_text, re.IGNORECASE)
    if meter_match:
        data['meter_number'] = meter_match.group(1).strip()
    
    # Violation
    violation_match = re.search(r'VIOLATION\(S\)\s*:\s*([A-Z0-9\s,.-]+)', ocr_text, re.IGNORECASE)
    if violation_match:
        data['violation'] = violation_match.group(1).strip()
    
    # Fine amount
    fine_match = re.search(r'FINE\s*AMOUNT\s*:\s*\$?(\d+\.?\d*)', ocr_text, re.IGNORECASE)
    if fine_match:
        data['fine_amount'] = float(fine_match.group(1))
    
    # Comments
    comments_match = re.search(r'COMMENTS\s*:\s*(.+?)(?:\n|$)', ocr_text, re.IGNORECASE | re.DOTALL)
    if comments_match:
        data['comments'] = comments_match.group(1).strip()
    
    return data


def get_last_image_in_dir(dir_path: str) -> Optional[str]:
    """Get the highest numbered image file in a directory."""
    try:
        image_files = []
        for file in os.listdir(dir_path):
            if file.lower().endswith(('.jpg', '.jpeg', '.png')):
                image_files.append(file)
        
        if not image_files:
            return None
        
        # Sort by filename (img_1.jpg, img_2.jpg, etc.)
        image_files.sort()
        return os.path.join(dir_path, image_files[-1])
    except Exception as e:
        print(f"Error reading directory {dir_path}: {e}")
        return None


def test_ocr_on_first_10_dirs():
    """Test OCR on the last image from the first 10 citation directories."""
    images_dir = Path("images")
    if not images_dir.exists():
        print("Images directory not found!")
        return
    
    # Get first 10 citation directories
    citation_dirs = []
    for item in sorted(images_dir.iterdir()):
        if item.is_dir():
            citation_dirs.append(item)
            if len(citation_dirs) >= 10:
                break
    
    results = []
    
    for citation_dir in citation_dirs:
        print(f"\n=== Processing {citation_dir.name} ===")
        
        last_image = get_last_image_in_dir(str(citation_dir))
        if not last_image:
            print(f"No images found in {citation_dir.name}")
            continue
        
        print(f"Processing image: {os.path.basename(last_image)}")
        
        # Extract text
        ocr_text = extract_text_from_image(last_image)
        if not ocr_text:
            print("No text extracted")
            continue
        
        # Parse data
        parsed_data = parse_citation_data(ocr_text)
        parsed_data['image_path'] = last_image
        parsed_data['raw_ocr_text'] = ocr_text
        
        results.append(parsed_data)
        
        # Print parsed fields
        for key, value in parsed_data.items():
            if key not in ['image_path', 'raw_ocr_text']:
                print(f"{key}: {value}")
    
    # Save results to JSON
    with open('ocr_test_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n=== Summary ===")
    print(f"Processed {len(results)} citations")
    print("Results saved to ocr_test_results.json")


if __name__ == '__main__':
    test_ocr_on_first_10_dirs()
