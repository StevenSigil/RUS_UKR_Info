from django.forms.models import model_to_dict
from Data.models import City, State, Country

import json
import spacy


# TODO Make and run tests to check accuracy of desired outcome for parsers that store!

TESTINGTEXT = "He did this to John."


def setup_spacy(text=TESTINGTEXT):
    nlp = spacy.load("en_core_web_sm")
    nlp.add_pipe('merge_entities')
    nlp.add_pipe('merge_noun_chunks')
    nlp.add_pipe('emoji', first=True)

    return nlp(text)  # doc


def check_token_is_place(token: spacy.tokens.token.Token, is_GPE: bool = False):
    ''' Checks if the token is a Proper-Noun (PROPN).
        If so, searches to check if the token is a City, State, or Country (in db)
        Uses the most likely match from `compare_strings()` 
        Returns: City | State | Country instance -OR- bool(False)
    '''
    def exact():
        if token.ent_type_ == 'GPE':  # TODO delete this double check?
            # Attempt to get db version of GPE
            found = Country.objects.get(name=token.text)
            if not found:
                found = State.objects.get(name=token.text)
                if not found:
                    found = City.objects.get(name=token.text)
            if found:
                return found
            else:
                # Couldn't find with exact search, try again with not exact.
                print(f"\nCOULD NOT FIND PLACE {token.text} WITH EXACT MATCH!")
                return False

    def loose():
        if token.pos_ == 'PROPN':
            possible_place = token.text

            # Smallest -> Largest DB
            country = Country.objects.filter(name__icontains=possible_place)
            state = State.objects.filter(name__icontains=possible_place)
            city = City.objects.filter(name__icontains=possible_place)

            parent = []

            [parent.append(model_to_dict(p)) for p in country]
            [parent.append(model_to_dict(p)) for p in state]
            [parent.append(model_to_dict(p)) for p in city]

            scored_objs = [compare_strings(p['name'], possible_place) for p in parent]

            best_match = sorted(scored_objs, key=lambda o: o['score'], reverse=True)[0]

            new_parent = [el for el in parent if el['name'] == best_match['string1']][0]

            if new_parent:
                if "state" in new_parent.keys() and "country" in new_parent.keys():  # is City
                    found = City.objects.get(id=new_parent['id'])
                elif "country" in new_parent.keys():  # is State
                    found = State.objects.get(id=new_parent['id'])
                else:  # is Country
                    found = Country.objects.get(id=new_parent['id'])
                return found

                return found
            return False
        else:
            return False

    if is_GPE:
        # Almost certainly a place! Attempt exact match
        exact_attempt = exact()
        if exact_attempt:
            return exact_attempt
    else:
        return loose()


def compare_strings(string1, string2):
    s1 = [x for x in string1.replace(' ', '')]
    s2 = [x for x in string2.replace(' ', '')]

    # set base to longer string
    if len(s1) > len(s2):
        base = s1
        shrt = s2
    else:
        base = s2
        shrt = s1

    score = 0

    # Add to score for matching letters in place
    for i, l in enumerate(base):
        if i < len(shrt) and l == shrt[i]:
            score += 1

    # Subtract score for overflow letters
    for i in base[len(shrt)-1:]:
        score -= 1

    # print(score)
    return {"score": score, "string1": string1, "string2": string2}


# ############################# From `~/spt.py` #############################
def has_direct_obj(token: spacy.tokens.token.Token):
    dobj = [w for w in token.rights if w.dep_ == 'dobj']
    if dobj:
        return dobj
    return False


def has_preposition(token: spacy.tokens.token.Token):
    prep = [w for w in token.rights if w.dep_ in ['prep']]
    if prep:
        pobj = [[w2 for w2 in w.subtree if w2.dep_ in ['pobj']] for w in prep]

        if pobj and pobj[-1]:
            print("POBJ\t", pobj, '\nPREP:', prep)
            pobj = pobj[-1]
            print("POBJ\t", pobj, '\nPREP:', prep, '\n')

            return [prep[0], pobj[0]]

    return False


def matches_subjVerbDobj(token: spacy.tokens.token.Token):
    """ Attempts to extract a phrase from branching from `token` 
        by checking if that token has a `left [child]` with a 
        dependency of `subj`. 
        If that is found, attempts to get the `token`s `aux` 
        dependency if present, 
        checks for direct objects `(dobj)` dependencies, 
        then for sub-prepositions.
    """
    # Get subject of sentence, relative to Token
    subj = [word for word in token.lefts if word.dep_ in ['nsubj', 'aux']]  # Token RIGHT of subj.

    if subj:
        # If there are more than 1 token in `subj`, it's likely an `aux` - use lemma & combine
        if len(subj) == 1:
            matched = {"subj": subj[0].text, "token": token.text}
        else:
            matched = {"subj": subj[0].text, "aux?": subj[1].lemma_, "token": token.text}
        # TODO: Change to string! - remove string concats in parent method

        dobj = has_direct_obj(token)
        if dobj:
            matched["dobj"] = dobj[0].text

            # check if dobj has preposition context
            pobj = has_preposition(dobj[0])
            if pobj:
                matched['pobj'] = ' '.join(i.text for i in pobj)

        # If Token has a subject, check for prepositions relative to Token
        # ie: "person did thing IN ATLANTA"
        preps = has_preposition(token)
        if preps:
            matched['subpreps'] = ' '.join(i.text for i in preps)

        return matched
    return False
