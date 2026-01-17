#!/usr/bin/env python3
"""
Helper to download Tunisia governorates and delegations GeoJSON files into static/geo.
Run from project root:
  python3 scripts/fetch_geojson.py

This script attempts to download public GeoJSON files. If your environment
blocks outbound traffic, download the files manually and place them under
`static/geo/` with names:
 - tunisia_governorates.geojson
 - tunisia_delegations.geojson

Adjust URLs below if you have a preferred source.
"""
import os
import sys
import argparse
from urllib.request import urlopen
import subprocess

OUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'static', 'geo')
# Default candidate URLs (may be stale); prefer passing explicit URLs via CLI
GOV_URL = 'https://raw.githubusercontent.com/leforumalge/geodata/master/tunisia/tunisia_governorates.geojson'
DELEG_URL = 'https://raw.githubusercontent.com/leforumalge/geodata/master/tunisia/tunisia_delegations.geojson'

def fetch(url, target):
    print('Downloading', url)
    try:
        with urlopen(url) as r, open(target, 'wb') as f:
            f.write(r.read())
        print('Saved to', target)
    except Exception as e:
        print('Failed to download', url, e)
        # On some macOS/python installs SSL certificate verification fails.
        # Try a fallback using the system `curl` ignoring cert validation as a last resort.
        try:
            print('Attempting fallback download with curl (insecure)')
            subprocess.run(['curl', '-k', '-sS', '-L', url, '-o', target], check=False)
            if os.path.exists(target) and os.path.getsize(target) > 100:
                print('Saved to', target, '(via curl)')
                return
            else:
                print('Curl fallback did not produce a usable file for', url)
        except Exception as e2:
            print('Curl fallback failed', e2)


def try_candidates(candidates, target):
    """Try a list of candidate URLs until one produces a usable file."""
    for u in candidates:
        print('Trying candidate URL:', u)
        fetch(u, target)
        try:
            if os.path.exists(target) and os.path.getsize(target) > 200:
                # validate content appears to be Tunisia (simple bbox/coor test)
                try:
                    if geo_is_tunisia(target):
                        print('Candidate succeeded:', u)
                        return True
                    else:
                        print('Candidate produced geojson but not Tunisia; skipping:', u)
                        try:
                            os.remove(target)
                        except Exception:
                            pass
                except Exception:
                    # if validation fails, skip this candidate
                    try:
                        os.remove(target)
                    except Exception:
                        pass
        except Exception:
            pass
    return False


def geo_is_tunisia(path):
    """Basic heuristic: check whether any coordinate in the GeoJSON falls within Tunisia bbox.
    Tunisia approximate bounds: lat 30..38, lon -10..13
    """
    import json
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception:
        return False

    def walk_coords(obj):
        if isinstance(obj, list) and len(obj) >= 2 and isinstance(obj[0], (int, float)):
            lon, lat = obj[0], obj[1]
            if isinstance(lat, (int, float)) and isinstance(lon, (int, float)):
                if 30.0 <= lat <= 38.5 and -10.5 <= lon <= 13.5:
                    return True
            return False
        if isinstance(obj, list):
            for item in obj:
                if walk_coords(item):
                    return True
        if isinstance(obj, dict):
            for v in obj.values():
                if walk_coords(v):
                    return True
        return False

    # look under features or raw geometry
    return walk_coords(data)

def main():
    parser = argparse.ArgumentParser(description='Fetch Tunisia GeoJSON files into static/geo')
    parser.add_argument('--gov-url', help='Governorates GeoJSON URL', default=GOV_URL)
    parser.add_argument('--deleg-url', help='Delegations GeoJSON URL', default=DELEG_URL)
    parser.add_argument('--out-dir', help='Output directory (default static/geo)', default=OUT_DIR)
    args = parser.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)
    gov_target = os.path.join(args.out_dir, 'tunisia_governorates.geojson')
    deleg_target = os.path.join(args.out_dir, 'tunisia_delegations.geojson')

    print('Governorate URL:', args.gov_url)
    print('Delegation URL:', args.deleg_url)

    # Try primary URLs first; if they fail, try a short list of candidates.
    fetch(args.gov_url, gov_target)
    if not (os.path.exists(gov_target) and os.path.getsize(gov_target) > 200):
        candidates = [
            'https://raw.githubusercontent.com/leforumalge/geodata/master/tunisia/tunisia_governorates.geojson',
            'https://raw.githubusercontent.com/deldersveld/topojson/master/countries/tunisia/tunisia-provinces.json',
            'https://raw.githubusercontent.com/ramtinak/geojson-tunisia/master/tunisia-governorates.geojson',
            'https://raw.githubusercontent.com/gregoiredavid/france-geojson/master/regions.geojson'
        ]
        print('Primary gov file missing or invalid; trying candidate URLs...')
        try_candidates(candidates, gov_target)

    fetch(args.deleg_url, deleg_target)
    if not (os.path.exists(deleg_target) and os.path.getsize(deleg_target) > 200):
        candidates = [
            'https://raw.githubusercontent.com/leforumalge/geodata/master/tunisia/tunisia_delegations.geojson',
            'https://raw.githubusercontent.com/deldersveld/topojson/master/countries/tunisia/tunisia-districts.json',
            'https://raw.githubusercontent.com/ramtinak/geojson-tunisia/master/tunisia-delegations.geojson'
        ]
        print('Primary deleg file missing or invalid; trying candidate URLs...')
        try_candidates(candidates, deleg_target)

if __name__ == '__main__':
    main()
