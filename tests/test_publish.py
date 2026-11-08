import json

import pytest
from PIL import Image
from pypdf import PdfWriter

import publish
from conftest import write_photos


def exported(issue):
    issue.en['_example'] = False
    issue.id['_example'] = False
    issue.write()
    base = f"elios-guide-{issue.en['_issue']}-{issue.en['_slug']}"
    for lang in ('en', 'id'):
        writer = PdfWriter()
        for _ in range(4):
            writer.add_blank_page(width=595, height=842)
        with open(issue.folder / f'{base}-{lang}.pdf', 'wb') as stream:
            writer.write(stream)
        Image.new('RGB', (1190, 1684)).save(issue.folder / f'{base}-cover-{lang}.png')
    return base


def test_publish_preserves_archive_and_copies_only_public_files(issue, tmp_path):
    exported(issue)
    site = tmp_path / 'site'
    site.mkdir()
    old = {'date': '2026-11-08', 'slug': 'old', 'topic': {'en': 'Old'}}
    (site / 'manifest.json').write_text(json.dumps({'guides': [old]}))
    (issue.folder / 'calc.py').write_text('raise Exception("never run")')
    publish.publish('2026-11-09', issue.root, site)
    guides = json.loads((site / 'manifest.json').read_text())['guides']
    assert [g['date'] for g in guides] == ['2026-11-09', '2026-11-08']
    assert len(list((site / 'issues' / '2026-11-09').iterdir())) == 6
    assert not (site / 'issues' / '2026-11-09' / 'calc.py').exists()
    publish.publish('2026-11-09', issue.root, site)
    assert len(json.loads((site / 'manifest.json').read_text())['guides']) == 2


def test_publish_copies_photos_and_drops_stale_ones(issue, tmp_path):
    exported(issue)
    write_photos(issue.folder)
    site = tmp_path / 'site'
    site.mkdir()
    entry = publish.publish('2026-11-09', issue.root, site)
    out = site / 'issues' / '2026-11-09'
    assert (out / 'photo.jpg').is_file() and (out / 'photo-800.jpg').is_file()
    assert entry['photo']['src'] == 'issues/2026-11-09/photo.jpg'
    for name in ('photo.jpg', 'photo-800.jpg'):
        (issue.folder / name).unlink()
    assert publish.publish('2026-11-09', issue.root, site)['photo'] is None
    assert not (out / 'photo.jpg').exists()


@pytest.mark.parametrize('failure', ['factcheck', 'example', 'pdf', 'png', 'symlink', 'small-png'])
def test_invalid_issue_does_not_change_published_site(issue, tmp_path, failure):
    base = exported(issue)
    if failure == 'factcheck':
        (issue.folder / 'check.json').write_text('[]')
    elif failure == 'example':
        issue.en['_example'] = True
        issue.write()
    elif failure == 'pdf':
        writer = PdfWriter()
        writer.add_blank_page(width=595, height=842)
        with open(issue.folder / f'{base}-en.pdf', 'wb') as stream:
            writer.write(stream)
    elif failure == 'png':
        (issue.folder / f'{base}-cover-id.png').write_bytes(b'bad')
    elif failure == 'small-png':
        Image.new('RGB', (595, 842)).save(issue.folder / f'{base}-cover-en.png')
    elif failure == 'symlink':
        (issue.folder / 'unexpected').symlink_to(issue.manifest)
    site = tmp_path / 'site'
    with pytest.raises(Exception):
        publish.publish('2026-11-09', issue.root, site)
    assert not site.exists()
