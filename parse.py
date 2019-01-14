import re
from settings import *
from utils import *
import pandas as pd
from mysql import MYSQL
import multiprocessing

data = pd.read_csv('repo.csv', header=0)
repo_names = data[0:-1]['name']
repo_ids = data[0:-1]['id']
user_names = data[0:-1]['owner']
mysql = MYSQL()


# remove emoji
def filter_emoji(text):
    try:
        re_emoji = re.compile(u'['
                              u'\U0001F300-\U0001F64F'
                              u'\U0001F680-\U0001F6FF'
                              u'\u2600-\u2B55'
                              u'\u23cf'
                              u'\u23e9'
                              u'\u231a'
                              u'\u3030'
                              u'\ufe0f'
                              u"\U0001F600-\U0001F64F"  # emoticons
                              u"\U0001F300-\U0001F5FF"  # symbols & pictographs
                              u'\U00010000-\U0010ffff'
                              u'\U0001F1E0-\U0001F1FF'  # flags (iOS)
                              u'\U00002702-\U000027B0]+',
                              re.UNICODE)
    except re.error:
        re_emoji = re.compile(u'('
                              u'\ud83c[\udf00-\udfff]|'
                              u'\ud83d[\udc00-\ude4f]|'
                              u'\uD83D[\uDE80-\uDEFF]|'
                              u"(\ud83d[\ude00-\ude4f])|"  # emoticon
                              u'[\u2600-\u2B55]|'
                              u'[\u23cf]|'
                              u'[\u1f918]|'
                              u'[\u23e9]|'
                              u'[\u231a]|'
                              u'[\u3030]|'
                              u'[\ufe0f]|'
                              u'\uD83D[\uDE00-\uDE4F]|'
                              u'\uD83C[\uDDE0-\uDDFF]|'
                              u'[\u2702-\u27B0]|'
                              u'\uD83D[\uDC00-\uDDFF])+',
                              re.UNICODE)
    return re_emoji.sub(r'', text)


def parse_comment(soup, repo_id, issue_num):
    comment_lists = soup.find_all(name='div', id=re.compile(r'^issuecomment-[0-9]+$'))
    if comment_lists:
        for comment in comment_lists:
            body = parse_body(comment)
            body = body.replace(',', '.')
            body = filter_emoji(body)
            user_id = comment.find(name='a', class_='author').get('data-hovercard-url')
            user_id = user_id.split('=')[-1] if user_id else 0
            created_at = comment.select('relative-time')[0].get('datetime')
            role = ''
            role_temp = soup.find(name='span', class_='timeline-comment-label')
            if role_temp:
                role = role_temp.get_text().replace('\n', '').strip()
            insert_data = {
                'repo_id': repo_id,
                'issue_num': issue_num,
                'user_id': user_id,
                'body': body,
                'created_at': created_at,
                'db_role': role
            }
            mysql.insert('comments', insert_data)


def parse_body(soup):
    body_reg = re.compile("<[^>]*>")
    edit_content = soup.find(name='div', class_='edit-comment-hide')
    temp = edit_content.select('table>tbody>tr>td')[0]
    content = ' '.join(body_reg.sub('', temp.prettify()).replace('\n', '').split())
    return content


def get_detailed(url, far_repo_id):
    soup = get_soup(url)
    if soup:
        print('URL:' + url)
        repo_id = far_repo_id
        tag = url.split('/')[-2]
        issue_num = url.split('/')[-1]
        parse_comment(soup, repo_id, issue_num)
        reporter_id = soup.find(name='a', class_='author').get('data-hovercard-url')
        reporter_id = reporter_id.split('=')[-1] if reporter_id else 0
        reviewers_id = []
        assignees_id = []
        assignees = soup.find_all(name='div', class_='sidebar-assignee')
        if assignees:
            for assignee in assignees:
                assignee_name = assignee.find(name='div', class_='discussion-sidebar-heading').string.strip()
                if assignee_name == 'Assignees':
                    for index in assignee.find_all(name='span', class_='js-hovercard-left'):
                        assignees_id.append(index.get('data-hovercard-url').split('=')[-1])
                elif assignee_name == 'Reviewers':
                    for index in assignee.find_all(name='span', class_='js-hovercard-left'):
                        reviewers_id.append(index.get('data-hovercard-url').split('=')[-1])
        title = soup.find(name='span', class_='js-issue-title').string.strip()
        title = title.replace(',', '.')
        title = filter_emoji(title)
        body = parse_body(soup.find(name='div', id=re.compile(r'^issue-[0-9]+$')))
        body = body.replace(',', '.')
        body = filter_emoji(body)
        created_at = soup.select('relative-time')[0].get('datetime')
        closed_at = ''
        merged_at = ''
        role = ''
        state = soup.find(name='div', class_='TableObject-item').find(class_='State').get_text().strip()
        if state == 'Closed':
            closed_at = soup.find(name='div', class_='discussion-item-closed').select('relative-time')[0].get(
                'datetime')
        if state == 'Merged':
            merged_at = soup.find(name='div', class_='discussion-item-merged').select('relative-time')[0].get(
                'datetime')
        role_temp = soup.find(name='div', id=re.compile(r'^issue-[0-9]+$')).find(name='span',
                                                                                 class_='timeline-comment-label')
        if role_temp:
            role = role_temp.get_text().replace('\n', '').strip()
        insert_data = {
            'repo_id': repo_id,
            'tag': tag,
            'issue_num': int(issue_num),
            'reporter_id': reporter_id,
            'assignees_id': ';'.join(assignees_id),
            'reviewers_id': ';'.join(reviewers_id),
            'title': title,
            'body': body,
            'state': STATE_LIST.index(state) + 1,
            'created_at': created_at,
            'closed_at': closed_at,
            'merged_at': merged_at,
            'db_role': role
        }
        mysql.insert('issues', insert_data)


def get_single(repo_url, repo_id):
    soup = get_soup(repo_url)
    if soup:
        next_page = soup.find(name='a', class_='next_page')
        repo_lists = soup.find_all(name='div', id=re.compile(r'^issue_[0-9]+$'))
        for repo in repo_lists:
            detailed_url = BASE_URL + repo.find(name='a', id=re.compile(r'^issue-id-[0-9]+$')).get('href')
            get_detailed(detailed_url, repo_id)
        if next_page:
            next_page_url = BASE_URL + next_page.get('href')
            print(next_page_url)
            get_single(next_page_url, repo_id)
        else:
            print('last page')


if __name__ == '__main__':
    '''
    print('Testing')
    get_single(BASE_URL + '/freeCodeCamp/freeCodeCamp/issues' + '?q=' + ISSUE, 28457823)
    '''
    print('Running')
    pool = multiprocessing.Pool(multiprocessing.cpu_count() + 4)
    for i in range(0, len(repo_names)):
        pool.apply_async(get_single, (
            BASE_URL + '/' + user_names[i] + '/' + repo_names[i] + '/issues' + '?q=' + ISSUE, int(repo_ids[i]),))
        pool.apply_async(get_single, (
            BASE_URL + '/' + user_names[i] + '/' + repo_names[i] + '/pulls' + '?q=' + PULL, int(repo_ids[i]),))
    pool.close()
    pool.join()
    print('Ending')
