from flask_wtf import FlaskForm
from wtforms.validators import Length, EqualTo, Email, DataRequired, ValidationError, NumberRange
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, IntegerField, TextAreaField, SubmitField, PasswordField

from app.models import User

class CadastroForm(FlaskForm):
    def validate_username(self, check_user):
        user = User.query.filter_by(usuario=check_user.data).first()
        if user:
            raise ValidationError("Usuario ja existe! Cadastre outro usuario")

    def validate_email(self, check_email):
        user = User.query.filter_by(usuario=check_email.data).first()
        if user:
            raise ValidationError("Email ja existe! Cadastre outro Email")
        
    def validate_senha(self, check_senha):
        user = User.query.filter_by(usuario=check_senha.data).first()
        if user:
            raise ValidationError("Senha ja existe! Cadastre outra senha")
        
    usuario = StringField(label='Username:', validators=[Length(min=2,max=30), DataRequired()])
    email = StringField(label='Email', validators=[Email(), DataRequired()])
    senha1 = PasswordField(label='Senha', validators=[Length(min=6), DataRequired()])
    senha2 = PasswordField(label='Confirmação da senha', validators=[EqualTo('senha1'), DataRequired()])
    submit = SubmitField(label='Cadastrar')


class LoginForm(FlaskForm):
    usuario = StringField(label='usuario', validators=[DataRequired()])
    senha = PasswordField(label='senha',validators=[DataRequired()])
    submit = SubmitField(label='log in')


class CompraProdutoForm(FlaskForm):
    submit = SubmitField(label='Comprar Produto!')

class VendaProdutoForm(FlaskForm):
    submit = SubmitField(label='Vender Produto!')

class CriarProdutoForm(FlaskForm):
    nome = StringField('Nome', validators=[DataRequired()])
    preco = StringField('Preço', validators=[DataRequired()])
    cod_barra = StringField('Código de Barras', validators=[DataRequired()])
    descricao = TextAreaField('Descrição', validators=[DataRequired()])
    imagem = FileField('Imagem')
    submit = SubmitField('Criar Produto')

    def save(self, user_id):
        imagem = self.imagem.data
        nome_seguro = secure_filename(imagem.filename) if isinstance(imagem, FileStorage) and imagem.filename else 'default.png'
        item = Item(nome=self.nome.data, user_id=user_id, imagem=nome_seguro)
        
        if imagem and imagem.filename:
            caminho_diretorio = os.path.join(os.path.abspath(os.path.dirname(__file__)), app.config['UPLOAD_FILES'])
            os.makedirs(caminho_diretorio, exist_ok=True)
            imagem.save(os.path.join(caminho_diretorio, nome_seguro))

        db.session.add(item)
        db.session.commit()




    