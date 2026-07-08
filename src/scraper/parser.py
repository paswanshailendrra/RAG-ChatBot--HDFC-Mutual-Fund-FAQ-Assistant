"""
Phase 2b: HTML Parser / Cleaner for Groww Mutual Fund Pages.

Parses raw HTML from Groww scheme pages (fetched via browser rendering)
and extracts clean, structured text blocks with metadata.
"""
from typing import List, Dict
import os
import re
import json
from datetime import datetime
from bs4 import BeautifulSoup, Comment

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from src.config import GROWW_URLS


# Directory for cleaned text output
CLEANED_TEXT_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'cleaned_text')
RAW_HTML_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'raw_html')


def _remove_irrelevant_elements(soup: BeautifulSoup) -> BeautifulSoup:
    """Remove navigation, footers, scripts, styles, ads, and other noise."""
    # Remove script, style, noscript tags
    for tag in soup(['script', 'style', 'noscript', 'link', 'meta', 'svg', 'img', 'iframe']):
        tag.decompose()

    # Remove HTML comments
    for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
        comment.extract()

    # Remove header/navbar elements
    for nav in soup.find_all(['nav', 'header']):
        # Only remove the top-level site header, not section headers
        if nav.name == 'header' and nav.find_parent('section'):
            continue
        nav.decompose()

    # Remove footer elements
    for footer in soup.find_all('footer'):
        footer.decompose()

    # Remove common Groww nav/header classes
    nav_classes = [
        'header2025_headerContainer', 'loggedOut_navContainer',
        'loggedOut_leftContainer', 'dropdownUI_dropdownContainer',
        'hoverDiv', 'loginBtn', 'searchBar',
    ]
    for cls in nav_classes:
        for el in soup.find_all(class_=lambda c: c and cls in ' '.join(c) if isinstance(c, list) else cls in str(c)):
            el.decompose()

    # Remove loader elements
    for el in soup.find_all(class_=lambda c: c and any('loader' in str(x).lower() for x in (c if isinstance(c, list) else [c]))):
        el.decompose()

    return soup


def _extract_scheme_header(soup: BeautifulSoup) -> Dict:
    """Extract scheme name and category pills from the header section."""
    info = {}

    # Scheme name from h1
    h1 = soup.find('h1')
    if h1:
        info['scheme_name'] = h1.get_text(strip=True)

    # Category pills (Equity, Mid Cap, Very High Risk, etc.)
    pills_container = soup.find(class_=lambda c: c and 'pills_container' in str(c))
    if pills_container:
        pills = [span.get_text(strip=True) for span in pills_container.find_all('span')]
        info['categories'] = pills

    return info


def _extract_fund_details(soup: BeautifulSoup) -> List[str]:
    """Extract the key fund details: NAV, Min SIP, AUM, Expense Ratio, Rating."""
    details = []

    fund_details_div = soup.find(class_=lambda c: c and 'fundDetails_fundDetailsContainer' in str(c))
    if not fund_details_div:
        return details

    # Each detail is in a flex-column div with a label and value
    detail_items = fund_details_div.find_all(class_=lambda c: c and 'fundDetails_gap4' in str(c))
    for item in detail_items:
        texts = [t.strip() for t in item.stripped_strings]
        if len(texts) >= 2:
            label = texts[0]
            value = texts[1]
            details.append(f"{label}: {value}")

    return details


def _extract_return_stats(soup: BeautifulSoup) -> List[str]:
    """Extract return statistics (3Y annualised, 1D return, etc.)."""
    stats = []

    return_container = soup.find(class_=lambda c: c and 'returnStats_returnStatsContainer' in str(c))
    if return_container:
        texts = [t.strip() for t in return_container.stripped_strings]
        if texts:
            stats.append("Returns: " + " ".join(texts))

    return stats


def _extract_return_calculator_table(soup: BeautifulSoup) -> List[str]:
    """Extract the return calculator table data."""
    rows = []

    return_calc = soup.find(class_=lambda c: c and 'returnCalculator_container' in str(c))
    if not return_calc:
        return rows

    # Extract table rows
    table = return_calc.find('table')
    if table:
        # Get headers
        headers = []
        thead = table.find('thead')
        if thead:
            for th in thead.find_all('th'):
                headers.append(th.get_text(strip=True))

        # Get data rows
        tbody = table.find('tbody')
        if tbody:
            for tr in tbody.find_all('tr'):
                cells = []
                for td in tr.find_all('td'):
                    cell_text = td.get_text(strip=True)
                    # Clean up HTML comment artifacts
                    cell_text = re.sub(r'<!--.*?-->', '', cell_text)
                    cells.append(cell_text)
                if cells:
                    row_text = " | ".join(
                        f"{headers[i]}: {cells[i]}" if i < len(headers) else cells[i]
                        for i in range(len(cells))
                    )
                    rows.append(row_text)

    return rows


def _extract_scheme_info_sections(soup: BeautifulSoup) -> List[str]:
    """Extract all remaining informational sections (exit load, stamp duty, tax, etc.)."""
    sections = []

    # Look for all section-like containers with heading + content
    for heading_tag in soup.find_all(['h2', 'h3', 'h4']):
        heading_text = heading_tag.get_text(strip=True)
        if not heading_text:
            continue

        # Get the parent container or next siblings for content
        parent = heading_tag.find_parent('div')
        if parent:
            # Get all text from this section
            section_texts = []
            for child in parent.children:
                text = child.get_text(strip=True) if hasattr(child, 'get_text') else str(child).strip()
                text = re.sub(r'<!--.*?-->', '', text)
                if text and text != heading_text:
                    section_texts.append(text)

            if section_texts:
                combined = f"{heading_text}\n" + "\n".join(section_texts)
                # Avoid adding duplicates
                if combined not in sections:
                    sections.append(combined)

    return sections


def _extract_all_tables(soup: BeautifulSoup) -> List[str]:
    """Extract all tables as structured text."""
    table_texts = []

    for table in soup.find_all('table'):
        rows = []
        for tr in table.find_all('tr'):
            cells = []
            for cell in tr.find_all(['th', 'td']):
                cell_text = cell.get_text(strip=True)
                cell_text = re.sub(r'<!--.*?-->', '', cell_text)
                cells.append(cell_text)
            if cells:
                rows.append(" | ".join(cells))
        if rows:
            table_texts.append("\n".join(rows))

    return table_texts


def parse_scheme_page(html_content: str, url: str, scheme_name: str) -> Dict:
    """
    Parse a single Groww scheme page's HTML and extract clean structured text.

    Args:
        html_content: Raw HTML string.
        url: The source Groww URL.
        scheme_name: Human-readable scheme name.

    Returns:
        Dict with keys: scheme_name, url, timestamp, text_blocks (list of strings)
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    soup = _remove_irrelevant_elements(soup)

    text_blocks = []

    # 1. Scheme header
    header_info = _extract_scheme_header(soup)
    if header_info:
        header_text = f"Scheme: {header_info.get('scheme_name', scheme_name)}"
        if 'categories' in header_info:
            header_text += f"\nCategory: {', '.join(header_info['categories'])}"
        text_blocks.append(header_text)

    # 2. Return stats
    return_stats = _extract_return_stats(soup)
    text_blocks.extend(return_stats)

    # 3. Fund details (NAV, SIP, AUM, Expense Ratio, Rating)
    fund_details = _extract_fund_details(soup)
    if fund_details:
        text_blocks.append("Fund Details:\n" + "\n".join(fund_details))

    # 4. Return calculator table
    return_table = _extract_return_calculator_table(soup)
    if return_table:
        text_blocks.append("Return Calculator (SIP):\n" + "\n".join(return_table))

    # 5. Informational sections (exit load, stamp duty, tax, etc.)
    info_sections = _extract_scheme_info_sections(soup)
    text_blocks.extend(info_sections)

    # 6. All remaining tables
    tables = _extract_all_tables(soup)
    for t in tables:
        if t not in "\n".join(text_blocks):
            text_blocks.append(f"Table Data:\n{t}")

    # Filter out empty or very short blocks
    text_blocks = [b.strip() for b in text_blocks if b.strip() and len(b.strip()) > 10]

    return {
        "scheme_name": scheme_name,
        "url": url,
        "timestamp": datetime.now().isoformat(),
        "text_blocks": text_blocks,
    }


def save_cleaned_text(parsed_data: Dict) -> str:
    """Save the parsed text blocks to a local file."""
    os.makedirs(CLEANED_TEXT_DIR, exist_ok=True)

    slug = parsed_data["url"].rstrip("/").split("/")[-1]
    filepath = os.path.join(CLEANED_TEXT_DIR, f"{slug}.txt")

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"Source URL: {parsed_data['url']}\n")
        f.write(f"Scheme Name: {parsed_data['scheme_name']}\n")
        f.write(f"Scraped At: {parsed_data['timestamp']}\n")
        f.write("=" * 60 + "\n\n")

        for i, block in enumerate(parsed_data['text_blocks'], 1):
            f.write(f"--- Block {i} ---\n")
            f.write(block + "\n\n")

    print(f"  💾 Saved cleaned text: {filepath} ({len(parsed_data['text_blocks'])} blocks)")
    return filepath


def parse_all_schemes(html_dir: str = None) -> List[Dict]:
    """
    Parse all scraped HTML files from the raw_html directory.

    Args:
        html_dir: Directory containing the raw HTML files. Defaults to RAW_HTML_DIR.

    Returns:
        List of parsed data dicts.
    """
    if html_dir is None:
        html_dir = RAW_HTML_DIR

    print("=" * 60)
    print("🧹 Starting HTML Parsing & Cleaning")
    print("=" * 60)

    results = []
    for i, entry in enumerate(GROWW_URLS, 1):
        slug = entry["url"].rstrip("/").split("/")[-1]
        html_path = os.path.join(html_dir, f"{slug}.html")

        print(f"\n[{i}/{len(GROWW_URLS)}] {entry['scheme_name']}")

        if not os.path.exists(html_path):
            print(f"  ❌ HTML file not found: {html_path}")
            continue

        with open(html_path, "r", encoding="utf-8") as f:
            html_content = f.read()

        parsed = parse_scheme_page(html_content, entry["url"], entry["scheme_name"])
        save_cleaned_text(parsed)
        results.append(parsed)

        print(f"  ✅ Extracted {len(parsed['text_blocks'])} text blocks")

    # Summary
    total_blocks = sum(len(r['text_blocks']) for r in results)
    print("\n" + "=" * 60)
    print(f"📊 Parsing Complete: {len(results)} schemes, {total_blocks} total text blocks")
    print("=" * 60)

    return results


if __name__ == "__main__":
    results = parse_all_schemes()

    # Print a sample
    if results:
        print(f"\n📋 Sample output from '{results[0]['scheme_name']}':")
        for i, block in enumerate(results[0]['text_blocks'][:5], 1):
            print(f"\n--- Block {i} ---")
            print(block[:200])
