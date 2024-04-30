from flask import Flask, render_template, redirect, request, abort, make_response
from flask_login import LoginManager, login_user, login_required, logout_user, current_user

from forms.user import RegisterForm, LoginForm
from forms.new_product import ProductForm
from data import db_session
from data.users import User
from data.new_product import Products
from data.gigachat import get_chat_completion, get_token
import html
from werkzeug.utils import secure_filename
import os
from PIL import Image

app = Flask(__name__)
login_manager = LoginManager()
login_manager.init_app(app)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
UPLOAD_EXTENSIONS = ['.jpg', '.png']

list = ['Яблоко', 'Банан', 'Морковь', 'Свинина', 'Капуста', 'Огурец', 'Говядина', 'Хлеб', 'Картофель', 'Курица',
            'Рис', 'Макароны', 'Молоко', 'Йогурт', 'Сыр', 'Яйца', 'Масло', 'Мука',
            'Шоколад', 'Апельсин', 'Виноград', 'Помидор', 'Лук', 'Рыба']


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.get(User, user_id)


def main():
    db_session.global_init("db/user.db")
    app.run()


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.name == form.name.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            return redirect("/")
        return render_template('login.html', message="Неправильный логин или пароль", form=form)
    return render_template('login.html', title='Авторизация', form=form)


@app.route('/register', methods=['GET', 'POST'])
def reqister():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('registration.html', title='Регистрация', form=form,
                                   message="Пароли не совпадают")
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.name == form.name.data).first():
            return render_template('registration.html', title='Регистрация', form=form,
                                   message="Такой пользователь уже есть")
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template('registration.html', title='Регистрация', form=form,
                                   message="Такой пользователь уже есть")
        user = User(
            name=form.name.data,
            email=form.email.data,
        )
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        return redirect('/login')
    return render_template('registration.html', title='Регистрация', form=form)


@app.route("/", methods=['GET', 'POST'])
def index():
    if current_user.is_authenticated:
        form = ProductForm()
        db_sess = db_session.create_session()
        product = db_sess.query(Products).filter(Products.who == current_user.name).all()
        custom_prosucts = [i.product for i in product]
        return render_template("products.html", list=list, custom_prosucts=custom_prosucts, class_products=product,
                               user=current_user.name, form=form, up_message='Просто '
                                                      'выберите внизу продукты, которые есть у вас дома, или '
                                                      'добавьте свой, после чего вы получите'
                                                       ' результат в виде рецепта!')
    else:
        return render_template("index.html")


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


@app.route('/loading')
@login_required
def loading():
    resp = make_response(render_template("loading.html", user=current_user.name,
                                             message='Идет загрузка, пожалуйста подождите!'))
    if ' '.join([i for i in request.values if i != 'csrf_token']):
        resp.set_cookie('products', ', '.join([i for i in [j.lower() for j in request.values] if i != 'csrf_token']))
        return resp
    else:
        return render_template("loading.html", user=current_user.name,
                            message='Что-то пошло не так, похоже вы не выбрали продукт...')


@app.route('/result')
def result():
    cookie = request.cookies.get('products')
    auth = 'OGJkNGI0ZmUtOTBlNy00NTBkLWE4M2MtYmI0ODFjMDAyYjlmOjk0MzUyZmE3LTQwYTktNGU0MS1iN2U5LWEwY2MwYTUxNzFlMg=='
    response = get_token(auth)
    if response != 1:
        giga_token = response.json()['access_token']
        answer = get_chat_completion(giga_token,
                                 f'Придумай или найди рецепт ОДИН РЕЦЕПТ, причем только с использованием в '
                                 f'ингридиентах ТОЛЬКО СЛЕДУЮЩИХ продуктов: {cookie}. Не используй другие продукты')
        recept = answer.json()['choices'][0]['message']['content']
        recept = recept.replace('Ингредиенты:', '<b>Ингредиенты:</b>')
        recept = recept.replace('Инструкции:', '<b>Инструкции:</b>')
        recept = recept.replace('Приготовление:', '<b>Приготовление:</b>')
        recept = recept.replace('\n', '<br>')
        return render_template("result.html", message=recept, user=current_user.name, up_message='Снизу представлен '
                                                'ваш рецепт! Было бы здорово, если бы вы оценили полученный рецепт :)')


def test_products(product):
    auth = 'OGJkNGI0ZmUtOTBlNy00NTBkLWE4M2MtYmI0ODFjMDAyYjlmOjk0MzUyZmE3LTQwYTktNGU0MS1iN2U5LWEwY2MwYTUxNzFlMg=='
    response = get_token(auth)
    if response != 1:
        giga_token = response.json()['access_token']
        answer = get_chat_completion(giga_token,
                                    f'Ответь одним словом, да или нет, является ли следующий элемент продуктов питания.'
                                    f' Продуктом питания называется только такой продукт, из которого можно создать '
                                    f'другое блюдо. Указанный элемент:{product}')
        return answer.json()['choices'][0]['message']['content']


@app.route('/upload_product', methods=['GET', 'POST'])
def upload_product():
    form = ProductForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(
                Products.product == form.title.data and Products.who == current_user).first():
            return render_template('myself_product.html', user=current_user.name,
                                   up_message='Для добавления продукта впишите'
                                              ' его название, по желанию выберите аватарку.', title='Регистрация',
                                   form=form,
                                   error="Такой продукт уже есть")
        if test_products(form.title.data) == 'Да':
            products = Products(
                who=current_user.name,
                product=form.title.data,
            )
            if form.image.data:
                filename = secure_filename(form.image.data.filename)
                file_ext = f".{filename[-3:]}"
                if file_ext not in UPLOAD_EXTENSIONS:
                    return render_template('myself_product.html', title='Регистрация', user=current_user.name,
                                           up_message='Для добавления продукта впишите'
                                                        ' его название, по желанию выберите аватарку.', form=form,
                                           error="Выбранный файл не является фотографией или формат не поддерживается. "
                                                 "Поддерживаемый формат: jpg, png")
                fullname = 'static/uploads/' + filename
                form.image.data.save(fullname)
                img = Image.open(fullname)
                new_image = img.resize((256, 256))
                file_list = os.listdir('static/uploads')
                os.remove(fullname)
                new_image.save(f"static/uploads/file{len(file_list)}.{filename[-3:]}")
                products.image = f"static/uploads/file{len(file_list)}.{filename[-3:]}"
            else:
                products.image = 'static/img/quations.png'
            db_sess.add(products)
            db_sess.commit()
            return redirect("/")
        return render_template("myself_product.html", user=current_user.name, up_message='Для добавления продукта '
                                                                                         'впишите'
                                                        ' его название, по желанию выберите аватарку.', form=form,
                                                        error='Упс! Похоже вы выбрали не продукт питания')
    return render_template("myself_product.html", user=current_user.name, up_message='Для добавления продукта впишите'
                                                        ' его название, по желанию выберите аватарку.', form=form)


@app.route('/products_delete/<int:id>', methods=['GET', 'POST'])
@login_required
def products_delete(id):
    db_sess = db_session.create_session()
    products = db_sess.query(Products).filter(Products.id == id, Products.who == current_user.name).first()
    if products:
        if products.image != 'static/img/quations.png':
            times_picture = db_sess.query(Products).filter(Products.image == products.image).all()
            if len(times_picture) == 1:
                os.remove(products.image)
        db_sess.delete(products)
        db_sess.commit()
    else:
        abort(404)
    return redirect('/')


if __name__ == '__main__':
    main()
