# Every [Obsolete] member of Unity's C# reference source (github.com/Unity-Technologies/UnityCsReference, a branch per
# Unity version) as (Type, Member, error?, message), tracking the enclosing type by brace depth; then the project's uses
# (from apiscan) of one. ERROR lines stop the editor from compiling; warn lines are warnings. Matches are by type and member
# name, not overload: check an ERROR line's signature against the obsolete overload before acting on it.
#   python3 obsolete_check.py <reference source dir> <uses.txt>
import re, os, sys, collections
SRC, USES = sys.argv[1], sys.argv[2]
attr_re = re.compile(r'\[\s*(?:System\.)?Obsolete(?:Attribute)?\s*(\((?:[^()]|\([^()]*\))*\))?')
type_re = re.compile(r'\b(class|struct|interface|enum)\s+([A-Za-z_]\w*)')
mem_re = re.compile(r'([A-Za-z_]\w*)\s*(?:<[^<>]*(?:<[^<>]*>[^<>]*)*>)?\s*(\(|\{|=>|=|;|$)')
KW = {'get', 'set', 'add', 'remove', 'if', 'return', 'new', 'public', 'static', 'override', 'virtual', 'extern', 'internal', 'protected',
      'private', 'unsafe', 'readonly', 'sealed', 'abstract', 'partial', 'const', 'event', 'operator', 'implicit', 'explicit', 'where', 'this'}
pairs = {}
arities = collections.defaultdict(set)
def params_of(text, name):
    """The number of parameters of `name`'s declaration on this line, or None (not a method, or not on one line)."""
    i = text.find(name + '(') if name + '(' in text else text.find(name + ' (')
    if i < 0: return None
    j = text.index('(', i); depth = 0; count = 0; seen = False
    for ch in text[j:]:
        if ch in '(<[': depth += 1
        elif ch in ')>]':
            depth -= 1
            if depth == 0: return count + 1 if seen else 0
        elif ch == ',' and depth == 1: count += 1
        elif not ch.isspace() and depth >= 1: seen = True
    return None
def strip(l):
    l = re.sub(r'"(?:\\.|[^"\\])*"', '""', l); l = re.sub(r"'(?:\\.|[^'\\])'", "''", l)
    return l.split('//')[0]
for root, _, files in os.walk(SRC):
    for f in files:
        if not f.endswith('.cs'): continue
        p = os.path.join(root, f)
        try: raw = open(p, encoding='utf-8', errors='ignore').read().split('\n')
        except Exception: continue
        stack = []; depth = 0; pending_type = None; pending_attr = None; in_comment = False
        for i, line in enumerate(raw):
            l = line
            if in_comment:
                if '*/' in l: l = l.split('*/', 1)[1]; in_comment = False
                else: continue
            if '/*' in l and '*/' not in l.split('/*', 1)[1]: l = l.split('/*', 1)[0]; in_comment = True
            m = attr_re.search(l)
            if m:
                args = m.group(1) or ''
                err = bool(re.search(r',\s*true\s*\)\s*$', args)) or 'error: true' in args or 'error:true' in args
                msg = re.findall(r'"((?:\\.|[^"\\])*)"', args)
                pending_attr = (err, msg[0] if msg else '', i)
                l = l[:m.start()] + l[m.end():]
                l = re.sub(r'^\s*[\],]*\s*', '', l)
            s = strip(l)
            t = type_re.search(s)
            decl_name = None
            if t and not re.search(r'\bnew\s+' , s[:t.start()]) and 'typeof' not in s:
                pending_type = t.group(2); decl_name = ('type', t.group(2))
            elif pending_attr and s.strip() and not s.strip().startswith('['):
                # the member declared on this line: the identifier before '(' '{' '=>' '=' ';'
                cands = [x for x in mem_re.findall(s) if x[0] not in KW]
                if cands: decl_name = ('member', cands[0][0])
                arity = params_of(' '.join(strip(x) for x in [s] + raw[i + 1:i + 5]), cands[0][0]) if cands else None
            if pending_attr and decl_name:
                err, msg, ai = pending_attr
                owner = stack[-1][0] if stack else '?'
                if decl_name[0] == 'type': pairs[(decl_name[1], decl_name[1])] = (err, msg, os.path.relpath(p, SRC))
                else:
                    pairs[(owner, decl_name[1])] = (err, msg, os.path.relpath(p, SRC))
                    arities[(owner, decl_name[1])].add(arity)
                pending_attr = None
            elif pending_attr and i - pending_attr[2] > 6: pending_attr = None
            for ch in s:
                if ch == '{':
                    depth += 1
                    if pending_type: stack.append((pending_type, depth)); pending_type = None
                elif ch == '}':
                    if stack and stack[-1][1] == depth: stack.pop()
                    depth -= 1
            if pending_type and ';' in s and '{' not in s: pending_type = None
print('obsolete members:', len(pairs), 'of which errors:', sum(1 for v in pairs.values() if v[0]))
uses = collections.defaultdict(list)
for line in open(USES):
    parts = line.rstrip('\n').split('\t')
    if len(parts) >= 2: uses[parts[0]].append(parts[1] + ('  ' + parts[2] if len(parts) > 2 else ''))
for (t, mname), (err, msg, f) in sorted(pairs.items()):
    key = t + '.' + mname
    if key in uses and (err or '--all' in sys.argv) and t != mname:
        # (only the uses of an obsolete overload: same number of parameters, when both are known)
        known = arities[(t, mname)]
        def used_arity(loc):
            sig = loc.split('  ', 1)[1] if '  ' in loc else ''
            if '(' not in sig: return None
            inner = sig[sig.index('(') + 1:sig.rindex(')')]
            return 0 if not inner.strip() else inner.count(',') + 1 - inner.count('<') * 0
        locs = sorted(set(l for l in uses[key] if None in known or used_arity(l) is None or used_arity(l) in known))
        if not locs: continue
        print(('ERROR  ' if err else 'warn   ') + key + '  -- ' + msg[:90] + '  [' + f + ']')
        for l in locs[:6]: print('         ' + l)
        if len(locs) > 6: print('         ... %d more' % (len(locs) - 6))
