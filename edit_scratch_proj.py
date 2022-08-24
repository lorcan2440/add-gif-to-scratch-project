'''
How to use this tool (assumes you already have Python installed)

1. Download your Scratch 3 project to your computer.
2. Edit the variables below to point the program to the project and the GIF you want to add.
3. Run the program. If you need to install PIL, run $ pip install Pillow at the command line.
4. Load the same Scratch project file you downloaded back into Scratch.
5. Result - the GIF you put has been added as a sprite with each costume as a frame.
6. Press Green Flag to see it animated.
'''

from zipfile import ZipFile
from io import BytesIO
import json, os, hashlib, copy, warnings

from PIL import Image


RESOURCES_DIR = r'C:\Users\lnick\Documents\Personal\Programming\x_More\Python\Reference Assets'
PROJ_PATH = os.path.join(RESOURCES_DIR, 'EmptyScratchProject.sb3')
GIF_PATH = os.path.join(RESOURCES_DIR, 'dragonite.gif')


def set_rotation_centre(img, costume_data: dict, sprite_centre_loc: int):
    
    if sprite_centre_loc in {1, 7, 8}:
        costume_data['rotationCenterX'] = 0
    elif sprite_centre_loc in {0, 2, 6}:
        costume_data['rotationCenterX'] = img.width // 2
    elif sprite_centre_loc in {3, 4, 5}:
        costume_data['rotationCenterX'] = img.width
    else:
        raise ValueError('`sprite_centre_loc` must be an integer from 0 to 8.')
    if sprite_centre_loc in {1, 2, 3}:
        costume_data['rotationCenterY'] = 0
    elif sprite_centre_loc in {0, 4, 8}:
        costume_data['rotationCenterY'] = img.height // 2
    elif sprite_centre_loc in {5, 6, 7}:
        costume_data['rotationCenterY'] = img.height
    else:
        raise ValueError('`sprite_centre_loc` must be an integer from 0 to 8.')


def add_gif_to_scratch_proj_as_sprite(scratch_proj_path: str, gif_path: str,
        sprite_name: str = None, sprite_centre_loc: int = 0):
    '''
    Adds a GIF to a Scratch project as a sprite. The costumes of the sprite will be the
    frames of the GIF, in the same order and at the original size.
    
    #### Arguments
    
    `scratch_proj_path` (str): the path to the downloaded Scratch project, ending in .sb3
    `gif_path` (str): the path to the GIF file to be added, ending in .gif

    #### Optional Keyword Arguments
    `sprite_name` (str, default = None): choose a different name for the sprite.
        A unique name will be chosen by default if this is not set.
    `sprite_centre_loc` (int, default = 0): choose whether the position of the sprite should
        be centred in the middle (0), or use numbers 1, 2, 3... for top-left, top-middle,
        top-right... etc.

    #### Returns
    `None`.
    '''    

    # set sprite user-facing properties
    if sprite_name is None:
        sprite_name = os.path.splitext(os.path.basename(gif_path))[0].title()

    # suppress warnings which say files inside the ZIP already exist
    warnings.filterwarnings("ignore", category=UserWarning, message='(Duplicate name: )')

    # create temporary working directory - stores project.json as it is edited
    ext_num = 0
    proj_hash = hashlib.md5(str(gif_path).encode('utf-8')).hexdigest()
    while os.path.isdir(tmp_dir := f'tmp_dir_{sprite_name}_{proj_hash[:8]}_{ext_num}'):
        ext_num += 1
    else:
        os.mkdir(tmp_dir)

    # extract project.json into temporary directory
    proj = ZipFile(scratch_proj_path, 'r')
    proj.extract('project.json', tmp_dir)
    
    # create the new sprite template
    with open('sprite_template.json', 'r') as f:
        template = json.load(f)
        new_sprite = template['spriteTemplate']
        new_sprite.update({'costumes': []})
        new_sprite['name'] = sprite_name
        costume_template_blank = template['costumeTemplate']
    
    # read frames from GIF into temp dir and fill out sprite JSON data
    proj = ZipFile(scratch_proj_path, 'a')
    anim = Image.open(gif_path)
    for frame in range(anim.n_frames):

        # load frame into anim
        anim.seek(frame)

        # write JSON data into sprite
        costume_data = copy.deepcopy(costume_template_blank)
        costume_data['assetId'] = hashlib.md5(anim.tobytes()).hexdigest()
        costume_data['name'] = sprite_name + str(frame + 1 if frame > 0 else '')
        costume_data['md5ext'] = costume_data['assetId'] + '.png'
        set_rotation_centre(anim, costume_data, sprite_centre_loc)
        new_sprite['costumes'].append(costume_data)
    
        # write image frame into project
        frame_bytes = BytesIO()
        anim.save(frame_bytes, format='PNG', quality=100, exif=anim.info.get('exif', None))
        proj.writestr(costume_data['md5ext'], frame_bytes.getvalue())

    # edit temporary project.json with the newly made sprite data
    with open(os.path.join(tmp_dir, 'project.json'), 'r+') as f:
        proj_json = json.load(f)
        proj_json['targets'].append(new_sprite)
        f.seek(0)
        f.truncate(0)
        f.write(json.dumps(proj_json))

    # replace project.json in zipfile with temp file
    proj.write(os.path.join(tmp_dir, 'project.json'), arcname='project.json')

    # remove temp directory
    os.remove(os.path.join(tmp_dir, 'project.json'))
    os.rmdir(tmp_dir)
        

if __name__ == '__main__':
    add_gif_to_scratch_proj_as_sprite(PROJ_PATH, GIF_PATH)
