#!/usr/bin/env python3
"""
Build the Kodi addon repository into an output directory.

Packs the addon at the repo root plus the repository addon under repo/, writes
addons.xml + addons.xml.md5, and lays out artwork the way Kodi expects so the
addon browser can show icons without downloading each zip first.

Usage:  python3 repo/build_repo.py [--out _site]
"""

import argparse
import hashlib
import os
import shutil
import xml.etree.ElementTree as ET
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# The plugin lives at the repo root; the repository addon lives under repo/.
PLUGIN_SRC = ROOT
REPO_ADDON_SRC = os.path.join(ROOT, "repo", "repository.les19")

# Never ship these inside the plugin zip
EXCLUDE_DIRS = {".git", ".github", "repo", "__pycache__", ".idea", ".vscode", "_site"}
EXCLUDE_FILES = {".gitignore", ".DS_Store"}
EXCLUDE_EXTS = {".pyc", ".pyo", ".zip"}


def read_addon(addon_xml_path):
    tree = ET.parse(addon_xml_path)
    root = tree.getroot()
    return root, root.get("id"), root.get("version")


def should_skip(rel_path):
    parts = rel_path.split(os.sep)
    if any(p in EXCLUDE_DIRS for p in parts[:-1]):
        return True
    name = parts[-1]
    if name in EXCLUDE_FILES:
        return True
    return os.path.splitext(name)[1] in EXCLUDE_EXTS


def make_zip(src_dir, addon_id, version, zips_dir, top_level_only=False):
    """Zip src_dir into <zips_dir>/<addon_id>/<addon_id>-<version>.zip.

    Kodi requires exactly one top-level directory named after the addon id.
    """
    out_dir = os.path.join(zips_dir, addon_id)
    os.makedirs(out_dir, exist_ok=True)
    zip_path = os.path.join(out_dir, f"{addon_id}-{version}.zip")

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for dirpath, dirnames, filenames in os.walk(src_dir):
            dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]
            for fn in sorted(filenames):
                abs_path = os.path.join(dirpath, fn)
                rel = os.path.relpath(abs_path, src_dir)
                if top_level_only and os.sep in rel:
                    continue
                if not top_level_only and should_skip(rel):
                    continue
                zf.write(abs_path, os.path.join(addon_id, rel))
    return zip_path


def copy_assets(addon_root, addon_id, zips_dir):
    """Copy icon/fanart (and addon.xml) next to the zips.

    Kodi fetches artwork from <datadir>/<addon_id>/<asset path> and would
    otherwise show blank tiles in the addon browser.
    """
    dest_root = os.path.join(zips_dir, addon_id)
    os.makedirs(dest_root, exist_ok=True)
    shutil.copy2(os.path.join(addon_root, "addon.xml"), os.path.join(dest_root, "addon.xml"))

    root, _, _ = read_addon(os.path.join(addon_root, "addon.xml"))
    assets = root.find("./extension[@point='xbmc.addon.metadata']/assets")
    if assets is None:
        return
    for asset in assets:
        if not asset.text:
            continue
        src = os.path.join(addon_root, asset.text)
        if not os.path.exists(src):
            print(f"  ! missing asset {asset.text} for {addon_id}")
            continue
        dest = os.path.join(dest_root, asset.text)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        shutil.copy2(src, dest)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="_site", help="output directory (default: _site)")
    args = ap.parse_args()

    out = os.path.join(ROOT, args.out) if not os.path.isabs(args.out) else args.out
    zips_dir = os.path.join(out, "repo", "zips")
    if os.path.exists(out):
        shutil.rmtree(out)
    os.makedirs(zips_dir)

    addons_el = ET.Element("addons")
    built = []

    for src, top_level_only in ((PLUGIN_SRC, False), (REPO_ADDON_SRC, True)):
        addon_xml = os.path.join(src, "addon.xml")
        root, addon_id, version = read_addon(addon_xml)
        zip_path = make_zip(src, addon_id, version, zips_dir, top_level_only=top_level_only)
        copy_assets(src, addon_id, zips_dir)
        addons_el.append(root)
        built.append((addon_id, version, zip_path))
        size = os.path.getsize(zip_path) / 1024
        print(f"  packed {addon_id}-{version}.zip ({size:.0f} KB)")

    # addons.xml + md5. Kodi hashes the file bytes, so write then hash.
    addons_xml_path = os.path.join(zips_dir, "addons.xml")
    ET.ElementTree(addons_el).write(addons_xml_path, encoding="utf-8", xml_declaration=True)
    with open(addons_xml_path, "rb") as f:
        digest = hashlib.md5(f.read()).hexdigest()
    with open(addons_xml_path + ".md5", "w") as f:
        f.write(digest)
    print(f"  addons.xml md5 = {digest}")

    # Bootstrap copy of the repository zip at the site root, plus an index page.
    repo_id, repo_ver, repo_zip = built[-1]
    bootstrap = f"{repo_id}-{repo_ver}.zip"
    shutil.copy2(repo_zip, os.path.join(out, bootstrap))

    rows = "\n".join(
        f'    <li><a href="repo/zips/{i}/{i}-{v}.zip">{i}-{v}.zip</a></li>' for i, v, _ in built
    )
    with open(os.path.join(out, "index.html"), "w") as f:
        f.write(f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="utf-8"><title>les19 Kodi Repository</title></head>
<body>
  <h1>les19 Kodi Repository</h1>
  <p>In Kodi, add this URL as a file source, then install
     <a href="{bootstrap}">{bootstrap}</a> via <em>Install from zip file</em>.</p>
  <h2>All packages</h2>
  <ul>
{rows}
  </ul>
</body>
</html>
""")
    print(f"  bootstrap zip: {bootstrap}")
    print(f"\nBuilt into {out}")


if __name__ == "__main__":
    main()
