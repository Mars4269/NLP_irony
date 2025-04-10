import re
import pandas as pd

def estrai_hastag(testo:str)->list: return [hashtag.lstrip('#') for hashtag in re.findall(r'#\w+', testo)] 

def find_word_in_sentence(sentence, list_of_words):
    for word in list_of_words:
        sentence = re.sub(rf'\b{re.escape(word)}\b', f'#{word}', sentence)
    return sentence

def collect_info(df: pd, link_as_hastag:bool = False, placeholder_list=[])->pd:
    """
    #### input: dataframe con colonna text da trasformare
    #### out: colonna che contiene la lista di feature estratte dal testo
    """
    # aggiungere link placeholder
    if link_as_hastag:
        df['text'] = df['text'].apply(lambda x: re.sub(r'https?v?:\/\/\S+', '#LINK', x))
    else:
        df['text'] = df['text'].apply(lambda x: re.sub(r'https?v?:\/\/\S+', 'LINK', x))
        
    df['text'] = df['text'].apply(lambda x: re.sub(r'\b(?:ha|he|hi|ho|ah|eh|ih|oh|uh){2,}\b', '#RISATA', x))

    df['text'] = df['text'].apply(lambda x: find_word_in_sentence(x, placeholder_list))

    return  df['text'].apply(estrai_hastag)

def collect_info_string(str: str, link_as_hastag:bool = False)->list:
    """
    #### input: dataframe con colonna text da trasformare
    #### out: colonna che contiene la lista di feature estratte dal testo
    """
    if link_as_hastag:
        str = re.sub(r'https?v?:\/\/\S+', '#LINK', str)
    else:
        str = re.sub(r'https?v?:\/\/\S+', 'LINK', str)
    str = re.sub(r'\b(?:ha|he|hi|ho|ah|eh|ih|oh|uh){2,}\b', '#RISATA', str)
    
    return  [hashtag.lstrip('#') for hashtag in re.findall(r'#\w+', str)] 

def remove_empty_list(df: pd, col_name:str='hastags')->pd:
    """
    #### input: dataframe su cui si vogliono filtrare tutte le righe con lista di feature vuota
    #### out: dataframe contenente lista di feature non vuote
    """
    return df[df[col_name].apply(lambda x: len(x) > 0)]

def create_occurrences_dict(df: pd, colname = 'hastag')->dict:
    """
    #### input: df con due colonne [iro	hastags] esattamente in questordine
    #### out: dizionario contenente le occorrenze delle parole.
    NON MISURO LE CO-OCCORRENZE (anche poerchè sarebbero poche)
    """
    tmp_dict = {0: {}, 1:{}}
    for _,elems  in df[['iro', colname]].iterrows():
        for elem in elems[colname]:
            if elem.lower() in tmp_dict[elems['iro']]:
                tmp_dict[elems['iro']][elem.lower()] += 1
            else:
                tmp_dict[elems['iro']][elem.lower()] = 1
    return tmp_dict


def calcola_prob_hastag_dato_iro(occ_dict:dict, iro:int=0, n_top_tweet = 15, prob_thr = 0.01)->dict:
    """
    #### input: dizionario delle occorrenze delle features
    #### output: dizionario con features più rilevanti (cioè tra i primi n_top_tweet con P(hastag|iro=1) > prob_thr)
    """
    tot_n_iro = sum(occ_dict[iro].values()) # numero totale di hastag contenuti nei tweets di tipo iro
    p_hastg = {}

    for _, elem in enumerate(sorted(occ_dict[iro].items(), key=lambda x: x[1], reverse=True)):
        if (elem[1]/tot_n_iro) < prob_thr : break
        if _ > n_top_tweet : break
        p_hastg[elem[0]] = elem[1]/tot_n_iro
    return p_hastg


def find_relevant_features(df_r: pd, link_as_hastag = False, placeholder_list:list=[])->dict:
    COL_NAME = 'hastag'
    df = df_r.copy()
    df[COL_NAME] = collect_info(df,
                                link_as_hastag = False,    # troppi link, non può funzionare bene
                                placeholder_list=placeholder_list,
                    )
    df = remove_empty_list(df, col_name=COL_NAME)
    dizionario_occorrenze = create_occurrences_dict(df)

    iro = 1
    p_feature_iro = calcola_prob_hastag_dato_iro(dizionario_occorrenze, iro=iro)        # eg. P(grillo|iro=1)

    # Bayes th.
    # n_tweet = len(df)
    # p_iro = sum(dizionario_occorrenze[1].values())/n_tweet

    # p_tweet = {tweet:(dizionario_occorrenze[0][tweet] + dizionario_occorrenze[1][tweet])/n_tweet for tweet in p_feature_iro.keys()}

    # p_iro_hastg_2 = {tweet: (p_feature_iro[tweet] * p_iro)/p_tweet[tweet] for tweet in p_feature_iro.keys()}
    # p_iro_hastg_2

    p_iro_hastg = {tweet:
                   (dizionario_occorrenze[1][tweet])/
                   (dizionario_occorrenze[0][tweet] + dizionario_occorrenze[1][tweet])
                   for tweet in p_feature_iro.keys()}

    return p_iro_hastg


def get_prob_from_sentence(text:str='', features_dict: dict = {})->int:
    """
    #### output P(iro=1|testo)
    non considera le co-occorrenze
    """
    features_extracted = collect_info_string(text)
    prob = 0
    for feature in features_extracted:
        if feature.lower() in features_dict.keys():
            prob = max(prob, features_dict[feature.lower()])

    return prob

