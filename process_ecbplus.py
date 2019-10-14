# py2

import os
import sys
import json
import xml.etree.ElementTree as ET
from collections import defaultdict

def is_belong_train_set(fname):
    """
    Args:
        fname: string, file name without dir path
    Returns:
        boolean
    """
    topic_num_in_test_set = ['3', '45']
    if fname.split('_')[0] in topic_num_in_test_set:
        return False
    else:
        return True

def convert_jsonlines_to_conll_format(input_file_path, output_file_path, cluster_key_name='predicted_clusters'):
    """
    Args:
        input_file_path: string
        output_file_path: string
        cluster_key_name: string
    """
    with open(input_file_path) as fopen, open(output_file_path, 'w') as fwrite:
        for line_cnt, line in enumerate(fopen):
            line_dict = json.loads(line.strip())
            doc_key = line_dict['doc_key'].encode('utf-8')
            sentences = line_dict['sentences']
            clusters = line_dict[cluster_key_name]
            # produce token_id - entity map
            start_word_map = defaultdict(list)
            end_word_map = defaultdict(list)
            single_word_map = defaultdict(list)
            entity_id = 0
            for cluster in clusters:
                for t_ids in cluster:
                    if t_ids[0] == t_ids[1]:
                        single_word_map[t_ids[0]].append(entity_id)
                    else:
                        start_word_map[t_ids[0]].append(entity_id)
                        end_word_map[t_ids[1]].append(entity_id)
                entity_id += 1
            # produce conll_lines
            conll_lines = []
            begin_line = '#begin document (%s); part 000' % (doc_key)
            conll_lines.append(begin_line)
            token_id = 0
            for sentence in sentences:
                token_id_within_sentence = 0
                for token in sentence:
                    line = '%s 0 %s %s * * * * * * * ' % (doc_key, token_id_within_sentence, token.encode('utf-8'))
                    hit_flag = False
                    if token_id in start_word_map:
                        for entity_id in start_word_map[token_id]:
                            if hit_flag == True:
                                line += '|'
                            line += '(%s' % (entity_id)
                            hit_flag = True
                    if token_id in end_word_map:
                        for entity_id in end_word_map[token_id]:
                            if hit_flag == True:
                                line += '|'
                            line += '%s)' % (entity_id)
                            hit_flag = True
                    if token_id in single_word_map:
                        for entity_id in single_word_map[token_id]:
                            if hit_flag == True:
                                line += '|'
                            line += '(%s)' % (entity_id)
                            hit_flag = True
                    if hit_flag == False:
                        line += '-'
                    token_id_within_sentence += 1
                    token_id += 1
                    conll_lines.append(line)
                conll_lines.append('')
            conll_lines.append('#end document')
            fwrite.write('\n'.join(conll_lines) + '\n')
    return
            

def convert_ecbplus_to_conll_format(input_file_path, no_action):
    """
    Args:
        input_file_path: string
        no_action: boolean
    Returns:
        conll_lines: string
    """
    tree = ET.parse(input_file_path)
    root = tree.getroot()
    markables = None
    relations = None

    # parsing doc_key
    #root.attrib: {'doc_id': 'DOC15653231646358310', 'doc_name': '1_10ecb.xml'}
    doc_key = 'nw/' + root.attrib['doc_name']
    # parsing sentences
    sentences = []
    cur_sentence_idx = 0
    cur_sentence = []
    for child in root:
        if child.tag != 'token':
            if child.tag == 'Markables':
                markables = child
            if child.tag == 'Relations':
                relations = child
            continue
        if cur_sentence_idx+1 == int(child.attrib['sentence']):
            sentences.append(cur_sentence)
            cur_sentence = []
            cur_sentence_idx += 1
        cur_sentence.append(child.text)
    if len(cur_sentence):
        sentences.append(cur_sentence)
    # parsing clusters
    # produce mention - token_span dict
    assert markables != None
    mt_dict = {}
    for mention in markables:
        if no_action and mention.tag.startswith('ACTION_'):
            continue
        m_id = mention.attrib['m_id']
        t_ids = []
        for mention_child in mention:
            t_ids.append(int(mention_child.attrib['t_id']))
        if len(t_ids) > 0:
            mt_dict[m_id] = [t_ids[0], t_ids[-1]]
        else:
            mt_dict[m_id] = []
    # produce clusters
    assert relations != None
    clusters = []
    for coref in relations:
        if len(coref) <= 2:
            continue
        cur_cluster = []
        for mention in coref:
            if "source" == mention.tag:
                m_id = mention.attrib['m_id']
                if m_id not in mt_dict:
                    continue
                t_ids = mt_dict[m_id]
                cur_cluster.append(t_ids)
        if cur_cluster:
            clusters.append(cur_cluster)
    # produce token_id - entity map
    start_word_map = defaultdict(list)
    end_word_map = defaultdict(list)
    single_word_map = defaultdict(list)
    entity_id = 0
    for cluster in clusters:
        for t_ids in cluster:
            if t_ids[0] == t_ids[1]:
                single_word_map[t_ids[0]].append(entity_id)
            else:
                start_word_map[t_ids[0]].append(entity_id)
                end_word_map[t_ids[1]].append(entity_id)
        entity_id += 1

    # produce conll_lines
    conll_lines = []
    begin_line = '#begin document (%s); part 000' % (doc_key)
    conll_lines.append(begin_line)
    token_id = 1
    for sentence in sentences:
        token_id_within_sentence = 0
        for token in sentence:
            line = '%s 0 %s %s * * * * * * * ' % (doc_key, token_id_within_sentence, token.encode('utf-8'))
            hit_flag = False
            if token_id in start_word_map:
                for entity_id in start_word_map[token_id]:
                    if hit_flag == True:
                        line += '|'
                    line += '(%s' % (entity_id)
                    hit_flag = True
            if token_id in end_word_map:
                for entity_id in end_word_map[token_id]:
                    if hit_flag == True:
                        line += '|'
                    line += '%s)' % (entity_id)
                    hit_flag = True
            if token_id in single_word_map:
                for entity_id in single_word_map[token_id]:
                    if hit_flag == True:
                        line += '|'
                    line += '(%s)' % (entity_id)
                    hit_flag = True
            if hit_flag == False:
                line += '-'
            token_id_within_sentence += 1
            token_id += 1
            conll_lines.append(line)
        conll_lines.append('')
    conll_lines.append('#end document')
    return '\n'.join(conll_lines)

def convert_ecbplus_to_e2ecoref_minimal_format(input_file_path, no_action):
    """
    Args:
        input_file_path: string
        no_action: boolean
    Returns:
        jsonline: string, one line of dumped json string
    """
    tree = ET.parse(input_file_path)
    root = tree.getroot()
    markables = None
    relations = None

    # parsing doc_key
    #root.attrib: {'doc_id': 'DOC15653231646358310', 'doc_name': '1_10ecb.xml'}
    doc_key = 'nw/' + root.attrib['doc_name'] + '_0'
    # parsing sentences
    sentences = []
    cur_sentence_idx = 0
    cur_sentence = []
    for child in root:
        if child.tag != 'token':
            if child.tag == 'Markables':
                markables = child
            if child.tag == 'Relations':
                relations = child
            continue
        if cur_sentence_idx+1 == int(child.attrib['sentence']):
            sentences.append(cur_sentence)
            cur_sentence = []
            cur_sentence_idx += 1
        cur_sentence.append(child.text)
    if len(cur_sentence):
        sentences.append(cur_sentence)
    # parsing speakers
    speakers = []
    for _ in sentences:
        speakers.append(['' for i in range(len(_))])

    # parsing clusters
    # produce mention - token_span dict
    assert markables != None
    mt_dict = {}
    for mention in markables:
        if no_action and mention.tag.startswith('ACTION_'):
            continue
        m_id = mention.attrib['m_id']
        t_ids = []
        for mention_child in mention:
            t_ids.append(int(mention_child.attrib['t_id']))
        if len(t_ids) > 0:
            mt_dict[m_id] = [t_ids[0], t_ids[-1]]
        else:
            mt_dict[m_id] = []
    # produce clusters
    assert relations != None
    clusters = []
    for coref in relations:
        if len(coref) <= 2:
            continue
        cur_cluster = []
        for mention in coref:
            if "source" == mention.tag:
                m_id = mention.attrib['m_id']
                if m_id not in mt_dict:
                    continue
                t_ids = mt_dict[m_id]
                # need convert to idx strating from 0
                t_ids = [_-1 for _ in t_ids]
                cur_cluster.append(t_ids)
        if cur_cluster:
            clusters.append(cur_cluster)

    res = {
            "speakers": speakers,
            "doc_key": doc_key,
            "sentences": sentences,
            "constituents": [],
            "clusters": clusters,
            "ner": []
           }
    #print(mt_dict)
    #print(res)
    return json.dumps(res)

def traverse_and_convert(input_file_dir, output_file_path, no_action=True):
    """
    Args:
        input_file_dir: string,
        output_file_path: string
        no_action: boolean, whether to add action
    """
    output_file_path_train = 'train.' + output_file_path + '.jsonlines'
    output_file_path_dev = 'dev.' + output_file_path + '.jsonlines'
    conll_file_path_dev = 'dev.' + output_file_path + '.conll'
    fwrite_train = open(output_file_path_train, 'w')
    fwrite_dev = open(output_file_path_dev, 'w')
    fwrite_conll_dev = open(conll_file_path_dev, 'w')

    for dir_name, subdir_list, file_list in os.walk(input_file_dir):
        for fname in file_list:
            if not fname.endswith('xml'):
                continue
            full_path_fname = dir_name + '/' + fname
            print('Now processing %s...' % (full_path_fname))
            jsonline = convert_ecbplus_to_e2ecoref_minimal_format(full_path_fname, no_action)
            if is_belong_train_set(fname):
                fwrite_train.write(jsonline+'\n')
            else:
                fwrite_dev.write(jsonline+'\n')
                conll_lines = convert_ecbplus_to_conll_format(full_path_fname, no_action)
                fwrite_conll_dev.write(conll_lines + '\n')
    fwrite_train.close()
    fwrite_dev.close()
    fwrite_conll_dev.close()

if __name__ == '__main__':
    input_file_dir = sys.argv[1]
    output_file_path = sys.argv[2]
    traverse_and_convert(input_file_dir, output_file_path, no_action=True)
    # only_action? with_action?
    #convert_jsonlines_to_conll_format(input_file_dir, output_file_path)
