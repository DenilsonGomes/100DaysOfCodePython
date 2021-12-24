# Blog Capstone Projeto refeito
import datetime as dt
import smtplib
from flask import Flask, render_template, request, redirect
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, URL
from flask_ckeditor import CKEditor, CKEditorField
import config

# notificacao do projeto dia  Day 60
SMTP_SERVER = "smtp.mailtrap.io"
SMTP_PORT = "2525"
SUBJECT_TEXT = "A Messagem do blog"
RECEIVER_NAME = "Thatiane"
RECEIVER_ADDRESS = "myemail@mydomain.zyx"

app = Flask(__name__)
app.secret_key = "ThisIsASecretKey"
ckeditor = CKEditor(app)
Bootstrap(app)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///posts.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class BlogPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    author = db.Column(db.String(250), nullable=False)
    img_url = db.Column(db.String(250), nullable=False)


class CreatePostForm(FlaskForm):
    title = StringField("Blog Post Title", validators=[DataRequired()])
    subtitle = StringField("Subtitle", validators=[DataRequired()])
    author = StringField("Your Name", validators=[DataRequired()])
    img_url = StringField("Blog Image URL", validators=[DataRequired(), URL()])
    # this is a CKEditorField
    body = CKEditorField("Blog Content", validators=[DataRequired()])
    submit = SubmitField("Submit Post")


def get_current_year():
    """Retorna o ano atual como INT."""
    return dt.datetime.now().year


def get_current_date():
    """Retorna a data atual como um STR."""
    return dt.datetime.now().strftime("%B %d, %Y")


def send_email(message):
    """Faz um DICT com os detalhes e envia um e-mail para o endereço definido."""
    # formatar o email
    sender = f"{message['name']} <{message['email']}>"
    receiver = f"{RECEIVER_NAME} <{RECEIVER_ADDRESS}>"
    body = f"Subject: {SUBJECT_TEXT}\nTo: {receiver}\nFrom: {sender}\n\n" \
           f"{message['message']}\n\n" \
           f"From:\nName: {message['name']}\nEmail: {message['email']}\nPhone: {message['phone']}"
    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(config.SMTP_LOGIN, config.SMTP_PASS)
            server.sendmail(sender, receiver, body)
    except smtplib.SMTPServerDisconnected as ex:
        print(ex)
        print("Make sure the SMTP_LOGIN and SMTP_PASS credentials have been set correctly in config.py.")
        return False
    else:
        # apenas para ter algum feedback
        print(f"Uma mensagem foi enviada para {RECEIVER_ADDRESS}.")
        return True


@app.route("/")
def home():
    all_posts = BlogPost.query.all()
    return render_template("index.html", posts=all_posts, year=get_current_year())


@app.route("/post/<int:blog_id>")
def show_post(blog_id):
    blog_post = BlogPost.query.get(blog_id)
    if blog_post:
        return render_template("post.html", post=blog_post, year=get_current_year())
    else:
        return redirect("/")


@app.route("/about")
def about():
    return render_template("about.html", year=get_current_year())


@app.route("/contact.html", methods=["GET", "POST"])
def contact():
    # display uma msg difrente
    if request.method == "POST":
        message = {
            "name": request.form["name"],
            "email": request.form["email"],
            "phone": request.form["phone"],
            "message": request.form["message"]
        }
        # sobre msg
        if send_email(message):
            status = "Success!"
            text = "Your message has been sent."
        else:
            status = "Something went wrong."
            text = "The message could not be sent."
        # display status pagina
        return render_template("message.html", status=status, text=text)
    # display the regular contato
    else:
        return render_template("contact.html", year=get_current_year())


@app.route("/new-post", methods=["GET", "POST"])
def add_post():
    form = CreatePostForm()
    if form.validate_on_submit():
        new_post = BlogPost(
            title=form.title.data,
            subtitle=form.subtitle.data,
            date=get_current_date(),
            body=form.body.data,
            author=form.author.data,
            img_url=form.img_url.data
        )
        db.session.add(new_post)
        db.session.commit()
        return redirect("/")
    return render_template("make-post.html", heading="New Post", form=form, year=get_current_year())


@app.route("/edit/<int:blog_id>", methods=["GET", "POST"])
def edit_post(blog_id):
    # encontre o blog no DB
    post = BlogPost.query.get(blog_id)
    if post:
        # se a postagem existe, preencha os campos do formulário
        form = CreatePostForm(
            title=post.title,
            subtitle=post.subtitle,
            img_url=post.img_url,
            author=post.author,
            body=post.body
        )
        # atualize o DB
        if form.validate_on_submit():
            post.title = form.title.data
            post.subtitle = form.subtitle.data
            post.img_url = form.img_url.data
            post.author = form.author.data
            post.body = form.body.data
            db.session.commit()
            # redirecionar post para pagina principal
            return redirect(f"/post/{post.id}")
        return render_template("make-post.html", heading="Edit Post", form=form, year=get_current_year())
    # se tal postagem não existir, basta redirecionar para a página principal
    return redirect("/")


@app.route("/delete/<int:blog_id>", methods=["GET", "POST"])
def delete_post(blog_id):
    post = BlogPost.query.get(blog_id)
    # se essas postagens existirem, exclua-as
    if post:
        db.session.delete(post)
        db.session.commit()
    # redirecionar a pagina principal
    return redirect("/")


if __name__ == "__main__":
    app.run(debug=True)