#!/usr/bin/env python3
"""
Extract 5-letter words from Collins Scrabble Words for Wordle game
"""

def extract_collins_words():
    words = []
    with open(r'c:\Users\omzdes\Downloads\Collins Scrabble Words (2019).txt', 'r', encoding='utf-8') as f:
        for line in f:
            word = line.strip()
            if len(word) == 5 and word.isalpha() and word.isupper():
                words.append(word)
    
    print(f'Total 5-letter words found: {len(words)}')
    
    # Use first 3000 words for good variety but manageable size
    subset = words[:3000]
    print(f'Using subset of {len(subset)} words')
    
    # Create Python list format
    python_list = '    WORD_LIST = [\n'
    for i in range(0, len(subset), 8):  # 8 words per line for readability
        row = subset[i:i+8]
        python_list += '        ' + ', '.join([f"'{w}'" for w in row]) + ',\n'
    python_list += '    ]'
    
    return python_list

if __name__ == '__main__':
    word_list = extract_collins_words()
    print("\nGenerated word list (first 100 chars):")
    print(word_list[:100] + "...")
    
    # Save to file
    with open('collins_word_list.txt', 'w') as f:
        f.write(word_list)
    print("\nSaved to collins_word_list.txt")