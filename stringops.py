'''
Created on Jan 16, 2014

@author: nonlinear
'''
from __builtin__ import min

def long_substr(data):
    substr = ''
    if len(data) > 1 and len(data[0]) > 0:
        for i in range(len(data[0])):
            if i==0 or data[0][i]==' ':
                for j in range(len(data[0])-i+1):
                    if i+j==len(data[0]) or data[0][i+j-1]==' ':
                        if j > len(substr) and all(data[0][i:i+j].strip() in x for x in data):
                            substr = data[0][i:i+j]
    return substr


def find_common_patterns(s1, s2): # used recursively
    if s1 == '' or s2 == '':
        return [], []
    com = long_substr([s1,s2])
    if len(com) < 2:
        return ([(0, s1)], [(0, s2)])
    s1_bef, _, s1_aft = s1.partition(com)
    s2_bef, _, s2_aft = s2.partition(com)
    before = find_common_patterns(s1_bef, s2_bef)
    after = find_common_patterns(s1_aft, s2_aft)
    return (before[0] + [(1, com)] + after[0],
            before[1] + [(1, com)] + after[1])


def find_common_patterns_of_all(data):
    str1 = data[0]
    ret_val = []
    patterns = []
    print(str1)
    for j in range(1,len(data)):
        patterns = find_common_patterns(str1,data[j])
        str1 = ''.join(x[1] for x in patterns[0] if x[0]>0)
    else:
        ret_val.extend(x[1] for x in patterns[0] if x[0]>0)
    print(ret_val)
    return ret_val


####################################################################


def beginning_in_common(str0,str1):
    substr = ''
    len0 = len(str0)
    len1 = len(str1)
    if len0 > 0 and len1 > 0:
        i = 0
        for i in xrange(min(len0,len1)):
            if str0[i] != str1[i]:
                break
        substr = str0[:i]
    return substr


def ending_in_common(str0,str1):
    substr = ''
    len0 = len(str0)
    len1 = len(str1)
    if len0 > 0 and len1 > 0:
        i = 0
        for i in xrange(min(len0,len1)):
            if str0[len0-i-1] != str1[len1-i-1]:
                break
        substr = str0[len0-i:]
    return substr


def find_common_beginning(data):
    for i in range(len(data)):
        for j in range(len(data)):
            if i != j:
                substr = beginning_in_common([data[i],data[j]])


def find_difference_inside(strings):
    '''
    method that will return:
        - string number that is in a group of the most similar strings
        - substring that makes a difference
        - position of a substring in the string

    method finds common substrings at the beginning at the end
    returns values only if string of difference was found in the middle
    '''
    string_no = -1
    diff_substring = ""
    diff_substring_pos = -1

    max_len_in_common = 0
    same_pattern_strings = []
    common_beg = ''
    common_end = ''

    for i in range(len(strings)):
        if i not in same_pattern_strings: # why repeat yourself?
            for j in range(len(strings)):
                if i != j:
                    beg_substr = beginning_in_common(strings[i],strings[j])
                    end_substr = ending_in_common(strings[i],strings[j])

                    if len(end_substr)>0:
                        if len(beg_substr)+len(end_substr) > max_len_in_common:
                            print 'new max!:',i,'and',j,'have beginning "'+beg_substr+'" and ending "'+end_substr+"' in common."
                            max_len_in_common = len(beg_substr)+len(end_substr)
                            same_pattern_strings = [i,j]
                            common_beg = beg_substr
                            common_end = end_substr
                        elif len(beg_substr)+len(end_substr) == max_len_in_common:
                            if i == same_pattern_strings[0]:
                                print j,'joined the group!'
                                same_pattern_strings.append(j)


    if len(same_pattern_strings) > 0:
        string_no = same_pattern_strings[0]

        common_strings = []
        for strno in same_pattern_strings:
            common_strings.append(strings[strno])

        diff_substring_pos = len(common_beg)
        diff_substring_end = len(strings[string_no])-len(common_end)
        diff_middle = strings[string_no][diff_substring_pos:diff_substring_end]

        return common_strings, common_beg, diff_middle, common_end
    else:
        return [], '', '', ''