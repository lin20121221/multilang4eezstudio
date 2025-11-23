import shlex
import re
import sys

def unicode_to_utf8(match):
    r"""将\uXXXX格式的UNICODE字符转换为UTF-8字节序列"""
    unicode_str = match.group(0)  # 获取完整的\uXXXX
    code_point = int(match.group(1), 16)  # 提取XXXX并转换为整数
    
    # 转换为UTF-8编码
    if code_point <= 0x7F:
        # 单字节: 0xxxxxxx
        return f'\\{code_point:03o}'
    elif code_point <= 0x7FF:
        # 双字节: 110xxxxx 10xxxxxx
        byte1 = 0xC0 | (code_point >> 6)
        byte2 = 0x80 | (code_point & 0x3F)
        return f'\\{byte1:03o}\\{byte2:03o}'
    elif code_point <= 0xFFFF:
        # 三字节: 1110xxxx 10xxxxxx 10xxxxxx
        byte1 = 0xE0 | (code_point >> 12)
        byte2 = 0x80 | ((code_point >> 6) & 0x3F)
        byte3 = 0x80 | (code_point & 0x3F)
        return f'\\{byte1:03o}\\{byte2:03o}\\{byte3:03o}'
    else:
        # 四字节: 11110xxx 10xxxxxx 10xxxxxx 10xxxxxx
        byte1 = 0xF0 | (code_point >> 18)
        byte2 = 0x80 | ((code_point >> 12) & 0x3F)
        byte3 = 0x80 | ((code_point >> 6) & 0x3F)
        byte4 = 0x80 | (code_point & 0x3F)
        return f'\\{byte1:03o}\\{byte2:03o}\\{byte3:03o}\\{byte4:03o}'

def convert_unicode_to_utf8(text):
    r"""将文本中的\uXXXX格式的UNICODE字符转换为UTF-8编码"""
    # 匹配\uXXXX格式，其中XXXX是4位十六进制数
    unicode_pattern = r'\\u([0-9A-Fa-f]{4})'
    return re.sub(unicode_pattern, unicode_to_utf8, text)

def main(c_source_file):
    # Parse multi_lang.txt
    rows = []
    with open('multi_lang.txt', 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith(';'):
                continue
            try:
                parsed = shlex.split(line)
            except ValueError:
                continue
            row = [s for s in parsed if s]
            if len(row) >= 3:
                # 转换每个字符串中的UNICODE字符
                converted_row = [convert_unicode_to_utf8(s) for s in row]
                rows.append(converted_row)

    if not rows:
        print("No valid rows in multi_lang.txt")
        return

    num_langs = len(rows[0]) - 1
    TOTAL_LANG = num_langs

    # Dictionaries for matching
    str_to_langstrings = {}
    str_to_arrayname = {}
    for row in rows:
        array_name = row[-1]
        langstrings = row[:-1]
        for s in langstrings:
            if s in str_to_langstrings:
                print(f"Warning: Duplicate string '{s}'")
            str_to_langstrings[s] = langstrings
            str_to_arrayname[s] = array_name

    # Generate strings.h
    with open('strings.h', 'w', encoding='utf-8') as h:
        h.write('#ifndef STRINGS_H\n#define STRINGS_H\n\n')
        h.write(f'#define TOTAL_LANG {TOTAL_LANG}\n\n')
        h.write('extern unsigned char lang_index;\n\n')
        for row in rows:
            array_name = row[-1]
            h.write(f'extern const char * {array_name}[TOTAL_LANG];\n')
        h.write('\n#endif\n')

    # Generate strings.c
    with open('strings.c', 'w', encoding='utf-8') as c:
        c.write('#include "strings.h"\n\n')
        for row in rows:
            array_name = row[-1]
            langs = row[:-1]
            c.write(f'const char * {array_name}[TOTAL_LANG] = {{\n')
            for s in langs:
                c.write(f'    "{s}",\n')
            c.write('};\n\n')
        c.write('unsigned char lang_index = 0;\n')

    # Process C source file
    with open(c_source_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # 首先转换C源码中的UNICODE字符
    content = convert_unicode_to_utf8(content)
    
    modified = False

    # Part a: Process map arrays
    map_pattern = r'static\s+const\s+char\s*\*\s*map\[(\d+)\]\s*=\s*\{(.*?)\};'
    matches = list(re.finditer(map_pattern, content, re.DOTALL | re.MULTILINE))

    new_content = ''
    prev_end = 0
    for match in matches:
        new_content += content[prev_end:match.start()]
        size = match.group(1)
        init = match.group(2)
        items = [i.strip() for i in init.split(',') if i.strip()]
        has_match = False
        lang_items = [[] for _ in range(num_langs)]
        for item in items:
            if item == 'NULL':
                for li in lang_items:
                    li.append('NULL')
                continue
            if not (item.startswith('"') and item.endswith('"')):
                for li in lang_items:
                    li.append(item)
                continue
            content_str = item[1:-1]
            if content_str in str_to_langstrings:
                has_match = True
                lang_strs = str_to_langstrings[content_str]
                for i in range(num_langs):
                    lang_items[i].append(f'"{lang_strs[i]}"')
            else:
                for li in lang_items:
                    li.append(item)
        if has_match:
            modified = True
            new_init = '{\n'
            for li in lang_items:
                new_init += '    {' + ', '.join(li) + '},\n'
            new_init += '}'
            new_def = f'static const char *map[TOTAL_LANG][{size}] = {new_init};'
            new_content += new_def
            # Find and modify the next lv_btnmatrix_set_map
            rest = content[match.end():]
            set_pattern = r'lv_btnmatrix_set_map\s*\(\s*obj\s*,\s*map\s*\)\s*;'
            set_match = re.search(set_pattern, rest)
            if set_match:
                new_set = 'lv_btnmatrix_set_map(obj, map[lang_index]);'
                new_content += rest[:set_match.start()] + new_set
                prev_end = match.end() + set_match.end()
            else:
                prev_end = match.end()
        else:
            new_content += match.group(0)
            prev_end = match.end()
    new_content += content[prev_end:]
    content = new_content

    # Find map init regions to exclude in part b
    map_init_pattern = r'static\s+const\s+char\s*\*\s*map\[(?:TOTAL_LANG|\d+)\](?:\[\d+\])?\s*=\s*\{(.*?)\};'
    init_matches = list(re.finditer(map_init_pattern, content, re.DOTALL | re.MULTILINE))
    map_init_regions = [(m.start(1), m.end(1)) for m in init_matches]

    # Part b: Replace other strings
    str_pattern = r'"[^"\\]*(?:\\.[^"\\]*)*"'
    str_matches = list(re.finditer(str_pattern, content))
    new_content = ''
    prev_end = 0
    for sm in str_matches:
        new_content += content[prev_end:sm.start()]
        literal = sm.group(0)
        str_content = literal[1:-1]
        is_in_map = any(r[0] <= sm.start() < r[1] for r in map_init_regions)
        if not is_in_map and str_content in str_to_arrayname:
            array_name = str_to_arrayname[str_content]
            new_repl = f'{array_name}[lang_index]'
            new_content += new_repl
            modified = True
        else:
            new_content += literal
        prev_end = sm.end()
    new_content += content[prev_end:]
    content = new_content

    # Add #include if modified
    if modified:
        if not content.startswith('#include "strings.h"'):
            content = '#include "strings.h"\n' + content

    # Write back to C file
    with open(c_source_file, 'w', encoding='utf-8') as f:
        f.write(content)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python multilang.py <c_source_file>")
        sys.exit(1)
    main(sys.argv[1])