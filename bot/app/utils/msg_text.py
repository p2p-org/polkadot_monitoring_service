
def text2dict(text: str):
    if '---\n' in text:
        text = text[text.index('---\n') + 4:]
    d = dict()
    key = ""
    for l in text.strip('\n').splitlines():
        if l == '':
            continue
        if l.endswith(":"):
            key = l[:-1]
            d[key] = []
        else:
            d[key].append(l)
    return d

def dict2text(d: dict):
    t = '---'
    for k in d.keys():
        t = "{}\n{}:\n{}".format(t,k,'\n'.join(d[k]))
    return t