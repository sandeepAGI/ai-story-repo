#!/usr/bin/env python3
"""
Check language distribution in Microsoft customer stories
"""

import psycopg2
import os
from urllib.parse import urlparse

# Get database connection
database_url = os.getenv('DATABASE_URL', 'postgresql://localhost/ai_stories')
parsed = urlparse(database_url)

conn = psycopg2.connect(
    host=parsed.hostname or 'localhost',
    database=parsed.path.lstrip('/') or 'ai_stories',
    user=parsed.username,
    password=parsed.password,
    port=parsed.port or 5432
)

cur = conn.cursor()

# Get ALL Microsoft stories and check URLs for language codes
cur.execute('''
    SELECT customer_name, title, url
    FROM customer_stories cs
    JOIN sources s ON cs.source_id = s.id
    WHERE s.name = 'Microsoft'
''')

all_stories = cur.fetchall()

# Language patterns in URLs
language_patterns = {
    'Chinese': ['/zh-cn/', '/zh-tw/'],
    'Korean': ['/ko-kr/'],
    'Japanese': ['/ja-jp/'],
    'German': ['/de-de/'],
    'French': ['/fr-fr/'],
    'Spanish': ['/es-es/'],
    'Portuguese': ['/pt-br/'],
    'Italian': ['/it-it/'],
    'Dutch': ['/nl-nl/']
}

language_counts = {}
non_english_stories = []

for customer_name, title, url in all_stories:
    url_lower = url.lower()
    
    # Check if URL contains language code
    story_language = 'English'  # default
    for lang, patterns in language_patterns.items():
        if any(pattern in url_lower for pattern in patterns):
            story_language = lang
            break
    
    if story_language != 'English':
        non_english_stories.append((customer_name, title, url, story_language))
        language_counts[story_language] = language_counts.get(story_language, 0) + 1

print('LANGUAGE DISTRIBUTION in {} Microsoft stories:'.format(len(all_stories)))
print('=' * 60)
print('English stories: {}'.format(len(all_stories) - len(non_english_stories)))

for lang, count in sorted(language_counts.items()):
    print('{} stories: {}'.format(lang, count))

print()
print('Total non-English stories: {}'.format(len(non_english_stories)))
print('Percentage non-English: {:.1f}%'.format(len(non_english_stories)/len(all_stories)*100))

if non_english_stories:
    print()
    print('SAMPLE NON-ENGLISH STORIES:')
    print('=' * 60)
    for i, (customer, title, url, lang) in enumerate(non_english_stories[:15], 1):
        print('{}. [{}] {}'.format(i, lang, customer))
        title_display = title[:80] + '...' if len(title) > 80 else title
        print('   Title: {}'.format(title_display))
        print('   URL: {}'.format(url))
        print()

conn.close()