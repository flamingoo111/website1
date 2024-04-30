from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, BooleanField, SubmitField, FileField
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms.validators import DataRequired
from flask_uploads import UploadSet


class ProductForm(FlaskForm):
    title = StringField('Название продукта', validators=[DataRequired()])
    image = FileField('image')
    submit = SubmitField('Применить')