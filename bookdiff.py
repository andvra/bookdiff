import requests
import urllib.request
import time
from bs4 import BeautifulSoup
import string
import json
import os
import numpy as np 
from paramiko import SSHClient, AutoAddPolicy
from scp import SCPClient, SCPException
import matplotlib.pyplot as plt
import zipfile
import nltk
import sys
import shutil

def get_author_from_h2(h2):
    a = h2.find_all('a')
    if len(a)==0:
        return h2.get_text()
    else:
        return a[0].get_text()

def get_books_from_ul(ul):
    books = []
    lis = ul.find_all("li",{"class":"pgdbetext"})
    for li in lis:
        a = li.find("a")
        if len(li.text)>len(a.text):
            rest = li.text[len(a.text):]
            start = rest.find("(")
            end = rest.find(")")
            lang = rest[start+1:end]
        else:
            lang = UNKNOWN
        book = {'name':a.text,'url':a.get('href'),'lang':lang}
        books.append(book)
    
    return books

def parse_authors():
    urls = ['https://www.gutenberg.org/browse/authors/'+x for x in list(string.ascii_lowercase)]
    authors = dict()
    for url in urls:
        letter = url[-1]
        response = requests.get(url)
        soup = BeautifulSoup(response.text,"html.parser")
        div = soup.find("div",{"class":"pgdbbyauthor"})
        records = div.findChildren(recursive=False)
        last_record=None
        authors_for_letter = []
        for record in records:
            # We filter out authors with no books listed.
            # This is done by checking if there is a list of books
            # in the UL preceeding the H2 element
            if record.name=='ul' and last_record != None and last_record.name=='h2':
                author_name = get_author_from_h2(last_record)
                books = get_books_from_ul(record)
                author = {'name':author_name, 'books':books,'no_books':len(books)}
                authors_for_letter.append(author)
            last_record = record
        print('There where {} authors starting with \'{}\''.format(len(authors_for_letter),letter))
        authors[letter] = authors_for_letter
        time.sleep(1)
    return authors

def filter_authors(authors, min_no_books=0, max_no_books=None, lang=None):
    ret = []
    unknown_author_names=['unknown','anonymous']
    for l in string.ascii_lowercase:
        if l in authors:
            for author in authors[l]:
                if author['name'].lower() not in unknown_author_names:
                    no_books_all_lang = author['no_books']
                    if no_books_all_lang>=min_no_books and no_books_all_lang<=max_no_books:
                        if lang!=None:
                            # If the total number of books is OK, make sure the
                            #   language of each book matches the preferred language
                            no_books = 0
                            lang = lang.lower()
                            for book in author['books']:
                                if book['lang'].lower()==lang:
                                    no_books += 1
                        else:
                            no_books = no_books_all_lang
                        if no_books>=min_no_books:
                            ret.append(author)
    return ret

def get_books_from_scp(filenames,source_path,dest_path,download_path,ip,port,username,password):
    archive_name = '_files_'+str(np.random.randint(1000000))+'_.zip'
    command = 'cd {} && zip ../{} {}'.format(source_path, archive_name, ' '.join(filenames))
    ssh = SSHClient()
    ssh.load_system_host_keys()
    ssh.set_missing_host_key_policy(AutoAddPolicy)
    ssh.connect(ip,port,username=username,password=password)
    stdin_, stdout_, stderr_ = ssh.exec_command(command)
    stdout_.channel.recv_exit_status()
    try:
        with SCPClient(ssh.get_transport()) as scp:
            scp.get('{}../{}'.format(source_path,archive_name),download_path)
            command='rm {}../{}'.format(source_path,archive_name)
            stdin_, stdout_, stderr_ = ssh.exec_command(command)
            stdout_.channel.recv_exit_status()
            zip_ref = zipfile.ZipFile('{}/{}'.format(download_path,archive_name), 'r')
            zip_ref.extractall(dest_path)
            zip_ref.close()
            return True
    except SCPException:
        print('SCPException. Transfer failed')
    except requests.Timeout as err:
        print("TODO: Handle this timeout error. {}".format(err.message))
    except requests.RequestException as err:
        print("TODO: Handle other request-related error. {}".format(err.message))
    except:
        print("There was another issue")
    return False

def get_books_from_local(filenames, source_path, dest_path):
    for f in filenames:
        src = os.path.join(source_path,f)
        if os.path.exists(src):
            shutil.copy(src,dest_path)

def clean_up_books(filenames,path_raw,path_clean):
    for filename in filenames:
        src = os.path.join(path_raw,filename)
        dst = os.path.join(path_clean,filename)
        if os.path.isfile(src):
            with open(src,'r') as f:
                all_txt = f.read()
            with open(dst,'w') as f:
                start  = all_txt.find("*** START OF THIS PROJECT GUTENBERG EBOOK")
                if start==-1:
                    start = all_txt.find("*** START OF THE PROJECT GUTENBERG")
                if start==-1:
                    start = all_txt.find("***START OF THE PROJECT GUTENBERG")
                start = start + all_txt[start+3:].find("***")+6
                end = all_txt.find("End of the Project Gutenberg")
                if end == -1:
                    end = all_txt.find('End of Project Gutenberg')
                if end==-1:
                    end = all_txt.find("***END OF THE PROJECT GUTENBERG")
                f.write(all_txt[start:end].strip())

def get_books(books,config,use_scp=False):
    filenames_to_fetch = []
    for book in books:
        filename = book['url'][book['url'].rindex('/')+1:] + '.txt'
        if not os.path.isfile(get_cache_path('books/'+filename)):
            filenames_to_fetch.append(filename)
    if len(filenames_to_fetch)>0:
        success = True
        dest_path = get_cache_path('books_raw')
        if use_scp:
            download_path = get_cache_path('downloads')
            scp_conf = config['scp']
            ip = scp_conf['ip']
            port = scp_conf['port']
            username = scp_conf['username']
            password = scp_conf['password']
            source_path = scp_conf['path']
            success = get_books_from_scp(filenames_to_fetch,source_path,dest_path,download_path,ip,port,username,password)
        else:
            source_path = config['local_book_lib']
            success = get_books_from_local(filenames_to_fetch,source_path,dest_path)
        clean_up_books(filenames_to_fetch,get_cache_path('books_raw'),get_cache_path('books'))

def prepare_folders():
    folders = [get_cache_path(), get_cache_path('books'), get_cache_path('books_raw'), get_cache_path('downloads')]
    for folder in folders:
        if not os.path.exists(folder):
            os.makedirs(folder)

def get_cache_path(f=''):
    return 'cache/'+f

def get_corpus(author):
    books = []
    for book in author['books']:
        bookname = book['name']
        filename = book['url'][book['url'].rindex('/')+1:] + '.txt'
        path = get_cache_path('books/'+filename)
        # Some books might not have been successfully downloaded, so check that file exist before reading it
        if os.path.isfile(path):
            with open(path,'r') as f:
                books.append((bookname,f.read()))
    return books


def compare_authors(authors,no_compare_tokens=1000):
    corpus = {}
    corpus_test = []
    no_test = 5
    for author in authors:
        author_name = author['name']
        corpus_current = get_corpus(author)
        np.random.shuffle(corpus_current)
        corpus_calc, corpus_validate = corpus_current[:-no_test], corpus_current[-no_test:]
        for bookname,text in corpus_validate:
            raw_tokens = nltk.word_tokenize(text)
            tokens = [token.lower() for token in raw_tokens if any(c.isalpha() for c in token)]
            freq = nltk.FreqDist(tokens)
            corpus_test.append({'name':author_name,'bookname':bookname,'tokens':tokens,'freq':freq})
        merged_corpus =  '\r\n'.join([x[1] for x in corpus_calc])
        raw_tokens = nltk.word_tokenize(merged_corpus)
        tokens = [token.lower() for token in raw_tokens if any(c.isalpha() for c in token)]
        freq = nltk.FreqDist(tokens)
        corpus[author_name] = {}
        corpus[author_name]['tokens'] = tokens
        corpus[author_name]['freq'] = freq
        print("Done tokenizing for author {}".format(author_name))
    merged_tokens = [token for d in corpus.values() for token in d['tokens']]
    print("Done merging")
    merged_freq = nltk.FreqDist(merged_tokens)
    most_common_tokens = list(merged_freq.most_common(no_compare_tokens))
    tokens = {}
    no_authors = len(authors)
    for token, _ in most_common_tokens:
        acc_var = 0
        acc_sum = 0
        for author in authors:
            author_name = author['name']
            freq = corpus[author_name]['freq']
            acc_var += (freq.freq(token)-merged_freq.freq(token))**2
            acc_sum += freq.freq(token)
        tokens[token] = {}
        tokens[token]['stdev'] = np.sqrt(acc_var)/no_authors
        tokens[token]['avg'] = acc_sum/no_authors
    Z = {}
    for k, v in tokens.items():
        for author in authors:
            author_name = author['name']
            freq = corpus[author_name]['freq']
            c = freq.freq(k)
            sigma = v['stdev']
            my = v['avg']
            z = (c-my)/sigma
            Z[(k,author_name)] = z
    no_correct = 0
    for cur_test in corpus_test:
        freq = cur_test['freq']
        name = cur_test['name']
        bookname = cur_test['bookname']
        min_delta = np.inf
        max_delta = -np.inf
        min_name=None
        for author in authors:
            author_name = author['name']
            delta = 0
            for k, v in tokens.items():
                c = freq.freq(k)
                sigma = v['stdev']
                my = v['avg']
                z = (c-my)/sigma
                delta += np.abs(z-Z[(k,author_name)])
            if delta<min_delta:
                min_delta = delta
                min_name = author_name
            if delta>max_delta:
                max_delta = delta
        if name==min_name:
            no_correct += 1
        else: 
            print('FAIL: {}: {}: {:.1f}: {:.1f}\r\n  {}'.format(name, min_name, min_delta, max_delta, bookname))
    print('{}/{} correctly classified'.format(no_correct,no_authors*no_test))

if __name__=="__main__":
    prepare_folders()
    with open('config.json','r') as f:
        config = json.load(f)
    fn = get_cache_path("authors.json")
    # Check if the authon JSON exists. Generating that file takes some time,
    #   and here we make sure it's only done once.
    if os.path.exists(fn):
        print("Read authors from file")
        with open(fn,'r') as f:
            authors = json.load(f)
    else:
        print("Parsing authors from web")
        authors = parse_authors()
        with open(get_cache_path('authors.json'),"w") as f:
            json.dump(authors,f,indent=4)
    print("Done reading authors")
    authors = filter_authors(authors,config['min_books'],config['max_books'],'english')
    selected_authors = np.random.choice(authors, config['number_of_authors'])
    no_books = sum([len(author['books']) for author in selected_authors])
    print('Using a total of {} books for input'.format(no_books))
    for author in selected_authors:
        get_books(author['books'],config,True)
    compare_authors(selected_authors)