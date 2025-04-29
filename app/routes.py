import os
from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from app import app, db
from app.models import Item, User
from app.forms import CadastroForm, LoginForm, CompraProdutoForm, VendaProdutoForm, CriarProdutoForm

UPLOAD_FOLDER = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'static', 'img')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def page_home():
    return render_template("home.html")


@app.route('/produtos', methods=['GET', 'POST'])
@login_required
def page_produto():
    compra_form = CompraProdutoForm()
    venda_form = VendaProdutoForm()

    search_query = request.args.get('search', '').strip()  # Obtem o termo de busca
    if search_query:
        itens = Item.query.filter(Item.nome.ilike(f'%{search_query}%')).all()  # Busca pelo nome
    else:
        itens = Item.query.all()

    dono_itens = Item.query.filter_by(dono=current_user.id)

    return render_template(
        "produtos.html",
        itens=itens,
        compra_form=compra_form,
        dono_itens=dono_itens,
        venda_form=venda_form,
        search_query=search_query
    )


@app.route('/pagamento', methods=['GET', 'POST'])
@login_required
def page_pagamento():
    produto_id = request.args.get('produto_id')

    if request.method == "POST":
        pagamento = request.form.get('pagamento')
        produto_obj = Item.query.get(produto_id)
        if produto_obj:
            flash(f"Pagamento realizado com sucesso usando {pagamento}.", category='success')
        return redirect(url_for('page_produto'))

    return render_template('pagamento.html', produto_id=produto_id)


@app.route('/cadastro', methods=['GET', 'POST'])
def page_cadastro():
    form = CadastroForm()
    if form.validate_on_submit():
        usuario = User(
            usuario=form.usuario.data,
            email=form.email.data,
            senhacrip=form.senha1.data
        )
        db.session.add(usuario)
        db.session.commit()
        return redirect(url_for('page_produto'))
    if form.errors != {}:
        for err in form.errors.values():
            flash(f"Erro ao cadastrar usuário {err}", category='danger')

    return render_template("cadastro.html", form=form)


@app.route('/login', methods=['GET', 'POST'])
def page_login():
    form = LoginForm()
    if form.validate_on_submit():
        usuario_logado = User.query.filter_by(usuario=form.usuario.data).first()
        if usuario_logado and usuario_logado.converte_senha(senha_texto_claro=form.senha.data):
            login_user(usuario_logado)
            flash(f'Sucesso! Seu login é: {usuario_logado.usuario}', category='success')
            return redirect(url_for('page_produto'))
        else:
            flash('Usuário ou senha estão incorretos! Tente novamente.', category='danger')
    return render_template('login.html', form=form)


@app.route('/logout')
def page_logout():
    logout_user()
    flash("Você fez o logout", category='info')
    return redirect(url_for('page_home'))


@app.route('/perfil', methods=['GET', 'POST'])
@login_required
def page_perfil():
    if request.method == "POST":
        # Atualiza o usuário
        current_user.usuario = request.form['usuario']
        current_user.email = request.form['email']
        # Aqui você pode adicionar lógica para salvar o endereço e outras informações
        new_senha = request.form['senha1']
        confirm_senha = request.form['senha2']

        if new_senha and new_senha == confirm_senha:
            current_user.senhacrip = new_senha

        db.session.commit()
        flash('Informações do perfil atualizadas com sucesso!', category='success')
        return redirect(url_for('page_perfil'))

    return render_template('perfil.html')

@app.route('/produto_detalhes/<int:produto_id>', methods=['GET'])
@login_required
def page_produto_detalhes(produto_id):
    item = Item.query.get(produto_id)
    if not item:
        flash("Produto não encontrado.", category='danger')
        return redirect(url_for('page_produto_detalhes'))

    return render_template('produto_detalhes.html', item=item)

@app.route('/contato', methods=['GET'])
def page_contato():
    return render_template('contato.html')


@app.route('/criar_produto', methods=['GET', 'POST'])
@login_required
def criar_produto():
    form = CriarProdutoForm()

    if form.validate_on_submit():
        # Processar imagem
        imagem = form.imagem.data
        if imagem and allowed_file(imagem.filename):
            filename = secure_filename(imagem.filename)
            caminho_imagem = os.path.join(app.config['UPLOAD_FOLDER'], filename)

            # Certifique-se de que o diretório de destino existe
            if not os.path.exists(app.config['UPLOAD_FOLDER']):
                os.makedirs(app.config['UPLOAD_FOLDER'])

            imagem.save(caminho_imagem)  # Salva a imagem no diretório

        else:
            filename = 'default.png'  # Imagem padrão caso nenhuma seja enviada ou não seja válida.

        # Criar novo produto
        novo_produto = Item(
            nome=form.nome.data,
            preco=form.preco.data,
            cod_barra=form.cod_barra.data,
            descricao=form.descricao.data,
            imagem=filename,
            dono=current_user.id  # Relacionar o produto ao usuário atual.
        )

        # Salvar no banco de dados
        db.session.add(novo_produto)
        db.session.commit()

        flash(f"Produto '{novo_produto.nome}' criado com sucesso!", category='success')
        return redirect(url_for('page_produto'))
    

    return render_template('criar_produto.html', form=form)

@app.route('/produto/<int:produto_id>/excluir', methods=['POST'])
@login_required
def excluir_produto(produto_id):
    if current_user.email != 'admin@gmail.com':
        flash("Você não tem permissão para excluir produtos.", "danger")
        return redirect(url_for('home'))

    produto = Item.query.get_or_404(produto_id)
    try:
        db.session.delete(produto)
        db.session.commit()
        flash("Produto excluído com sucesso.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Erro ao excluir o produto: {str(e)}", "danger")
    return redirect(url_for('page_produto'))


@app.route('/editar_produto/<int:produto_id>', methods=['GET', 'POST'])
@login_required
def editar_produto(produto_id):
    # Verifica se o usuário logado é o administrador
    if current_user.email != 'admin@gmail.com':
        return redirect(url_for('home'))  # Redireciona se não for admin

    # Busca o item no banco de dados
    item = Item.query.get_or_404(produto_id)

    if request.method == 'POST':
        # Atualiza as informações do produto
        item.nome = request.form['nome']
        item.cod_barra = request.form['cod_barra']
        item.preco = request.form['preco']
        item.descricao = request.form['descricao']
        
        # Verifica se uma nova imagem foi enviada
        imagem = request.files['imagem']
        if imagem:
            imagem_filename = secure_filename(imagem.filename)
            imagem.save(os.path.join(app.config['UPLOAD_FOLDER'], imagem_filename))
            item.imagem = imagem_filename
        
        db.session.commit()  # Salva as alterações no banco de dados
        return redirect(url_for('page_produto', produto_id=item.Id))  # Redireciona para a página de detalhes do produto

    return render_template('editar_produto.html', item=item)


