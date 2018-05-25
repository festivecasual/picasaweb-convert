from pathlib import Path
import json
import xml.etree.ElementTree as ET
from distutils.dir_util import copy_tree
import shutil
import subprocess

convert_command = str(Path('imagemagick', 'convert.exe')) + ' -resize 512x512^ -extent 256x256 -gravity center %s %s'


for metadata in sorted(Path('photos').glob('*/metadata.json')):
    # Extract the URL component from the parent directory name
    url = metadata.parent.name.split('_')[1]

    # Extract title from metadata.json
    with metadata.open('r', encoding='utf8') as metadata_file:
        title = json.load(metadata_file)['albumData']['title']

    # Initialize a config.xml structure
    config = ET.Element('juiceboxgallery')
    config.set('galleryTitle', title)

    # Copy the skeleton gallery directory to the proper location
    copy_tree(str(Path('gallery_template')), str(Path('galleries', url)))

    copied_count, skipped_count, thumbnail_count = 0, 0, 0

    # Cycle through photo metadata in active directory
    for photo_metadata in sorted(metadata.parent.glob('*.JPG.json')):
        # Extract the photo description from the photo metadata
        with photo_metadata.open('r', encoding='utf8') as photo_metadata_file:
            description = json.load(photo_metadata_file)['description']

        # Select the best photo file to use, prioritizing any available -edited version
        basic_file = photo_metadata.with_name(photo_metadata.stem)
        edited_file = basic_file.with_name(basic_file.stem + '-edited.JPG')
        source_file = edited_file if edited_file.exists() else basic_file

        # Build the photo's entry in the config XML
        photo_node = ET.SubElement(config, 'image', {
            'imageURL' : 'images/' + source_file.name,
            'thumbURL' : 'thumbs/' + source_file.name,
            'linkURL' : 'images/' + source_file.name,
            'linkTarget' : '_blank',
        })
        photo_caption = ET.SubElement(photo_node, 'caption')
        photo_caption.text = description
        photo_title = ET.SubElement(photo_node, 'title')
        photo_title.text = basic_file.name

        # Copy the photo, if necessary
        photo_target = Path('galleries', url, 'images', source_file.name)
        if not photo_target.exists():
            shutil.copyfile(str(source_file), str(photo_target))
            copied_count += 1
        else:
            skipped_count += 1

        # Create the thumbnail, if necessary
        thumb_target = Path('galleries', url, 'thumbs', source_file.name)
        if not thumb_target.exists():
            subprocess.run(convert_command % (str(source_file), str(thumb_target)))
            thumbnail_count += 1

    # Write out the config.xml file in the current output directory
    Path('galleries', url, 'config.xml').write_bytes(ET.tostring(config))

    print('Completed %s (%d/%d images copied, %d thumbnails generated)' % (url, copied_count, copied_count + skipped_count, thumbnail_count))
