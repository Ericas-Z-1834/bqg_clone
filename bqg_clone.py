"""bqg_clone by Ericas Z.
Changelog:
[版本 1.1] Prints additional content checksum to output file.
[版本 1.0] Initial version."""
__version__ = '1.1'
from argparse import ArgumentParser
from requests import get
from bs4 import BeautifulSoup as B
from bs4 import element
from threading import Thread
from time import localtime, strftime, sleep
from tqdm import tqdm
from re import sub
from json import dumps
from hashlib import sha256
desc = "笔趣阁小说下载 CLI by Ericas Z. 使用 Python 3.12.3 基于 Requests 和 BeautifulSoup 编写，基于 Threading 多线程运行。输入小说地址，即可将小说内容下载为带有书籍信息和章节标注的文本文件，以便离线阅读。由于本程序使用多线程运行，在良好的网络连接（百兆级网速）下，下载 100 章以内的短篇小说大约耗时 20 秒，下载长篇小说耗时不超过 1 分钟，十分高效。欲下载小说，请进入 https://m.bls89a.cfd （网址可能发生变动，进入后应会重定向到最新可用网址），在搜索框搜索小说，并将小说地址作为参数运行此程序。地址应该形如 https://[主域名]/books/[若干位数字]/ ，由于笔趣阁不同站点的框架结构有所不同，故如输入其它主域名的站点，可能无法正确解析。由于网站本身原因，解析所得文本可能存在重复、错误排版等问题，一般不影响阅读。"
t = lambda: strftime('%Y-%m-%d_%H-%M-%S', localtime())
c = lambda s: f"\033[1;32;49m{s}\033[0m"
headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.142 Safari/537.36'}
data = []  # [[chap_index, chap_name, [[p1t1, p1t2, ...], [p2t1, p2t2, ...], ...]], ...]
prog = 0
tot = 0
h = 'html.parser'
l = '-' * 10
ok = False
tq = None
def parse_chap(chap_name, href):
    global data, headers, prog, tot, ok, tq
    chap_index = href.split('/')[-1][:-5]
    chap_data = []
    for pagenum in range(1, 1000):
        try: page = B(get(href.replace('.html', f'_{pagenum}.html'), headers=headers).content, h)
        except: raise RuntimeError(f"线程/章节 {chap_index} 请求失败。")
        blocks = [i.text.strip() for i in page.select('div#chaptercontent')[0].contents if type(i) is element.NavigableString and '请收藏：https://' not in i.text]
        if '' in blocks: blocks.remove('')
        chap_data.append(blocks)
        if '_' not in page.select('div.Readpage > a#pb_next.Readpage_down.js_page_down')[0]['href']: break
    data.append([int(chap_index), chap_name, chap_data])
    tq.update(1)
    prog += 1
    if prog == tot:
        del tq
        print(c(f"\n所有 {tot} 个章节全部解析完成。"))
        ok = True
parser = ArgumentParser(usage="bqg_clone input [-t txt_name]", description=desc)
parser.add_argument('input', type=str, help="小说地址 - 如遇解析失败，请运行 bqg_clone --help 以获取关于小说地址的详细信息。")
parser.add_argument('-t', type=str, help="要下载到文本文件的地址，包含文件名。如不提供，则以小说编号 + 创建时间，写至本程序同一文件夹下。")
args = parser.parse_args()
print(f"欢迎使用 bqg_clone [版本 {c(__version__)}] by Ericas Z.\n开始解析 ...")
try:
    b = B(get(args.input, headers=headers).content, h)
    misc = {'title': b.select('div.book_box > dl > dt.name')[0].text, 'author': b.select('div.book_box > dl > dd > span')[0].text[3:],
            'type': b.select('div.book_box > dl > dd > span')[1].text[3:], 'last_update': b.select('div.book_box > dl > dd > span')[4].text[3:].replace(' ', '_').replace(':', '-')}
    unfin = b.select('div.book_box > dl > dd > span')[2].text[3:] == '连载'
    chaps = B(get(args.input + 'list.html', headers=headers).content, h).select('dl > dd > a')[1:]
    tot = len(chaps)
    print(f"《{c(misc['title'])}》 || 作者：{c(misc['author'])} || 分类：{c(misc['type'])} || 更新：{c(misc['last_update'])}")
    if unfin: print(f"{c("注意：")}此书状态为 <{c("连载")}>，可能尚未完本。在输出的文本文件中将会标注此信息。")
    print(f"已检索到 {c(tot)} 个章节。")
    tq = tqdm(total=tot, desc="解析章节", unit="章")
    for chapter in chaps: Thread(target=parse_chap, args=(chapter.text, args.input + chapter['href'].split('/')[-1])).start()
    while not ok: sleep(1)
    data.sort(key=lambda i: i[0])
    txt_name = f'bqg_clone_{args.input.split('/')[-2]}_{sub(r'[\\/:*?"<>|]', '_', misc['title'])}_{t()}.txt'
    try:
        txt = open(args.t, 'r')
        txt.close()
    except FileNotFoundError: txt_name = args.t
    except Exception: pass
    if txt_name != args.t: print(f"{c("注意：")}所给定的输出文本文件已经存在，或为非法地址，或未提供地址。本程序将把小说文本写至本程序同一文件夹下的 {c(txt_name)} 。")
    with open(txt_name, 'w', encoding='utf-8') as txt:
        print(f"正在写入：{c("文件头")}")
        cksm = sha256(dumps(misc, sort_keys=False).encode('utf-8')).hexdigest()
        print(f"本次下载操作的校验码为：{c(cksm)} ，将写入文件头中的 “校验码 1” 部分。")
        print(f"{l}{l} 本文件由 bqg_clone [版本 {__version__}] by Ericas Z. 生成 {l}{l}\n《{misc['title']}》 || 作者：{misc['author']} || 分类：{misc['type']}"
              f"|| 更新：{misc['last_update']}\n创建时间：{t()} || 源网址：{args.input}\n{"注意：在本文件创建之时，网站标注此书状态为 <连载>，可能尚未完本。" if unfin else ''}\n\n"
              f"\n校验码 1：{cksm}"
              f"\n校验码 2：\n{'\n'.join([sha256(dumps(block, sort_keys=False).encode('utf-8')).hexdigest() for block in data])}"
              f"\n{l}{l} 目录 {l}{l}\n", file=txt)
        print(f"")
        print(f"正在写入：{c("目录")}")
        for i in data: print(f"{i[0]}. {i[1]}", file=txt)
        print(f"\n{l}{l} 正文开始 {l}{l}\n", file=txt)
        for i in tqdm(data, desc=f"写入{c("正文")}", unit="章"):
            print(f"\n\n\n{l} 第 {i[0]} 章：{i[1]} {l}\n\n\n", file=txt)
            print(*['\n\n'.join(j) for j in i[2]], sep='\n\n', file=txt)
    print(c("完成！"), "文件已保存在", c(txt_name), "\n本程序由 Ericas Z. 编写。欢迎下次使用。")
except Exception as e: print(e)
