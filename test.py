from http.server import BaseHTTPRequestHandler
import re
import os
from collections import Counter
import math
import json
import simplejson
from unidecode import unidecode
from storage3 import create_client
from supabase import create_client as supa_create_client, Client
import tempfile
import time
import csv


class JobTitleMatch:
    """
    Matches user input of jobtitles for relevancy with the criteria outlined in their brief.
    """
    
    def __init__(self, jobtitles = [], kw = [], exclude_kw = [], sen = [], exclude_sen = [], jt = [], exclude_jt = []):
        self.jobtitles = jobtitles #jobtitles uploaded by user in list format
        self.kw = kw #relevant keywords from the brief in list format
        self.exclude_kw = exclude_kw #exclusion keywords from the brief in list format
        self.sen = sen #relevant seniorities from the brief in list format
        self.exclude_sen = exclude_sen #exclusion seniorities from the brief in list format
        self.jt = jt #relevant jobtitles from the brief in list format
        self.exclude_jt = exclude_jt #exclusion jobtitles from the brief in list format
        
        self.jobtitles_checker = jobtitles
        
        #same as above but without punctuation, lowercase, and with english characters
        self.jobtitles_clean = [unidecode(re.sub(r"[^\w\s]", " ", j)).lower().strip().replace("  ", " ") for j in jobtitles]
        self.kw_clean = [unidecode(re.sub(r"[^\w\s]", " ", j)).lower().strip().replace("  ", " ")  for j in kw]
        self.exclude_kw_clean = [unidecode(re.sub(r"[^\w\s]", " ", j)).lower().strip().replace("  ", " ")  for j in exclude_kw]
        self.sen_clean = [unidecode(re.sub(r"[^\w\s]", " ", j)).lower().strip().replace("  ", " ")  for j in sen]
        self.exclude_sen_clean = [unidecode(re.sub(r"[^\w\s]", " ", j)).lower().strip().replace("  ", " ")  for j in exclude_sen]
        self.jt_clean = [unidecode(re.sub(r"[^\w\s]", " ", j)).lower().strip().replace("  ", " ")  for j in jt]
        self.exclude_jt_clean = [unidecode(re.sub(r"[^\w\s]", " ", j)).lower().strip().replace("  ", " ")  for j in exclude_jt]
        
        self.jobtitles_clean_extra = [unidecode(re.sub(r"[^\w\s]", " ", j)).lower().strip().replace("  ", " ") for j in jobtitles]
        self.kw_clean_extra = [unidecode(re.sub(r"[^\w\s]", " ", j)).lower().strip().replace("  ", " ")  for j in kw]
        self.sen_clean_extra = [unidecode(re.sub(r"[^\w\s]", " ", j)).lower().strip().replace("  ", " ")  for j in sen]
        self.jt_clean_extra = [unidecode(re.sub(r"[^\w\s]", " ", j)).lower().strip().replace("  ", " ")  for j in jt]
        #self.exclude_jt_clean = [unidecode(re.sub(r'[\W_]+ |(/)', " ", j)).lower().strip() for j in exclude_jt]
        
    def remove_filler_words_from_jts(self):
        
        filler_words = ['a', 'an', 'and', 'at', 'do', 'has', 'in', 'of', 'the', 'to', 'my']
        additional_words = ['afghanistan', 'africa', 'aland islands', 'albania', 'algeria', 'america', 'american', 'american samoa', 'americas', 'andorra', 'angola', 'anguilla', 'antarctica', 'antigua and barbuda', 'apac', 'area', 'argentina', 'armenia', 'aruba', 'asia', 'australia', 'austria', 'azerbaijan', 'bahamas', 'bahrain', 'bangladesh', 'barbados', 'belarus', 'belgium', 'belize', 'benelux', 'benin', 'bermuda', 'bhutan', 'big', 'bolivia', 'bosnia and herzegovina', 'botswana', 'bouvet island', 'brazil', 'british indian ocean territory', 'brunei darussalam', 'bulgaria', 'burkina faso', 'burundi', 'cabo verde', 'cambodia', 'cameroon', 'canada', 'caribbean', 'cayman islands', 'central', 'central african republic', 'chad', 'chile', 'china', 'christmas island', 'coast', 'colombia', 'comoros', 'company', 'congo', 'cook islands', 'costa rica', 'cote divoire', 'country', 'croatia', 'cuba', 'curaçao', 'cyprus', 'czechia', 'denmark', 'division', 'divisional', 'djibouti', 'dominica', 'dominican republic', 'east', 'eastern', 'ecuador', 'egypt', 'el salvador', 'emea', 'equatorial guinea', 'eritrea', 'estonia', 'eswatini', 'ethiopia', 'eu', 'europe', 'european', 'exec', 'executive', 'falkland islands', 'faroe islands', 'fiji', 'finland', 'france', 'french guiana', 'french polynesia', 'french southern territories', 'functional', 'gabon', 'gambia', 'georgia', 'germany', 'ghana', 'gibraltar', 'global', 'greece', 'greenland', 'grenada', 'group', 'guadeloupe', 'guam', 'guatemala', 'guernsey', 'guinea', 'guinea-bissau', 'guyana', 'haiti', 'heard island and mcdonald islands', 'honduras', 'hong kong', 'hungary', 'iceland', 'india', 'indonesia', 'innovation', 'institutional', 'internation', 'international', 'iran', 'iraq', 'ireland', 'isle of man', 'israel', 'italy', 'jamaica', 'japan', 'jersey', 'jordan', 'kazakhstan', 'kenya', 'kingdom', 'kiribati', 'korea', 'kuwait', 'kyrgyzstan', 'latam', 'latin', 'latvia', 'lebanon', 'lesotho', 'liberia', 'libya', 'liechtenstein', 'lithuania', 'local', 'london', 'luxembourg', 'macao', 'madagascar', 'malawi', 'malaysia', 'maldives', 'mali', 'malta', 'marshall islands', 'martinique', 'mauritania', 'mauritius', 'mayotte', 'mexico', 'middle', 'moldova', 'monaco', 'mongolia', 'montenegro', 'montserrat', 'morocco', 'mozambique', 'myanmar', 'namibia', 'national', 'nauru', 'nepal', 'netherlands', 'new caledonia', 'new zealand', 'nicaragua', 'niger', 'nigeria', 'niue', 'nordic', 'nordics', 'norfolk island', 'north', 'northeast', 'northern', 'northern mariana islands', 'norway', 'oman', 'pacific', 'pakistan', 'palau', 'palestine', 'panama', 'papua new guinea', 'paraguay', 'peru', 'philippines', 'pitcairn', 'poland', 'portugal', 'principal', 'puerto rico', 'qatar', 'region', 'regional', 'regions', 'republic of north macedonia', 'romania', 'russia', 'russian federation', 'rwanda', 'saint barthelemy', 'saint helena', 'saint kitts and nevis', 'saint lucia', 'saint martin', 'saint pierre and miquelon', 'saint vincent and the grenadines', 'samoa', 'san marino', 'sao tome and principe', 'saudi arabia', 'section', 'senegal', 'senior', 'serbia', 'seychelles', 'sierra leone', 'singapore', 'sint maarten', 'slovakia', 'slovenia', 'snr', 'solomon islands', 'somalia', 'south', 'south africa', 'south georgia and the south sandwich islands', 'south sudan', 'southeast', 'spain', 'sr', 'sri lanka', 'states', 'sudan', 'suriname', 'svalbard and jan mayen', 'sweden', 'switzerland', 'syrian arab republic', 'taiwan', 'tajikistan', 'tanzania', 'thailand', 'timor-leste', 'togo', 'tokelau', 'tonga', 'transformation', 'trinidad and tobago', 'tunisia', 'turkey', 'turkmenistan', 'turks and caicos islands', 'tuvalu', 'uganda', 'uk', 'uki', 'ukraine', 'united', 'united arab emirates', 'united kingdom of great britain and northern ireland', 'united states minor outlying islands', 'united states of america', 'uruguay', 'us', 'usa', 'uzbekistan', 'vanuatu', 'venezuela', 'viet nam', 'virgin islands', 'wallis and futuna', 'west', 'western sahara', 'worldwide', 'yemen', 'zambia']
        additional_words_extra = ['co', 'executive', 'lead', 'principle', 'senior', 'snr', 'sr', 'chief', 'afghanistan', 'africa', 'aland islands', 'albania', 'algeria', 'america', 'american', 'american samoa', 'americas', 'andorra', 'angola', 'anguilla', 'antarctica', 'antigua and barbuda', 'apac', 'area', 'argentina', 'armenia', 'aruba', 'asia', 'australia', 'austria', 'azerbaijan', 'bahamas', 'bahrain', 'bangladesh', 'barbados', 'belarus', 'belgium', 'belize', 'benelux', 'benin', 'bermuda', 'bhutan', 'big', 'bolivia', 'bosnia and herzegovina', 'botswana', 'bouvet island', 'brazil', 'british indian ocean territory', 'brunei darussalam', 'bulgaria', 'burkina faso', 'burundi', 'cabo verde', 'cambodia', 'cameroon', 'canada', 'caribbean', 'cayman islands', 'central', 'central african republic', 'chad', 'chile', 'china', 'christmas island', 'coast', 'colombia', 'comoros', 'company', 'congo', 'cook islands', 'costa rica', 'cote divoire', 'country', 'croatia', 'cuba', 'curaçao', 'cyprus', 'czechia', 'denmark', 'division', 'divisional', 'djibouti', 'dominica', 'dominican republic', 'east', 'eastern', 'ecuador', 'egypt', 'el salvador', 'emea', 'equatorial guinea', 'eritrea', 'estonia', 'eswatini', 'ethiopia', 'eu', 'europe', 'european', 'exec', 'executive', 'falkland islands', 'faroe islands', 'fiji', 'finland', 'france', 'french guiana', 'french polynesia', 'french southern territories', 'functional', 'gabon', 'gambia', 'georgia', 'germany', 'ghana', 'gibraltar', 'global', 'greece', 'greenland', 'grenada', 'group', 'guadeloupe', 'guam', 'guatemala', 'guernsey', 'guinea', 'guinea-bissau', 'guyana', 'haiti', 'heard island and mcdonald islands', 'honduras', 'hong kong', 'hungary', 'iceland', 'india', 'indonesia', 'innovation', 'institutional', 'internation', 'international', 'iran', 'iraq', 'ireland', 'isle of man', 'israel', 'italy', 'jamaica', 'japan', 'jersey', 'jordan', 'kazakhstan', 'kenya', 'kingdom', 'kiribati', 'korea', 'kuwait', 'kyrgyzstan', 'latam', 'latin', 'latvia', 'lebanon', 'lesotho', 'liberia', 'libya', 'liechtenstein', 'lithuania', 'local', 'london', 'luxembourg', 'macao', 'madagascar', 'malawi', 'malaysia', 'maldives', 'mali', 'malta', 'marshall islands', 'martinique', 'mauritania', 'mauritius', 'mayotte', 'mexico', 'middle', 'moldova', 'monaco', 'mongolia', 'montenegro', 'montserrat', 'morocco', 'mozambique', 'myanmar', 'namibia', 'national', 'nauru', 'nepal', 'netherlands', 'new caledonia', 'new zealand', 'nicaragua', 'niger', 'nigeria', 'niue', 'nordic', 'nordics', 'norfolk island', 'north', 'northeast', 'northern', 'northern mariana islands', 'norway', 'oman', 'pacific', 'pakistan', 'palau', 'palestine', 'panama', 'papua new guinea', 'paraguay', 'peru', 'philippines', 'pitcairn', 'poland', 'portugal', 'principal', 'puerto rico', 'qatar', 'region', 'regional', 'regions', 'republic of north macedonia', 'romania', 'russia', 'russian federation', 'rwanda', 'saint barthelemy', 'saint helena', 'saint kitts and nevis', 'saint lucia', 'saint martin', 'saint pierre and miquelon', 'saint vincent and the grenadines', 'samoa', 'san marino', 'sao tome and principe', 'saudi arabia', 'section', 'senegal', 'senior', 'serbia', 'seychelles', 'sierra leone', 'singapore', 'sint maarten', 'slovakia', 'slovenia', 'snr', 'solomon islands', 'somalia', 'south', 'south africa', 'south georgia and the south sandwich islands', 'south sudan', 'southeast', 'spain', 'sr', 'sri lanka', 'states', 'sudan', 'suriname', 'svalbard and jan mayen', 'sweden', 'switzerland', 'syrian arab republic', 'taiwan', 'tajikistan', 'tanzania', 'thailand', 'timor-leste', 'togo', 'tokelau', 'tonga', 'transformation', 'trinidad and tobago', 'tunisia', 'turkey', 'turkmenistan', 'turks and caicos islands', 'tuvalu', 'uganda', 'uk', 'uki', 'ukraine', 'united', 'united arab emirates', 'united kingdom of great britain and northern ireland', 'united states minor outlying islands', 'united states of america', 'uruguay', 'us', 'usa', 'uzbekistan', 'vanuatu', 'venezuela', 'viet nam', 'virgin islands', 'wallis and futuna', 'west', 'western sahara', 'worldwide', 'yemen', 'zambia']
        
        #Want to make sure that none of the words are excluded or relevant
        all_words = self.kw_clean + self.exclude_kw_clean + self.sen_clean + self.exclude_sen_clean + self.jt_clean + self.exclude_jt_clean
        additional_words = list(set(additional_words) - set(all_words))
        
        #Additional removal of singular words that are relevant or excluded
        all_words = ' '.join(all_words)
        all_words = all_words.split(' ')
        additional_words = list(set(additional_words) - set(all_words))
            
        cleaned_titles = []
        cleaned_titles1 = []
        cleaned_titles2 = []
        
        for i in self.jobtitles_clean: #remove filler and additional words from user's jobtitles
            cleaned_titles.append(' '.join([j for j in i.split(' ') if j not in filler_words]))
            cleaned_titles1.append(' '.join([j for j in i.split(' ') if j not in filler_words]))
            cleaned_titles2.append(' '.join([j for j in i.split(' ') if j not in additional_words_extra]))
        
        self.jobtitles_clean = cleaned_titles
        self.jobtitles_checker = cleaned_titles1
        self.jobtitles_clean_extra = cleaned_titles2
        
        cleaned_titles = []
        cleaned_titles1 = []
        
        for i in self.jt_clean: #remove filler words from jobtitles in brief
            cleaned_titles.append(' '.join([j for j in i.split(' ') if j not in filler_words]))
            cleaned_titles1.append(' '.join([j for j in i.split(' ') if j not in additional_words_extra]))
        
        self.jt_clean = cleaned_titles
        self.jt_clean_extra = cleaned_titles1
        
        cleaned_titles = []
        
        for i in self.exclude_jt_clean: #remove filler words from exclusion jobtitles in brief
            cleaned_titles.append(' '.join([j for j in i.split(' ') if j not in filler_words]))
        
        self.exclude_jt_clean = cleaned_titles
        
        cleaned_titles = []
        
        for i in self.sen_clean_extra:
            cleaned_titles.append(' '.join([j for j in i.split(' ') if j not in additional_words_extra]))
        
        self.sen_clean_extra = cleaned_titles
        
        cleaned_titles = []
        
        for i in self.kw_clean_extra:
            cleaned_titles.append(' '.join([j for j in i.split(' ') if j not in additional_words_extra]))
        
        self.kw_clean_extra = cleaned_titles
        
    def add_extra_titles(self):
        
        extra_kw = [
            ['it','information technology', 'ict'],
            ['technology', 'tech', 'technical'],
            ['information', 'info'],
            ['hr', 'human resources'],
            ['esg', 'environmental social and governance'],
            ['sdg', 'sustainable development goals'],
            ['application', 'app'],
            ['cyber security', 'cybersecurity'],
            ['finance', 'financial']
            ]
        
        #for specific titles so we can add information etc. if it is used.
        extra_kw_other = [
            ['it','information technology', 'ict', 'technology', 'tech', 'technical', 'information', 'info'],
            ['hr', 'human resources'],
            ['esg', 'environmental social and governance'],
            ['sdg', 'sustainable development goals'],
            ['application', 'app'],
            ['cyber security', 'cybersecurity'],
            ['finance', 'financial']
            ]
        
        extra_sen = [
            ['manager', 'mgr'],
            ['svp','senior vice president', 'sr vp', 'sr vice president', 'snr vp', 'snr vice president', 'senior vp'],
            ['vp', 'vice president', 'svp', 'senior vice president', 'sr vp', 'sr vice president', 'snr vp', 'snr vice president', 'senior vp', 'evp','executive vice president', 'executive vp'],
            ['evp','executive vice president', 'executive vp'],
            ]
        
        def check(lst, include):
             
            for i in lst:
                for j in i:
                    if j in include:
                        if j in ['svp','senior vice president', 'sr vp', 'sr vice president', 'snr vp', 'snr vice president', 'senior vp']:
                            if i[0] != 'svp':
                                continue
                        elif j in ['evp','executive vice president', 'executive vp']:
                            if i[0] != 'evp':
                                continue
                                
                        include.extend([k for k in i if k not in include])
                        break
                            
            return include
        
        def check2(lst, title):
            
            cleaned = []

            for p in lst:
                if re.search(rf'\b{p}\b', title):
                    for k in lst:
                        if re.search(rf'\b{k}\b', title) and title not in cleaned:
                            cleaned.append(title)
                        else:
                            temp = re.sub(rf'\b{p}\b',k,title).replace('  ', ' ')
                            if temp not in cleaned:
                                cleaned.append(temp)
                elif title not in cleaned:
                    cleaned.append(title)
                            
            return cleaned
        
        self.kw_clean = check(extra_kw, self.kw_clean)
        
        cleaned_st = []
        for i in self.kw_clean:
            for j in extra_kw:
                cleaned_st.extend(check2(j, i))
        
        self.kw_clean = cleaned_st
        self.kw_clean.extend([f'{i}s' for i in self.kw_clean if f'{i}s' not in self.kw_clean and i[-1] != 's' and len(i) > 2])
        self.kw_clean.extend([i[:-1] for i in self.kw_clean if i[:-1] not in self.kw_clean and i[-1] == 's' and len(i) > 2])
        self.kw_clean = list(set(self.kw_clean))
        self.kw_clean_extra = self.kw_clean
        
        self.sen_clean = check(extra_sen, self.sen_clean)
        self.sen_clean_extra = self.sen_clean
        
        self.exclude_kw_clean = check(extra_kw, self.exclude_kw_clean)
        
        cleaned_st = []
        for i in self.exclude_kw_clean:
            for j in extra_kw:
                cleaned_st.extend(check2(j, i))
        
        self.exclude_kw_clean = cleaned_st
        self.exclude_kw_clean.extend([f'{i}s' for i in self.exclude_kw_clean if f'{i}s' not in self.exclude_kw_clean and i[-1] != 's' and len(i) > 2])
        self.exclude_kw_clean.extend([i[:-1] for i in self.exclude_kw_clean if i[:-1] not in self.exclude_kw_clean and i[-1] == 's' and len(i) > 2])
        self.exclude_kw_clean = list(set(self.exclude_kw_clean))
        
        self.exclude_sen_clean = check(extra_sen, self.exclude_sen_clean)
        
        cleaned_st = []
        
        for i in self.jt_clean:
            for j in extra_kw_other:
                cleaned_st.extend(check2(j, i))
        
        self.jt_clean = cleaned_st
        self.jt_clean = list(set(self.jt_clean))
        
        cleaned_st = []
        
        for i in self.jt_clean:
            for j in extra_sen:
                cleaned_st.extend(check2(j, i))
        
        self.jt_clean = cleaned_st
        self.jt_clean = list(set(self.jt_clean))
        
        cleaned_st = []
        
        for i in self.exclude_jt_clean:
            for j in extra_kw_other:
                cleaned_st.extend(check2(j, i))
        
        self.exclude_jt_clean = cleaned_st
        self.exclude_jt_clean = list(set(self.exclude_jt_clean))
        
        cleaned_st = []
        
        for i in self.exclude_jt_clean:
            for j in extra_sen:
                cleaned_st.extend(check2(j, i))
        
        self.exclude_jt_clean = cleaned_st
        self.exclude_jt_clean = list(set(self.exclude_jt_clean))
                        
    def get_cosine(self, vec1, vec2):
        intersection = set(vec1.keys()) & set(vec2.keys())
        numerator = sum([vec1[x] * vec2[x] for x in intersection])
    
        sum1 = sum([vec1[x] ** 2 for x in list(vec1.keys())])
        sum2 = sum([vec2[x] ** 2 for x in list(vec2.keys())])
        denominator = math.sqrt(sum1) * math.sqrt(sum2)
    
        if not denominator:
            return 0.0
        else:
            return float(numerator) / denominator

    def text_to_vector(self, text):
        WORD = re.compile(r"\w+")
        words = WORD.findall(text)
        return Counter(words)
    
    def check_percentage_match(self):
        
        def check_between_two_words(jobtitle, word1, word2, kw = '', percent = 0.00, different = False):
            
            if type(kw) != list:
                kw = kw.split(' ')
            
            if re.search(rf'\b{word1}(?:\s+\S+){{0}}\s{word2}\b', jobtitle):
                return percent
                # if percent != 1.00:
                #     return 0.75
                # else:
                #     return 1.00
            
            if different == False:
                if re.search(rf'\b{word1}(?:\s+\S+){{0,2}}\s{word2}\b', jobtitle):
                    if kw == ['']:
                        if percent < 0.75:
                            return 0.75
                    temp = jobtitle.split(' ')
                    temp = temp[temp.index(f'{word1}'):temp.index(f'{word2}')]
                    for i in kw:
                        if i in temp:
                            if percent < 0.75:
                                return 0.75
                            break
                        else:
                            percent = 0.65
            
            else:
                if re.search(rf'\b{word1}(?:\s+\S+){{0,3}}\s{word2}\b', jobtitle):
                    if kw == ['']:
                        if percent < 0.75:
                            return 0.75
                    temp = jobtitle.split(' ')
                    temp = temp[temp.index(f'{word1}'):temp.index(f'{word2}')]
                    for i in kw:
                        if i in temp:
                            if percent < 0.75:
                                return 0.75
                            break
                        else:
                            percent = 0.00
            
            return percent
        
        def check_for_lower_sen(jobtitle, target):
            """
            Parameters
            ----------
            jobtitle : str
                cleaned jobtitle
            target : str
                target seniority, specific title or keyword
                
            Returns
            -------
            True (percentage should be 0.00) or False (percentage keep the same)
            """
            checks = ['to the chief', 'for the chief', 'ea to', 'ea for', 'pa to', 'pa for', 'office of', 'to chief', 'for chief', 'chief of staff to']
            c_level = ['cio', 'ciso', 'cto', 'cso', 'cfo', 'cmo', 'chro', 'cro', 'cco', 'cxo', 'cpo', 'cdo', 'cwo', 'ceo', 'coo', 'cao', 'cxo', 'cbo']
            
            for i in c_level:
                checks.extend([f'to the {i}', f'for the {i}', f'for {i}', f'to {i}'])
            
            delete = []
            
            for title in self.jt_clean:
                for index, check in enumerate(checks):
                    if re.search(rf'\b{title}\b', check) or re.search(rf'\b{check}\b', title):
                        delete.append(index - 1)
            
            for i in delete:
                checks.pop(i)
            
            for i in checks:
                if re.search(rf'\b{i}\b', jobtitle):
                    if re.search(rf'\b{i}\b', target):
                        pass
                    else:
                        return True
            
            return False
        
        def check_correct_sen(jobtitle, target):
            """
            Parameters
            ----------
            jobtitle : str
                jobtitle
            target : str
                seniority, specific title

            Returns
            -------
            bool
                True (percentage should be 0.00) or False (percentage keep the same)
            """
            
            check_words = ['associate', 'assoc', 'assocate', 'global head', 'group head', 'general manager']
            check = False
            
            for i in check_words:
                if i.count(' '):
                    high_perc1 = check_between_two_words(jobtitle, i[:i.index(' ')], i[i.index(' ') + 1:])
                    high_perc2 = check_between_two_words(target, i[:i.index(' ')], i[i.index(' ') + 1:])
                    if high_perc1 != 0.00 and high_perc2 != 0.00:
                        return False
                    elif high_perc1 != 0.00:
                        check = True
                    elif high_perc2 != 0.00:
                        check = True
                elif re.search(rf'\b{i}\b', jobtitle) and re.search(rf'\b{i}\b', target):
                    return False
                elif re.search(rf'\b{i}\b', jobtitle):
                    check = True
                elif re.search(rf'\b{i}\b', target):
                    check = True
                
            return check
        
        report = {}
        report_counts = {'High':0, 'Medium':0, 'Low':0}
        
        #exclude = self.exclude_kw_clean + self.exclude_sen_clean + self.exclude_jt_clean
        exclude = self.exclude_kw_clean + self.exclude_sen_clean
        
        additional_words = ['client', 'corporate', 'interim', 'founder', 'account', 'co', 'executive', 'lead', 'principle', 'senior', 'snr', 'sr', 'chief', 'afghanistan', 'africa', 'aland islands', 'albania', 'algeria', 'america', 'american', 'american samoa', 'americas', 'andorra', 'angola', 'anguilla', 'antarctica', 'antigua and barbuda', 'apac', 'area', 'argentina', 'armenia', 'aruba', 'asia', 'australia', 'austria', 'azerbaijan', 'bahamas', 'bahrain', 'bangladesh', 'barbados', 'belarus', 'belgium', 'belize', 'benelux', 'benin', 'bermuda', 'bhutan', 'big', 'bolivia', 'bosnia and herzegovina', 'botswana', 'bouvet island', 'brazil', 'british indian ocean territory', 'brunei darussalam', 'bulgaria', 'burkina faso', 'burundi', 'cabo verde', 'cambodia', 'cameroon', 'canada', 'caribbean', 'cayman islands', 'central', 'central african republic', 'chad', 'chile', 'china', 'christmas island', 'coast', 'colombia', 'comoros', 'company', 'congo', 'cook islands', 'costa rica', 'cote divoire', 'country', 'croatia', 'cuba', 'curaçao', 'cyprus', 'czechia', 'denmark', 'division', 'divisional', 'djibouti', 'dominica', 'dominican republic', 'east', 'eastern', 'ecuador', 'egypt', 'el salvador', 'emea', 'equatorial guinea', 'eritrea', 'estonia', 'eswatini', 'ethiopia', 'eu', 'europe', 'european', 'exec', 'executive', 'falkland islands', 'faroe islands', 'fiji', 'finland', 'france', 'french guiana', 'french polynesia', 'french southern territories', 'functional', 'gabon', 'gambia', 'georgia', 'germany', 'ghana', 'gibraltar', 'global', 'greece', 'greenland', 'grenada', 'group', 'guadeloupe', 'guam', 'guatemala', 'guernsey', 'guinea', 'guinea-bissau', 'guyana', 'haiti', 'heard island and mcdonald islands', 'honduras', 'hong kong', 'hungary', 'iceland', 'india', 'indonesia', 'innovation', 'institutional', 'internation', 'international', 'iran', 'iraq', 'ireland', 'isle of man', 'israel', 'italy', 'jamaica', 'japan', 'jersey', 'jordan', 'kazakhstan', 'kenya', 'kingdom', 'kiribati', 'korea', 'kuwait', 'kyrgyzstan', 'latam', 'latin', 'latvia', 'lebanon', 'lesotho', 'liberia', 'libya', 'liechtenstein', 'lithuania', 'local', 'london', 'luxembourg', 'macao', 'madagascar', 'malawi', 'malaysia', 'maldives', 'mali', 'malta', 'marshall islands', 'martinique', 'mauritania', 'mauritius', 'mayotte', 'mexico', 'middle', 'moldova', 'monaco', 'mongolia', 'montenegro', 'montserrat', 'morocco', 'mozambique', 'myanmar', 'namibia', 'national', 'nauru', 'nepal', 'netherlands', 'new caledonia', 'new zealand', 'nicaragua', 'niger', 'nigeria', 'niue', 'nordic', 'nordics', 'norfolk island', 'north', 'northeast', 'northern', 'northern mariana islands', 'norway', 'oman', 'pacific', 'pakistan', 'palau', 'palestine', 'panama', 'papua new guinea', 'paraguay', 'peru', 'philippines', 'pitcairn', 'poland', 'portugal', 'principal', 'puerto rico', 'qatar', 'region', 'regional', 'regions', 'republic of north macedonia', 'romania', 'russia', 'russian federation', 'rwanda', 'saint barthelemy', 'saint helena', 'saint kitts and nevis', 'saint lucia', 'saint martin', 'saint pierre and miquelon', 'saint vincent and the grenadines', 'samoa', 'san marino', 'sao tome and principe', 'saudi arabia', 'section', 'senegal', 'senior', 'serbia', 'seychelles', 'sierra leone', 'singapore', 'sint maarten', 'slovakia', 'slovenia', 'snr', 'solomon islands', 'somalia', 'south', 'south africa', 'south georgia and the south sandwich islands', 'south sudan', 'southeast', 'spain', 'sr', 'sri lanka', 'states', 'sudan', 'suriname', 'svalbard and jan mayen', 'sweden', 'switzerland', 'syrian arab republic', 'taiwan', 'tajikistan', 'tanzania', 'thailand', 'timor-leste', 'togo', 'tokelau', 'tonga', 'transformation', 'trinidad and tobago', 'tunisia', 'turkey', 'turkmenistan', 'turks and caicos islands', 'tuvalu', 'uganda', 'uk', 'uki', 'ukraine', 'united', 'united arab emirates', 'united kingdom of great britain and northern ireland', 'united states minor outlying islands', 'united states of america', 'uruguay', 'us', 'usa', 'uzbekistan', 'vanuatu', 'venezuela', 'viet nam', 'virgin islands', 'wallis and futuna', 'west', 'western sahara', 'worldwide', 'yemen', 'zambia']
        
        for index, jt in enumerate(self.jobtitles_clean):
            
            jt = re.sub('  ', ' ', jt)
            jt_checker = re.sub('  ', ' ', self.jobtitles_checker[index])
            temp = jt.split(" ")
        
            jt_no_add_words = jt
            
            for word in additional_words:
                if word not in exclude and word not in self.kw_clean and word not in self.sen_clean and word not in self.jt_clean:
                    jt_no_add_words = re.sub(rf'\b{word}\b', ' ', jt_no_add_words)
                    jt_no_add_words = re.sub('  ', ' ', jt_no_add_words).strip()
            
            high_perc = 0.00
            
            if self.sen_clean != [] or self.kw_clean != []:
                if self.sen_clean == [] and self.kw_clean != []:
                    for i in self.kw_clean:
                        word_or_plural = re.escape(i) + 's?'
                        if re.search(rf'\b{i}\b', jt) or re.match(word_or_plural, jt):
                            high_perc = 0.99
                            break
                else:
                    #Then check for matching with seniorities and keywords paired:
                    for index1, i in enumerate(self.sen_clean):
                        check = False
                        
                        #if associate director in jobtitle and the current seniority to check is director, continue:
                        if check_correct_sen(jt, i) == True:
                            continue
                        
                        #check that title doesn't indicate lower seniority e.g. office of the CIO
                        if check_for_lower_sen(self.jobtitles[index].lower(), i) == True:
                            continue
                        
                        if re.search(rf'\b{i}\b', jt):
                            check = 0.99
                        elif i.count(' ') <= 3: #if the seniority has 2 words, we want to see if there are words between:
                            temp1 = i.split(' ')
                            word1 = temp1[0]
                            word2 = temp1[-1]
                            check = check_between_two_words(jt, word1, word2)
                        
                        if self.sen_clean != [] and self.kw_clean == []:
                            if check >= 0.75:
                                high_perc = 0.99
                            break

                        elif check != 0.00:
                            
                            temp_list1 = self.kw_clean + self.jt_clean
                            temp_list2 = self.kw_clean_extra + self.jt_clean_extra
                            
                            for index2, j in enumerate(temp_list1): #for index2, j in enumerate(self.kw_clean):
                                
                                if re.search(rf'\b{j}\b', jt):
                                    keywords = []
                                    
                                    #want to check keywords combined as well with the seniority to see if percentage is stronger:
                                    for k in temp_list1:
                                        if k == j:
                                            vector1 = self.text_to_vector(jt)
                                            vector2 = self.text_to_vector(f'{i} {j}')
                                            cosine = round(self.get_cosine(vector1, vector2),2)
    
                                        else:
                                            vector1 = self.text_to_vector(jt)
                                            vector2 = self.text_to_vector(f'{i} {j} {k}')
                                            cosine1 = round(self.get_cosine(vector1, vector2),2)  
                                            
                                            keywords.append(k)
                                            vector1 = self.text_to_vector(jt)
                                            vector2 = self.text_to_vector(f'{i} {" ".join(keywords)}')
                                            cosine2 = round(self.get_cosine(vector1, vector2),2)  
                                            
                                            if cosine1 >= cosine2:
                                                cosine = cosine1
                                            else:
                                                cosine = cosine2
                                        
                                        checker = False
                                        
                                        if cosine == 1.00:
                                            
                                            if jt != jt_checker:
                                                cosine = 0.99
                                                
                                            high_perc = cosine
                                            break
    
                                        if i == 'chief' and checker == False:
                                            #need to make sure that if it matches with chief, it is a chief officer
                                            cosine = check_between_two_words(jt, 'chief', 'officer', j, 0.00, different = True)
                                            checker = True
                                    
                                        # if cosine >= 0.65:
                                            # print(self.kw_clean_extra[index2])
                                            # print(self.sen_clean_extra[index1])
                                            # print(check_title)
                                            #if jt starts with relevant title, we want it to be a strong match
                                        if cosine > 0.20:
                                            original_cosine = cosine
                                            if checker == False:
                                                #allow 1 or 0 words between the seniority and keyword - the clean_extra removes additional_words.
                                                try:
                                                    if re.search(rf'\b{temp_list2[index2]}(?:\s+\S+){{0,1}}\s{self.sen_clean_extra[index1]}\b', jt_no_add_words).start() == 0:
                                                        if original_cosine >= 0.65:
                                                            cosine = 0.75
                                                        else:
                                                            cosine = 0.65
                                                        checker = True
                                                    else:
                                                        if original_cosine >= 0.65:
                                                            cosine = 0.65
                                                        else:
                                                            cosine = 0.64
                                                except:
                                                    if original_cosine >= 0.65:
                                                        cosine = 0.65
                                                    else:
                                                        cosine = 0.64
                                                    
                                            if checker == False:
                                                try:
                                                    if re.search(rf'\b{self.sen_clean_extra[index1]}(?:\s+\S+){{0,1}}\s{temp_list2[index2]}\b', jt_no_add_words).start() == 0:
                                                        if original_cosine >= 0.65:
                                                            cosine = 0.75
                                                        else:
                                                            cosine = 0.65
                                                        checker = True
                                                    else:
                                                        if original_cosine >= 0.65:
                                                            cosine = 0.65
                                                        else:
                                                            cosine = 0.64
                                                except:
                                                    if original_cosine >= 0.65:
                                                        cosine = 0.65
                                                    else:
                                                        cosine = 0.64
                                                    
                                            if checker == False:
                                                #allow 1 or 0 words between the seniority and keyword - the clean_extra removes additional_words.
                                                try:
                                                    if re.search(rf'\b{i}(?:\s+\S+){{0,1}}\s{j}\b', jt_no_add_words).start() == 0:
                                                        if original_cosine >= 0.65:
                                                            cosine = 0.75
                                                        else:
                                                            cosine = 0.65
                                                        checker = True
                                                    else:
                                                        if original_cosine >= 0.65:
                                                            cosine = 0.65
                                                        else:
                                                            cosine = 0.64
                                                except:
                                                    if original_cosine >= 0.65:
                                                        cosine = 0.65
                                                    else:
                                                        cosine = 0.64
                                                    
                                            if checker == False:
                                                try:
                                                    if re.search(rf'\b{j}(?:\s+\S+){{0,1}}\s{i}\b', jt).start() == 0:
                                                        if original_cosine >= 0.65:
                                                            cosine = 0.75
                                                        else:
                                                            cosine = 0.65
                                                        checker = True
                                                    else:
                                                        if original_cosine >= 0.65:
                                                            cosine = 0.65
                                                        else:
                                                            cosine = 0.64
                                                except:
                                                    if original_cosine >= 0.65:
                                                        cosine = 0.65
                                                    else:
                                                        cosine = 0.64               

                                            if cosine > high_perc:
                                                high_perc = cosine
                                                
                                        elif cosine > 0 and cosine > high_perc:
                                            high_perc = cosine
                                        
                        if high_perc == 1.00:
                            break

            #Exact titles:
            if self.jt_clean != [] and high_perc != 1.00:
                for index3, w in enumerate(self.jt_clean):
                    check = False
                    
                    #check that title doesn't indicate lower seniority e.g. office of the CIO
                    if check_for_lower_sen(self.jobtitles[index].lower(), w):
                        continue
                    
                    if check_correct_sen(jt, w) == True:
                        continue
                    
                    jt_temp = w.split(' ')
                    test = [i for i in jt_temp if i in temp]

                    if len(test) == len(jt_temp) or re.search(rf'\b{w}\b', jt):
                        
                        vector1 = self.text_to_vector(jt)
                        vector2 = self.text_to_vector(f'{w}')
                        cosine = round(self.get_cosine(vector1, vector2),2)
                        
                        if cosine == 1.00:
                            if jt != jt_checker:
                                cosine = 0.99
                                    
                            high_perc = cosine
                            break
                        elif cosine > 0.20:
                            checker = False
                            
                            try:
                                if re.search(rf'\b{w}\b', jt).start() == 0:
                                    if cosine < 0.65:
                                        cosine = 0.65
                                # if re.search(rf'\b{w}\b', jt):
                                #     if cosine < 0.65:
                                #         cosine = 0.65
                            except:
                                pass
                            
                            if re.search(r'\bchief\b', jt) and re.search(r'\bofficer\b', jt):
                                if re.search(r'\bofficer\b', w):
                                    pass
                                else:
                                    cosine = 0.00
                                    checker = True
                            
                            if re.search(r'\bchief\b', w) and re.search(r'\bofficer\b', w):
                                cosine = check_between_two_words(jt, 'chief', 'officer', kw = self.kw_clean, percent = cosine, different = True)
                                checker = True
                            
                            if checker != True:
                                if w.count(' ') == 1:
                                    cosine = check_between_two_words(jt, w[:w.index(' ')], w[w.index(' ') + 1:], kw = self.kw_clean, percent = cosine)
                                    checker = True
                            
                            # if cosine >= 0.65 and checker != True:
                            
                            original_cosine = cosine

                            if checker == False:
                                if self.jt_clean_extra[index3].count(' ') == 1:
                                    word1 = self.jt_clean_extra[index3][:self.jt_clean_extra[index3].index(' ')]
                                    word2 = self.jt_clean_extra[index3][self.jt_clean_extra[index3].index(' ') + 1:]
                                    
                                    try:
                                        if re.search(rf'\b{word1}(?:\s+\S+){{0,2}}\s{word2}\b', jt).start() == 0:
                                            if original_cosine >= 0.65:
                                                cosine = 0.75
                                            else:
                                                cosine = 0.65
                                            checker = True
                                        else:
                                            if original_cosine >= 0.65:
                                                cosine = 0.65
                                            else:
                                                cosine = 0.64
                                    except:
                                        if original_cosine >= 0.65:
                                            cosine = 0.65
                                        else:
                                            cosine = 0.64
                                    
                                    if checker == False:
                                        try:
                                            if re.search(rf'\b{word2}(?:\s+\S+){{0,2}}\s{word1}\b', jt).start() == 0:
                                                if original_cosine >= 0.65:
                                                    cosine = 0.75
                                                else:
                                                    cosine = 0.65
                                                checker = True
                                            else:
                                                if original_cosine >= 0.65:
                                                    cosine = 0.65
                                                else:
                                                    cosine = 0.64
                                        except:
                                            if original_cosine >= 0.65:
                                                cosine = 0.65
                                            else:
                                                cosine = 0.64
                                
                                if checker == False:

                                    try:
                                        if re.search(rf'\b{self.jt_clean_extra[index3]}\b', jt_no_add_words).start() == 0: #or re.search(rf'\b{self.jt_clean_extra[index3]}\b', jt_no_add_words).end() == len(jt):
                                            cosine = 0.75
                                            checker = True
                                            # if original_cosine >= 0.65:
                                            #     cosine = 0.75
                                            # else:
                                            #     cosine = 0.65
                                            # checker = True
                                        else:
                                            if original_cosine >= 0.65:
                                                cosine = 0.65
                                            else:
                                                cosine = 0.64
                                    except:
                                        if original_cosine >= 0.65:
                                            cosine = 0.65
                                        else:
                                            cosine = 0.64
                                
                                if checker == False:
                                    try:
                                        if re.search(rf'\b{w}\b', jt).start() == 0: #or re.search(rf'\b{w}\b', jt).end() == len(jt):
                                            if original_cosine >= 0.65:
                                                cosine = 0.75
                                            else:
                                                cosine = 0.65
                                            checker = True
                                        else:
                                            if original_cosine >= 0.65:
                                                cosine = 0.65
                                            else:
                                                cosine = 0.64
                                    except:
                                        if original_cosine >= 0.65:
                                            cosine = 0.65
                                        else:
                                            cosine = 0.64
                            
                                if cosine > high_perc:
                                    high_perc = cosine
                                
                        if cosine > high_perc:
                            high_perc = cosine
                            
            #Exclusion checker - set to 2.00 if found:
            if high_perc != 0.00 and (exclude != [] or self.exclude_jt_clean != []):
                for o in exclude:
                    if re.search(rf'\b{o}\b', jt):
                        high_perc = 2.00
                        break
                
                if high_perc != 2.00:
                    for index4, i in enumerate(self.exclude_jt_clean):
                        if re.search(rf'\b{i}\b', jt):
                            high_perc = 2.00
                            break
                        else:
                            if self.exclude_jt_clean[index4].count(' ') > 0:
                                temp1 = self.exclude_jt_clean[index4].split(' ')
                                word1 = temp1[0]
                                word2 = temp1[-1]
                                
                                if re.search(rf'\b{word1}\b', jt) and re.search(rf'\b{word2}\b', jt):
                                    kw1 = temp1[temp1.index(word1) + 1:temp1.index(word2)]
                                    temp1 = jt.split(' ')
                                    kw2 = temp1[temp1.index(word1) + 1:temp1.index(word2)]
                                    
                                    test = [j for j in kw1 if j in kw2]
                                    
                                    if len(kw1) == len(test):
                                        high_perc = 2.00
                                        break    
            
            if high_perc == 0.00:
                report[self.jobtitles[index]] = 'No match'
                report_counts['Low'] += 1
            elif high_perc == 2.00:
                report[self.jobtitles[index]] = 'Exclude'
                report_counts['Low'] += 1
            elif high_perc == 1.00:
                report[self.jobtitles[index]] = 'Clean match'
                report_counts['High'] += 1
            elif high_perc < 1.00 and high_perc >= 0.75:
                report[self.jobtitles[index]] = 'Strong match'
                report_counts['High'] += 1
            elif high_perc < 0.75 and high_perc >= 0.65: #0.60 before
                report[self.jobtitles[index]] = 'Medium match'
                report_counts['Medium'] += 1
            else:
                report[self.jobtitles[index]] = 'Weak match'
                report_counts['Low'] += 1
            
        return report, report_counts
    
    def hello(self):

        print(f'User jobtitles: {self.jobtitles_clean}')
        print(f'Relevant keywords: {self.kw_clean}')
        print(f'Relevant seniorities: {self.sen_clean}')
        print(f'Relevant jobtitles: {self.jt_clean}')
        print(f'Exclusion keywords: {self.exclude_kw_clean}')
        print(f'Exclusion seniorities: {self.exclude_sen_clean}')
        print(f'Exclusion jobtitles: {self.exclude_jt_clean}')
        
class CompanyMatch(JobTitleMatch):

    def __init__(self, companies = [], targets = [], exclude = []):
        self.companies = companies
        self.targets = targets
        self.exclude = exclude
        
        #same as above but without punctuation, lowercase, and with english characters
        self.companies_clean = [unidecode(re.sub(r"[^\w\s]", "", j)).lower().strip().replace("  ", " ") for j in companies]
        self.targets_clean = [unidecode(re.sub(r"[^\w\s]", "", j)).lower().strip().replace("  ", " ") for j in targets]
        self.exclude_clean = [unidecode(re.sub(r"[^\w\s]", "", j)).lower().strip().replace("  ", " ") for j in exclude]
        
    def remove_company_extensions(self):
        
        company_adds = ['group', '3ao', '3at', 'a', 'aat', 'ab', 'account', 'ad', 'adsitz', 'ae', 'afghanistan', 'africa', 'ag', 'aj', 'akc spol', 'aland islands', 'albania', 'algeria', 'amba', 'america', 'american', 'american samoa', 'americas', 'an', 'and', 'and company', 'andorra', 'angola', 'anguilla', 'ans', 'antarctica', 'antigua and barbuda', 'apac', 'area', 'argentina', 'armenia', 'aruba', 'as', 'as oy', 'asa', 'asia', 'asoy', 'at', 'australia', 'austria', 'ay', 'azerbaijan', 'ba', 'bahamas', 'bahrain', 'bangladesh', 'bank', 'barbados', 'belarus', 'belgium', 'belize', 'benelux', 'benin', 'bermuda', 'bhd', 'bhutan', 'big', 'bl', 'bm', 'bolivia', 'bosnia and herzegovina', 'botswana', 'bouvet island', 'brazil', 'british indian ocean territory', 'brunei darussalam', 'bulgaria', 'burkina faso', 'burundi', 'bv', 'bvba', 'c por a', 'ca', 'cabo verde', 'cambodia', 'cameroon', 'canada', 'caribbean', 'cayman islands', 'cbva', 'central', 'central african republic', 'chad', 'chief', 'chile', 'china', 'christmas island', 'cic', 'cio', 'client', 'co', 'coast', 'colombia', 'commv', 'comoros', 'company', 'congo', 'cook islands', 'coop', 'corp', 'corporate', 'corporation', 'costa rica', 'cote divoire', 'country', 'cpt', 'crl', 'croatia', 'cuba', 'curaçao', 'cv', 'cvoa', 'cxa', 'cyprus', 'czechia', 'da', 'dat', 'dd', 'ddo', 'denmark', 'division', 'divisional', 'djibouti', 'dno', 'do', 'dominica', 'dominican republic', 'doo', 'dooel', 'ead', 'east', 'eastern', 'ec', 'ecuador', 'eg', 'egypt', 'ehf', 'ei', 'eirl', 'el salvador', 'emea', 'ent', 'ep', 'epe', 'equatorial guinea', 'eritrea', 'estonia', 'esv', 'eswatini', 'et', 'etat', 'ethiopia', 'eu', 'eurl', 'europe', 'european', 'ev', 'exec', 'executive', 'fa', 'falkland islands', 'faroe islands', 'fcp', 'fie', 'fiji', 'finland', 'fkf', 'fmba', 'fop', 'founder', 'france', 'french guiana', 'french polynesia', 'french southern territories', 'functional', 'gabon', 'gambia', 'gbr', 'georgia', 'germany', 'gesbr', 'ghana', 'gibraltar', 'gie', 'global', 'gmbh', 'gmbh  co kg', 'gp', 'greece', 'greenland', 'grenada', 'gs', 'gte', 'guadeloupe', 'guam', 'guatemala', 'guernsey', 'guinea', 'guinea-bissau', 'guyana', 'haiti', 'has', 'hb', 'heard island and mcdonald islands', 'hf', 'honduras', 'hong kong', 'hungary', 'iceland', 'ij', 'ik', 'iks', 'in', 'inc', 'incorporated', 'india', 'indonesia', 'innovation', 'institutional', 'interim', 'internation', 'international', 'iran', 'iraq', 'ireland', 'is', 'isle of man', 'israel', 'italy', 'jamaica', 'japan', 'jersey', 'jordan', 'jtd', 'kazakhstan', 'kb', 'kd', 'kda', 'kenya', 'kf', 'kft', 'kg', 'kgaa', 'kht', 'kingdom', 'kiribati', 'kkt', 'koop', 'korea', 'ks', 'kt', 'kuwait', 'kv', 'ky', 'kyrgyzstan', 'latam', 'latin', 'latvia', 'lda', 'lead', 'lebanon', 'lesotho', 'liberia', 'libya', 'liechtenstein', 'limited', 'lithuania', 'llc', 'llp', 'local', 'london', 'lp', 'ltd', 'ltda', 'luxembourg', 'macao', 'madagascar', 'malawi', 'malaysia', 'maldives', 'mali', 'malta', 'marshall islands', 'martinique', 'mauritania', 'mauritius', 'mayotte', 'mb', 'mchj', 'mepe', 'mexico', 'middle', 'moldova', 'monaco', 'mongolia', 'montenegro', 'montserrat', 'morocco', 'mozambique', 'my', 'myanmar', 'namibia', 'national', 'nauru', 'nepal', 'netherlands', 'new caledonia', 'new zealand', 'nicaragua', 'niger', 'nigeria', 'niue', 'nl', 'nordic', 'nordics', 'norfolk island', 'north', 'northeast', 'northern', 'northern mariana islands', 'norway', 'nuf', 'nv', 'nyrt', 'oaj', 'oao', 'obrt', 'od', 'oe', 'of', 'og', 'ohf', 'ohg', 'ok', 'oman', 'ong', 'ooo', 'ovee', 'oy', 'oyj', 'pacific', 'pakistan', 'palau', 'palestine', 'panama', 'papua new guinea', 'paraguay', 'partg', 'peec', 'peru', 'philippines', 'pitcairn', 'plc', 'plc ltd', 'pllc', 'poland', 'portugal', 'pp', 'principal', 'principle', 'ps', 'pse', 'psu', 'pt', 'pte', 'pte ltd', 'pty ltd', 'puerto rico', 'pvt ltd', 'qatar', 'qk', 'qmj', 'region', 'regional', 'regions', 'republic of north macedonia', 'rhf', 'romania', 'rt', 'russia', 'russian federation', 'rwanda', 's de rl', 's en c', 'sa', 'saa', 'sab', 'sad', 'sae', 'sagl', 'saint barthelemy', 'saint helena', 'saint kitts and nevis', 'saint lucia', 'saint martin', 'saint pierre and miquelon', 'saint vincent and the grenadines', 'sal', 'samoa', 'san marino', 'sao tome and principe', 'saoc', 'saog', 'sapa', 'sapi', 'sarl', 'sas', 'sasu', 'saudi arabia', 'sc', 'sca', 'sccl', 'sce i', 'scoop', 'scop', 'scpa', 'scra', 'scrl', 'scs', 'sd', 'sdn bhd', 'se', 'secs', 'section', 'sem', 'senegal', 'senior', 'sep', 'serbia', 'ses', 'seychelles', 'sf', 'sgps', 'sgr', 'sha', 'shpk', 'sia', 'sicav', 'sierra leone', 'singapore', 'sint maarten', 'ska', 'sl', 'sll', 'slne', 'slovakia', 'slovenia', 'sm pte ltd', 'smba', 'snc', 'snr', 'soccol', 'sogepa', 'solomon islands', 'somalia', 'south', 'south africa', 'south georgia and the south sandwich islands', 'south sudan', 'southeast', 'sp', 'sp zoo', 'spa', 'spain', 'spj', 'spk', 'spp', 'sprl', 'sr', 'sri lanka', 'srl', 'sro', 'ss', 'states', 'stg', 'suc de descendants', 'sudan', 'suriname', 'svalbard and jan mayen', 'sweden', 'switzerland', 'syrian arab republic', 'taiwan', 'tajikistan', 'tanzania', 'tapui', 'tdv', 'teo', 'thailand', 'the', 'timor-leste', 'tmi', 'to', 'togo', 'tokelau', 'tonga', 'tov', 'transformation', 'trinidad and tobago', 'tunisia', 'turkey', 'turkmenistan', 'turks and caicos islands', 'tuvalu', 'uab', 'ud', 'uganda', 'uk', 'uki', 'ukraine', 'ultd', 'united', 'united arab emirates', 'united kingdom of great britain and northern ireland', 'united states minor outlying islands', 'united states of america', 'unltd', 'uruguay', 'us', 'usa', 'uzbekistan', 'vanuatu', 'vat', 'venezuela', 'viet nam', 'virgin islands', 'vof', 'vos', 'vzw', 'wallis and futuna', 'west', 'western sahara', 'worldwide', 'xk', 'xt', 'xxk', 'yemen', 'yoaj', 'zambia', 'zao', 'zat', 'zrt']
        
        def clean(comps, company_adds):
            
            temp = []
            
            for i in comps:
                comp = i.split(' ')
                comp = [i for i in comp if i not in company_adds]
                if comp == []:
                    temp.append(i)
                    continue
                temp.append(' '.join(comp))
            
            return temp
        
        self.companies_clean = clean(self.companies_clean, company_adds)
        self.targets_clean = clean(self.targets_clean, company_adds)
        self.exclude_clean = clean(self.exclude_clean, company_adds)
        
    def add_other_variations(self):
        
        #variations = {'bally':['bally manufacturing', 'bally entertainment'], 'abba seafood':['abba'], 'abc':['american broadcasting'], 'abloy':['assa abloy'], 'adobe systems':['adobe'], 'aflac':['american family life assurance columbus'], 'ahlstrom':['ahlstrom munksjo'], 'ahold':['koninklijke ahold', 'ahold delhaize'], 'akamai':['akamai technologies'], 'akzo':['akzo nobel', 'akzonobel'], 'alcatellucent':['lucent technologies'], 'alfa romeo':['alfa romeo automobiles'], 'alibaba group':['alibaba'], 'alltel wireless':['alltel'], 'amazoncom':['amazon'], 'ambev':['inbev', 'ambev', 'anheuserbusch inBev'], 'amc theatres':['amc entertainment'], 'amd':['advanced micro devices'], 'amkor':['amkor technology'], 'arp':['arp instruments'], 'artis':['natura artis magistra'], 'asda':['asda stores'], 'aston martin':['aston martin lagonda'], 'asus':['asustek computer']}
        variations = {'rb':['reckitt benckiser'], 'hp':['hewlett packard'], 'gsk':['glaxosmithkline'], 'facebook':['meta'], 'ey':['ernst & young'], 'ea':['electronic arts'], 'bbc':['british broadcasting company'],'bt':['british telecom'], 'london stock exchange':['lseg', 'london stock exchange lseg', 'lseg london stock exchange', 'lseg london stock exchange group'], 'lch':['london clearing house'], 'onesavings bank':['osb group'], 'liverpool victoria':['lv'], 'bank america':['bofa'], 'american express':['amex'], 'aflac':['american family life assurance columbus'], 'akzo':['akzonobel'], 'alcatellucent':['lucent technologies'], 'amazon':['amazoncom'], 'ambev':['inbev', 'anheuserbusch inBev'], 'amc theatres':['amc entertainment'], 'amd':['advanced micro devices'], 'asus':['asustek computer']}
        
        def check_for_var(comp, variations):
            
            for i in variations.keys():
                if re.search(rf'\b{i}\b', comp) or re.search(rf'\b{comp}\b', i):
                    return_list = [i]
                    return_list.extend(variations[i])
                    return return_list
                for j in variations[i]:
                    if re.search(rf'\b{j}\b', comp) or re.search(rf'\b{comp}\b', j):
                        return_list = [i]
                        return_list.extend(variations[i])
                        return return_list
                
            return False
        
        extra_targets = []
        extra_targets2 = []
        
        for index, comp in enumerate(self.targets_clean):
            extra = check_for_var(comp, variations)
            if extra != False:
                extra_targets.extend([f'{i}:{self.targets[index]}' for i in extra if i not in self.targets_clean])
                extra_targets2.extend([f'{self.targets[index]}' for i in extra if i not in self.targets_clean])
                
        self.targets_clean.extend(extra_targets)
        self.targets.extend(extra_targets2)
                
        extra_exclude = []
        for index, comp in enumerate(self.exclude_clean):
            extra = check_for_var(comp, variations)
            if extra != False:
                extra_exclude.extend([f'{i}:{self.exclude[index]}' for i in extra if i not in self.exclude_clean])
        
        self.exclude_clean.extend(extra_exclude)
        
    def check_percentage_match(self):
        
        report = {}
        report_counts = {'High':0, 'Medium':0, 'Low':0}
        matched_companies = {}
        
        for index, comp in enumerate(self.companies_clean):
            
            high_perc = 0.00
            
            key = ''
            value = ''
            
            for index1, i in enumerate(self.exclude_clean):
                
                if ':' in i:
                    temp = i[:i.index(':')]
                else:
                    temp = i
                    
                if re.search(rf'\b{temp}\b', self.companies[index]) or re.search(rf'\b{self.companies[index]}\b', temp):
                    high_perc = 2.00
                    if ':' in i:
                        # key = temp
                        # value = i[i.index(':') + 1:]
                        key = self.companies[index]
                        value = i[i.index(':') + 1:]
                    else:
                        key = self.companies[index]
                        value = self.exclude[index1]
                    break
            
            if high_perc == 0.00:
                
                for index2, j in enumerate(self.targets_clean):
                    
                    if j == '':
                        continue
                    
                    if ':' in j:
                        temp = j[:j.index(':')]
                    else:
                        temp = j
                    
                    if re.search(rf'\b{temp}\b', comp) or re.search(rf'\b{comp}\b', temp):
                        pass
                    else:
                        continue
                    
                    # test1 = [p.lower() for p in self.companies[index].split()]
                    # test2 = [o.lower() for o in self.targets[index2].split()]
                    
                    # print(test1)
                    # print(test2)
                    
                    # if (len(test1) == 2 or len(test2) == 2) and comp != temp:
                    #     if len(test1) > len(test2):
                    #         result = [s for s in test2 if s in test1]
                    #         if len(result) != len(test2):
                    #             continue
                    #     else:
                    #         result = [s for s in test1 if s in test2]
                    #         if len(result) != len(test1):
                    #             continue
                    
                    if temp.strip() == comp.strip() or self.companies[index].lower().strip() == self.targets[index2].lower().strip():
                        if self.companies[index].lower().strip() == self.targets[index2].lower().strip():
                            high_perc = 1.00
                        elif self.companies[index].lower().strip() != self.targets[index2].lower().strip():
                            high_perc = 0.70
                        elif temp not in [k.lower() for k in self.targets] or comp not in [k.lower() for k in self.companies]:
                            high_perc = 0.70
                        else:
                            high_perc = 1.00
                            
                        if ':' in j:
                            # key = temp
                            # value = i[i.index(':') + 1:]
                            key = self.companies[index]
                            value = j[j.index(':') + 1:]
                        else:
                            key = self.companies[index]
                            value = self.targets[index2]
                        
                        if high_perc == 1.00:
                            break
                    
                    temp2 = temp
                    comp2 = comp
                    
                    if ' ' not in temp2:
                        if temp2[-1] == 's':
                            temp2 = temp2[:-1]
                            
                    if ' ' not in comp2:
                        if comp2[-1] == 's':
                            comp2 = comp2[:-1]
                    
                    try:
                        if ' ' in temp and ' ' in comp and temp.split()[0] not in comp.split() and comp.split()[0] not in temp.split():  
                            if (temp2 != temp or comp2 != comp) and temp2.split()[0] not in comp2.split() and comp2.split()[0] not in temp2.split():
                                pass
                            else:
                                continue
                    except:
                        pass
                    
                    # try:
                    #     if re.search(rf'\b{temp}\b', comp).start() == 0:
                    #         cosine = 0.99
                    # except:
                    #     try:
                    #         if re.search(rf'\b{comp}\b', temp).start() == 0:
                    #             cosine = 0.99
                    #     except:
                        
                    vector1 = self.text_to_vector(comp)
                    vector2 = self.text_to_vector(temp)
                    cosine = round(self.get_cosine(vector1, vector2),2)
                    
                    
                    #if either company is 1 word, then it needs to be first word in both to be strong match
                    #if first word of both company is not found in each, then cannot be a match at all.
                    
                    
                    if cosine < 1.00 and cosine >= 0.70:
                        check = False
                        try:
                            if re.search(rf'\b{temp}\b', comp).start() == 0:
                                check = True
                            else:
                                pass
                        except:
                            pass
                        
                        try:
                            if re.search(rf'\b{comp}\b', temp).start() == 0:
                                check = True
                            else:
                                pass
                        except:
                            pass
                        
                        if check == False:
                            cosine = 0.69

                    if cosine == 1.00:
                        if temp not in self.targets or comp not in self.companies:
                            high_perc = 0.70
                        else:
                            high_perc = 1.00
                        
                        if ':' in j:
                            # key = temp
                            # value = i[i.index(':') + 1:]
                            key = self.companies[index]
                            value = j[j.index(':') + 1:]
                        else:
                            key = self.companies[index]
                            value = self.targets[index2]
                        if high_perc == 1.00:
                             break
                    
                    elif cosine > high_perc and cosine >= 0.5:
                        if len(temp.split()) < len(self.targets[index2].split()) or len(comp.split()) < len(self.companies[index].split()):
                            cosine = 0.69
                        
                        high_perc = cosine
                        
                        if ':' in j:
                            # key = temp
                            # value = i[i.index(':') + 1:]
                            key = self.companies[index]
                            value = j[j.index(':') + 1:]
                        else:
                            key = self.companies[index]
                            value = self.targets[index2]
                    
                    elif cosine > high_perc and cosine > 0:
                        if temp.split()[0] == comp.split()[0]:
                            high_perc = 0.5
                            
                            if ':' in j:
                                # key = temp
                                # value = i[i.index(':') + 1:]
                                key = self.companies[index]
                                value = j[j.index(':') + 1:]
                            else:
                                key = self.companies[index]
                                value = self.targets[index2]
                    
                    else:
                        if re.sub(' ', '', comp2) == re.sub(' ', '', temp2):
                            high_perc = 1.00
                            
                            if ':' in j:
                                # key = temp
                                # value = i[i.index(':') + 1:]
                                key = self.companies[index]
                                value = j[j.index(':') + 1:]
                            else:
                                key = self.companies[index]
                                value = self.targets[index2]
                                
                        elif temp2 != temp or comp2 != comp:
                            vector1 = self.text_to_vector(temp2)
                            vector2 = self.text_to_vector(comp2)
                            cosine = round(self.get_cosine(vector1, vector2),2)

                            if cosine > high_perc and cosine >= 0.5:
                                high_perc = cosine
                            
                                if ':' in j:
                                    # key = temp
                                    # value = i[i.index(':') + 1:]
                                    key = self.companies[index]
                                    value = j[j.index(':') + 1:]
                                else:
                                    key = self.companies[index]
                                    value = self.targets[index2]
                                
                                if high_perc == 1.0:
                                    break
                                    
            
            if key != '' and high_perc != 0.00:
                matched_companies[key] = value
        
            if high_perc == 0.00:
                report[self.companies[index]] = 'No match'
                report_counts['Low'] += 1
            elif high_perc == 2.00:
                report[self.companies[index]] = 'Exclude'
                report_counts['Low'] += 1
            elif high_perc == 1.00:
                report[self.companies[index]] = 'Clean match'
                report_counts['High'] += 1
            elif high_perc < 1.00 and high_perc >= 0.70:
                report[self.companies[index]] = 'Strong match'
                report_counts['High'] += 1
            elif high_perc < 0.70 and high_perc > 0.50:
                report[self.companies[index]] = 'Medium match'
                report_counts['Medium'] += 1
            else:
                report[self.companies[index]] = 'Weak match'
                report_counts['Low'] += 1
            
        return report, report_counts, matched_companies
    
    def hello(self):
        
        print(f'User companies: {self.companies_clean}')
        print(f'Relevant companies: {self.targets_clean}')
        print(f'Exclusion companies: {self.exclude_clean}')

class handler(BaseHTTPRequestHandler):

    def do_POST(self):
        self.send_response(200)
        self.end_headers()

        self.data_string = self.rfile.read(int(self.headers['Content-Length']))

        data = simplejson.loads(self.data_string)
        print(data)
        
        # DB variables to login
        key: str = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
        url = os.environ.get("NEXT_PUBLIC_SUPABASE_URL") 
        supabase: Client = supa_create_client(url, key)
 
        try:
            test = JobTitleMatch(
                jobtitles=list(set(data["jobtitles"])),
                kw=data["kw"],
                exclude_kw=data["exclude_kw"],
                sen=data["sen"],
                exclude_sen=data["exclude_sen"],
                jt=data["jt"],
                exclude_jt=data["exclude_jt"]
            )

            test.remove_filler_words_from_jts()

            test.add_extra_titles()

            a = test.check_percentage_match()

            unique_jts = len(set(data["jobtitles"]))

            test2 = CompanyMatch(
                companies=list(set(data["companies"])),
                targets=data["include_companies"],
                exclude=data["exclude_companies"])

            test2.add_other_variations()
            
            test2.remove_company_extensions()

            b = test2.check_percentage_match()

            unique_comps = len(set(data["companies"]))

            comp_report_sum = b[1]
            jt_report_sum = a[1]

            # make unique url for the file name to be stored at
            str = data["user_id"]+"/"+data["id"]+"/"+data["file_name"]+".csv"

            # update the row in the db with a completed row with results
            supabase.table("results").update(
                {   
                    "comp_high": comp_report_sum["High"],
                    "comp_medium": comp_report_sum["Medium"],
                    "comp_low": comp_report_sum["Low"],
                    "job_title_high": jt_report_sum["High"],
                    "job_title_medium": jt_report_sum["Medium"],
                    "job_title_low": jt_report_sum["Low"],
                    "job_title_unique_count": unique_jts,
                    "comp_unique_count": unique_comps,
                    "is_processing": False,
                    "row_count": unique_comps + unique_jts ,
                    "file": str}).eq("id", data["id"]).execute()

            # open client connection from file storage
            storage_client = create_client(url+ "/storage/v1", {"apiKey": key, "Authorization": f"Bearer {key}"}, is_async=False)

            # make temp file
            new_file, filename = tempfile.mkstemp(suffix='.csv')

            # write in temp file from the results
            jobtitle_match = [a[0][titles] for titles in data["jobtitles"]]
            company_match = [b[0][compny] for compny in data["companies"]]
            company_targets = []
            for i in data["companies"]:
                if i in b[2]:
                    company_targets.append(b[2][i])
                else:
                    company_targets.append('')

            if len(data["jobtitles"]) > len(data["companies"]) and data["jobtitles"] != [] and data["companies"] != []:
                for i in range(len(company_match), len(jobtitle_match) + 1):
                    company_match.append('')
                    company_targets.append('')
                    data["companies"].append('')

            if data["jobtitles"] != [] and data["companies"] != []:
                headers = ['Jobtitles', 'Jobtitles group', 'Companies', 'Companies group', 'Companies match']
            elif data["jobtitles"] != [] and data["companies"] == []:
                headers = ['Jobtitles', 'Jobtitles group']
            elif data["jobtitles"] == [] and data["companies"] != []:
                headers = ['Companies', 'Companies group', 'Companies match']

            # write in temp file from the results
            with open(filename, 'w', encoding='UTF8', newline='') as csv_file:
                writer = csv.writer(csv_file)
                writer.writerow(headers)

                if data["jobtitles"] != [] and data["companies"] != []:
                    for index, i in enumerate(data["jobtitles"]):
                        writer.writerow([i, jobtitle_match[index], data["companies"][index], company_match[index], company_targets[index]])
                elif data["jobtitles"] != [] and data["companies"] == []:
                    for index, i in enumerate(data["jobtitles"]):
                        writer.writerow([i, jobtitle_match[index]])
                elif data["jobtitles"] == [] and data["companies"] != []:
                    for index, i in enumerate(data["companies"]):
                        writer.writerow([i, company_match[index], company_targets[index]])

            # store new file on the db
            storage_client.get_bucket("reports").upload(str, new_file)

            os.close(new_file)

            self.wfile.write(json.dumps({'received': 'ok'}).encode())

            return
        
        except Exception as e:
            print("has error")
            print(e)
            
            supabase.table("results").update(
            { 
                "error": "Failed to process data",
                "is_processing": False
            }).eq("id", data["id"]).execute()
            
            self.wfile.write(json.dumps({'received': 'failed'}).encode())

            return 
