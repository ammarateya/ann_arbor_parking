import os
import time
from scraper import CitationScraper


def main():
    # Test a small window of citation numbers around a recent range
    # Adjust as needed
    start = int(os.getenv('TEST_START', '10516370'))
    count = int(os.getenv('TEST_COUNT', '10'))
    numbers = [str(start - i) for i in range(count)]

    scraper = CitationScraper()

    for num in numbers:
        print(f"\n=== Testing citation {num} ===")
        data = scraper.search_citation(num)
        if not data:
            print("No results found or error.")
            continue
        # Print a concise snapshot
        keys = [
            'citation_number', 'location', 'plate_state', 'plate_number', 'vin',
            'issue_date', 'due_date', 'status', 'amount_due', 'more_info_url',
            'issuing_agency', 'violation_code', 'comments'
        ]

        for k in keys:
            if k in data:
                print(f"{k}: {data[k]}")

        # Violations (list) and images
        if 'violations' in data:
            print("violations:")
            for v in data['violations']:
                print(f"  - {v}")
        if 'image_urls' in data:
            print(f"image_urls: {len(data['image_urls'])} found")
            for u in data['image_urls'][:3]:
                print(f"  * {u}")

        # Be polite between requests
        time.sleep(1)


if __name__ == '__main__':
    main()


