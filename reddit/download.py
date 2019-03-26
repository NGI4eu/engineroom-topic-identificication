import requests
import requests.auth
import pandas as pd
import itertools
import praw

r = praw.Reddit(client_id='',
                 client_secret='',
                 user_agent='',
                 username='',
                 password='')

terms = [
    'gender discrimination',
    'gdpr',
]

dir_name = './res_reddit/'

all_posts = {}
for term in terms:
    print('---\nTERM: ' + term + '\n---')
    new_posts = r.subreddit('all').search(term, limit=500, sort='new')
    top_posts = r.subreddit('all').search(term, limit=500, sort='top')
    search_posts = itertools.chain(new_posts, top_posts)
    all_posts[term] = []
    for i, c in enumerate(search_posts):
        if i % 100 == 0:
            print(i, r.auth.limits)
        post_dict = vars(c)
        post_comments = []
        c.comments.replace_more(limit=0)
        comment_queue = c.comments[:]  # Seed with top-level
        comment_counter = 0
        while comment_queue:
            comment = comment_queue.pop(0)
            post_comments.append(comment.body)
            comment_counter += 1
            # include lower-level posts
            comment_queue.extend(comment.replies)
        post_dict['comments_body'] = str(post_comments)
        all_posts[term].append(post_dict)
    pd.DataFrame(all_posts[term]).drop_duplicates(subset=['url']).to_csv(
    	dir_name + 'n500_t500_child_' + term.replace(' ', '_') + '.csv')