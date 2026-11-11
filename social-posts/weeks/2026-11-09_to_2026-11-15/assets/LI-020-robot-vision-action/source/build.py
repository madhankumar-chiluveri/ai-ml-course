"""Package complete generated carousel pages without adding or changing text."""
from pathlib import Path
import zipfile

import fitz
from PIL import Image
from pypdf import PdfReader, PdfWriter
from pypdf.generic import DictionaryObject, NameObject, TextStringObject

HERE = Path(__file__).resolve().parent
OUT = HERE.parent
SOURCE = 'https://deepmind.google/blog/gemini-robotics-2-5-accelerates-real-world-physical-intelligence/'
PDF = OUT / 'LI-020-robot-vision-action.pdf'


def main():
    doc = fitz.open()
    for i in range(1, 7):
        source = HERE / f'direct-slide-{i:02d}.png'
        output = OUT / f'slide-{i:02d}.png'
        with Image.open(source) as im:
            if abs(im.width / im.height - .8) > .012:
                raise ValueError(f'Unexpected generated aspect ratio: {source.name}: {im.size}')
            print(f'{source.name}: native {im.width} x {im.height}')
            im.convert('RGB').resize((2160, 2700), Image.Resampling.LANCZOS).save(output, optimize=True)
        page = doc.new_page(width=864, height=1080)
        page.insert_image(page.rect, filename=str(output))
        print(f'Exported {output.name}: 2160 x 2700', flush=True)
    temporary = OUT / 'LI-020-packaging.pdf'
    doc.save(temporary, deflate=True)
    doc.close()
    writer = PdfWriter()
    writer.append(PdfReader(temporary))
    writer.add_metadata({'/Title': 'How does AI help a robot pick up a part?', '/Author': 'madvibe.ai', '/Subject': 'A beginner explanation of Google’s reported robotics pilot'})
    source = writer.add_outline_item('Source: Google DeepMind — Gemini Robotics 2.5', 5)
    source.get_object()[NameObject('/A')] = DictionaryObject({NameObject('/S'): NameObject('/URI'), NameObject('/URI'): TextStringObject(SOURCE)})
    with PDF.open('wb') as stream:
        writer.write(stream)
    temporary.unlink()
    reader = PdfReader(PDF)
    assert len(reader.pages) == 6
    assert all(abs(float(p.mediabox.width) / float(p.mediabox.height) - .8) < .001 for p in reader.pages)
    assert reader.outline, 'Source bookmark missing'
    with zipfile.ZipFile(OUT / 'LI-020-instagram-carousel.zip', 'w', zipfile.ZIP_DEFLATED) as archive:
        for i in range(1, 7):
            archive.write(OUT / f'slide-{i:02d}.png', arcname=f'slide-{i:02d}.png')
    print('Verified six generated pages, a source bookmark, and the Instagram ZIP.')


if __name__ == '__main__':
    main()
