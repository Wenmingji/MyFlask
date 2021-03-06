# -*- coding:utf-8 -*-
from datetime import datetime

from app import app
from flask import render_template, request, redirect, url_for, session, render_template_string
from models import db_session, User, Article
from hashlib import md5
from markdown import markdown
from os import popen


@app.route('/')
def welcome():
    return render_template('welcome.html')


@app.route('/home/')
def hello_world():
    if 'username' in session.keys():
        # title = session['username']
        name = session.get('username')
    else:
        name = None
    return render_template('home.html', title=name)


@app.route('/login/', methods=['GET'])
def login_form():
    title = u'登录'
    return render_template('login.html', title=title)


@app.route('/login/', methods=['POST'])
def login():
    username = request.form['username']
    password = md5(request.form['password']).hexdigest()
    # db_session.execute("SELECT * FROM table_name WHERE column_name = %s", "column_value")
    sql = db_session.execute(
        "select username, password from user where username = '{}' and password = '{}'".format(username, password))
    data = sql.fetchone()
    # for i in data:
    # print i
    if data:
        # title = u'登录成功'
        # print data
        session['username'] = data[0]
        session.permanent = True
        db_session.close()
        return redirect(url_for('hello_world'))  # render_template('login.html', title=title)
    else:
        title = u'登录失败'
        fail = True
        db_session.close()
        return render_template('login.html', title=title, fail=fail)


@app.route('/register/', methods=['GET'])
def register_form():
    title = u'注册'
    return render_template('register.html', title=title)


@app.route('/register/', methods=['POST'])
def register():
    # username = request.form['username']
    # password = request.form['password']
    username = request.form.get('username')
    password = request.form.get('password')
    sql = "INSERT INTO `flask_db`.`user` (`id`, `username`, `password`) VALUES (NULL, '{}', '{}')".format(username,
                                                                                                          md5(
                                                                                                              password).hexdigest())
    try:
        # 执行sql语句
        db_session.execute(sql)
        # 提交到数据库执行
        db_session.commit()
    except LookupError:
        # 发生错误时回滚
        db_session.rollback()
    # data = sql.fetchone()
    # title = u'登录成功'
    db_session.commit()
    db_session.close()
    return redirect(url_for('hello_world'))  # render_template('login.html', title=title)


# except:
#     title = u'注册失败'
#     db_session.close()
#     return render_template('login.html', title=title)

@app.route('/logout/', methods=['GET', 'POST'])
def logout():
    session['username'] = False  # 变成false 就意味着需要重新登录了
    session.clear()
    return redirect(url_for('hello_world'))


@app.route('/post/')
def post():
    title = u'文章列表'
    posts = db_session.query(Article).order_by(Article.data_publish.desc()).all()
    authors = db_session.query(User.id, User.username).all()
    db_session.close()
    return render_template('articles.html', posts=posts, title=title, authors=authors)


@app.route('/profile/')
def profile():
    """
    mp: (mystery-person) a simple, cartoon-style silhouetted outline of a person (does not vary by email hash)
    identicon: a geometric pattern based on an email hash
    monsterid: a generated 'monster' with different colors, faces, etc
    wavatar: generated faces with differing features and backgrounds
    retro: awesome generated, 8-bit arcade-style pixelated faces
    robohash: a generated robot with different colors, faces, etc
    blank:a transparent PNG image (border added to HTML below for demonstration purposes)
    """
    if 'username' in session.keys():
        # title = session['username']
        title = u'用户资料'
        name = session.get('username')
        avatar_hash = md5(name).hexdigest()
    else:
        title = None
        name = None
    return render_template('profile.html', title=title, name=name, avatar=avatar_hash)


# cursor.execute("insert into user(id,age,name,create_time,update_time) \
# values('%d', '%d', '%s', '%s', '%s')
# " % \
# (user.getId(), user.getAge(), user.getName(), dt, dt))
@app.template_filter('md')
def markdown_to_html(txt):
    # md过滤器
    return markdown(txt)


@app.route('/write/', methods=['GET'])
def write_article_form():
    title = u'撰写博文'
    return render_template('write.html', title=title)


@app.route('/write/', methods=['POST'])
def write_article():
    title = u'发布成功'
    post_title = request.form.get('title')
    post_content = request.form.get('content')
    post_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    post_uid = db_session.query(User.id).filter(User.username == session.get('username')).first()[0]
    tmp = Article(title=post_title, content=post_content, data_publish=post_datetime, user_id=post_uid)
    db_session.add(tmp)
    db_session.commit()
    db_session.close()
    return render_template('write.html', title=title)


@app.route('/post/<int:p_id>')
def show_post(p_id):
    title = u'文章详情'
    # p_id = request.args.get('p_id')
    posts = (db_session.query(Article).filter(Article.id == p_id).first())
    author = db_session.query(User.username).filter(Article.user_id == User.id, Article.id == p_id).first()[0]
    return render_template('article_details.html', post=posts, title=title, author=author)


@app.route('/post/<username>')
def show_user_article(username):
    title = "Articles wrote by " + username
    data = db_session.query(Article).filter(Article.user_id == User.id, User.username == username).all()
    return render_template('user_post.html', title=title, posts=data, username=username)


@app.route('/ping/', methods=['GET'])
def get_ping_command():
    title = 'Ping'
    return render_template('ping.html', title=title)


@app.route('/ping/', methods=['POST'])
def ping():
    bannedlist = ['&&', '||', '`', ';', '%0a']
    title = 'Ping'
    ip = request.form.get('command')
    for i in bannedlist:
        if i in ip:
            res = u'检测到非法字符!'
            align = True
            return render_template('ping.html', title=title, res=res, align=align)
    ip = 'ping -c 2 ' + ip
    res = (popen(ip).read().decode('gb2312'))
    return render_template('ping.html', title=title, res=res)


@app.errorhandler(404)
def page_not_found(e):
    template = '''
                {%% extends "base.html" %%}
                {%% block head %%}
                <style>
                .container{
                    float: none;
                    display: block;
                    margin-top: 5%%;
                    margin-left: auto;
                    margin-right: auto;
                }
                </style>
                {%% endblock %%}
                {%% block content %%}
                <div class="container text-center">
                <div class="center-content error">
                <h1 style="font-size:100px;font-family:chiller;">404 Not Found</h1>
                <h1>This is not the web page you are looking for.</h1>
                <h3>%s</h3>
                </div>
                {%% endblock %%}
                ''' % request.url
    return render_template_string(template), 404
    # return render_template('404.html'), 404
