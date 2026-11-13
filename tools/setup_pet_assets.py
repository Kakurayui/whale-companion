"""Restore the two locally selected surfpet skins from a checksum-pinned release."""
from pathlib import Path, PurePosixPath
import hashlib
import shutil
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]
URL = 'https://github.com/Mieksido/surfpet/releases/download/v0.2.3/pet-pack.zip'
SHA256 = '784be55efcf14d4eb633c22cb111fc13f7a13280677de266a33aec1a56e498ac'

def main():
    archive = ROOT / '.work/reference/surfpet/pet-pack.zip'
    archive.parent.mkdir(parents=True, exist_ok=True)
    if not archive.exists():
        with urllib.request.urlopen(URL, timeout=60) as response, archive.open('wb') as output:
            shutil.copyfileobj(response, output)
    if hashlib.sha256(archive.read_bytes()).hexdigest() != SHA256:
        raise RuntimeError('Asset archive checksum mismatch; extraction cancelled.')
    with zipfile.ZipFile(archive) as package:
        for entry in package.infolist():
            name = PurePosixPath(entry.filename)
            if name.is_absolute() or '..' in name.parts or '\\' in entry.filename:
                raise RuntimeError('Unsafe archive entry')
            if len(name.parts) < 3 or name.parts[0] != 'skins' or name.parts[1] not in ('feiyu-02', 'feiyu-03') or entry.is_dir():
                continue
            target = ROOT / 'desktop' / Path(*name.parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(package.read(entry))
        (ROOT / 'desktop/icon.png').write_bytes(package.read('assets/icon.png'))
    (ROOT / 'web/feiyu').mkdir(parents=True, exist_ok=True)
    if not (ROOT / 'web/feiyu/pet.png').exists():
        shutil.copyfile(ROOT / 'desktop/skins/feiyu-03/preview.png', ROOT / 'web/feiyu/pet.png')
    print('Two prototype skins restored. See THIRD_PARTY_NOTICES.md for attribution.')

if __name__ == '__main__':
    main()
