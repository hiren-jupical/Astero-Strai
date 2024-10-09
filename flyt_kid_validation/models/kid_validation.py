#!/usr/bin/env python

# https://www.lefdal.cc/div/moduluskontroll.php
# https://no.wikipedia.org/wiki/MOD10


def kid_mod11_wiki(a):
    # https://no.wikipedia.org/wiki/MOD11
    revers = a[::-1]
    cross = sum([int(val) * [2,3,4,5,6,7][idx % 6] for idx,val in enumerate(revers)])    
    cs = 11-(cross % 11)
    
    css = {11 : '0', 10: '-'}
    return "%s%s" % (a, css.get(cs, cs))

def kid_mod10(a):
    return "%s%s" % (a, (10-(sum([int(n) for n in list("".join([str(int(val)*[2,1][idx%2]) for idx,val in enumerate(list(str(a))[::-1])]))])%10))%10)

def kid_valid(kid):    
    kid_without_control = kid[:-1]
    k1 = kid_mod10(kid_without_control)
    k2 = kid_mod11_wiki(kid_without_control)    

    if k1 == kid or k2 == kid:
        return True
    else:
        return False