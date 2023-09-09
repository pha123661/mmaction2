import pickle

anno_pkl = '../../../data/gym/skeleton/gym_2d.pkl'

anno = pickle.load(open(anno_pkl, 'rb'))

assert 'annotations' in anno and 'split' in anno, anno.keys()


def rename_frame_dir_to_filename(frame_dir: str):
    '''
    Only for `gym` dataset:
        AZ4wWG6Rcak_004073_004175_0054_0055 ->  AZ4wWG6Rcak_E_004073_004175_A_0054_0055.mp4
    '''
    frame_dir = frame_dir.split('_')
    frame_dir.insert(1, 'E')
    frame_dir.insert(4, 'A')
    filename = '_'.join(frame_dir) + '.mp4'
    return filename


output_lists = {split: list() for split in anno['split']}
identifier = 'filename' if 'filename' in anno['annotations'][0] else 'frame_dir'
for sample in anno['annotations']:
    flag = False
    for split in anno['split']:
        if sample[identifier] in anno['split'][split]:
            if identifier == 'frame_dir':
                sample['filename'] = rename_frame_dir_to_filename(
                    sample['frame_dir'])
            output_lists[split].append(sample)
            flag = True
            break
    assert flag, f'Cannot find {sample[identifier]} in any split.'

for split, output_list in output_lists.items():
    output_pkl = anno_pkl.replace('.pkl', f'_{split}.pkl')
    pickle.dump(output_list, open(output_pkl, 'wb'))
    print(f'{split} data list is saved to {output_pkl}')
