import re
from flask import Flask,request,jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/web'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
ma = Marshmallow(app)

class Usuario(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    nombre=db.Column(db.String(100))
    apellidos=db.Column(db.String(100))
    correo=db.Column(db.String(100),unique=True)
    contraseña=db.Column(db.String(100))

    def __init__(self, nombre, apellidos,correo,contraseña):
        self.nombre = nombre
        self.apellidos=apellidos
        self.correo = correo
        self.contraseña=contraseña

db.create_all()

class UsuarioSchema(ma.Schema):
    class Meta:
        fields = ('id', 'nombre', 'apellidos', 'correo' , 'contraseña')

usuario_schema = UsuarioSchema()
usuarios_schema = UsuarioSchema(many=True)       

class Blog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(70))
    description = db.Column(db.String(100))
    id_usuario=db.Column(db.Integer,ForeignKey("usuario.id"))
    usuariop_id=relationship("Usuario",foreign_keys=[id_usuario])
    def __init__(self, title, description,id_usuario):
        self.title = title
        self.description = description
        self.id_usuario=id_usuario

db.create_all()

class BlogSchema(ma.Schema):
    class Meta:
        fields = ('id', 'title', 'description' , 'id_usuario')


blog_schema = BlogSchema()
blogs_schema = BlogSchema(many=True)

class Entrada(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(70))
    content = db.Column(db.String(255))
    id_usuario=db.Column(db.Integer,ForeignKey("usuario.id"))
    id_blog=db.Column(db.Integer,ForeignKey("blog.id"))
    usuario_id=relationship("Usuario",foreign_keys=[id_usuario])
    blog_id=relationship("Blog",foreign_keys=[id_blog])

    def __init__(self, title, content,id_usuario,id_blog):
        self.title = title
        self.content = content
        self.id_usuario=id_usuario
        self.id_blog=id_blog

db.create_all()

class EntradaSchema(ma.Schema):
    class Meta:
        fields = ('id', 'title', 'content' , 'id_usuario' , 'id_blog')


entrada_schema = EntradaSchema()
entradas_schema = EntradaSchema(many=True)



@app.route('/usuario',methods=["POST"])
def crear_usuario():
    correo=request.json['correo']
    nombre=request.json['nombre']
    apellido=request.json['apellido']
    contraseña=request.json['contraseña']
    usuario = Usuario.query.filter_by(correo=correo).first()
    if(usuario):
        res={
        'error':'el usuario con ese correo ya ha sido creado'
        }
    else:
        nuevo_usuario=Usuario(nombre,apellido,correo,contraseña)
        db.session.add(nuevo_usuario)
        db.session.commit()
        res={
            'success':'usuario creado correctamente'
        }
    return jsonify(res)

@app.route('/usuario/login',methods=["POST"])
def login_usuario():
    correo=request.json['correo']
    contraseña=request.json['contraseña']
    usuario = Usuario.query.filter_by(correo=correo).first()
    if(usuario):
        if(usuario.contraseña==contraseña):
            res={
            'success':'Bienvenido al Sistema de blog más interactivo del mundo',
            'id':usuario.id
            }
        else:
            res={
                'error':'La contraseña no  coincide'
            }
    else:
        res={
        'error':'el usuario con ese correo no existe'
        }
    return jsonify(res)

@app.route('/usuario/password',methods=['POST'])
def cambiar_contraseña():
    correo=request.json['correo']
    usuario = Usuario.query.filter_by(correo=correo).first()
    if(usuario):
        res={
        'success':'Cambiando el password'
        }
        return jsonify(res)
    else:
        res={
        'error':'el usuario con ese correo no existe'
        }
        return jsonify(res)

@app.route('/usuario/password/<correo>',methods=['PUT'])
def cambiar_contraseña2(correo):
    contraseña=request.json['contraseña']
    usuario = Usuario.query.filter_by(correo=correo).first()
    if(usuario):
        usuario.contraseña=contraseña
        db.session.commit()
        res={
            'success':'El password se ha cambiado correctamente'
        }
        return jsonify(res)
    else:
        res={
        'error':'Ocurrio un problema con el cambio de contraseña'
        }
        return jsonify(res)

@app.route('/blog',methods=["POST"])
def crear_blog():
    title=request.json['title']
    description=request.json['description']
    id_usuario=request.json['id_usuario']
    usuario = Usuario.query.get(id_usuario)
    if(usuario):
        nuevo_blog=Blog(title,description,id_usuario)
        db.session.add(nuevo_blog)
        db.session.commit()
        res={
        'success':'Blog creado correctamente'
        }
    else:
        res={
        'error':'El usuario no existe'
        }
    return jsonify(res)

@app.route('/entrada/<id_blog>',methods=['GET'])
def obtener_entradas(id_blog):
    obtener_entradas=Entrada.query.filter_by(id_blog=id_blog).all()
    result=entradas_schema.dump(obtener_entradas)
    return jsonify(result)

@app.route('/entrada',methods=['POST'])
def crear_entradas():
    title=request.json['title']
    content=request.json['content']
    id_usuario=request.json['id_usuario']
    id_blog=request.json['id_blog']
    nueva_entrada=Entrada(title,content,id_usuario,id_blog)
    db.session.add(nueva_entrada)
    db.session.commit()
    res={
        'success':'Entrada creada correctamente'
    }
    return jsonify(res)

@app.route('/entrada/actualizar/<id>',methods=['PUT'])
def actualizar_entrada(id):
    title=request.json['title']
    content=request.json['content']
    entrada = Entrada.query.get(id)
    if(entrada):
        entrada.title=title
        entrada.content=content
        db.session.commit()
        res={
            'success':'Entrada actualizada'
        }
    else:
        res={
            'error':'No se ha podido encontrar la entrada'
        }
    
    return jsonify(res)

@app.route('/entrada/eliminar/<id>',methods=['DELETE'])
def eliminar_entrada(id):
    entrada=Entrada.query.get(id)
    db.session.delete(entrada)
    db.session.commit()
    return entrada_schema.jsonify(entrada)

@app.route('/entrada/buscar',methods=['GET'])
def buscar_entrada():
    title=request.json['title']
    search = "%{}%".format(title)
    obtener_entrada = Entrada.query.filter(Entrada.title.like(search)).one()
    if(obtener_entrada):
        return entrada_schema.jsonify(obtener_entrada)
    else:
        res={
            'error':'No se ha pódido encontrar ninguna entrada con ese titulo'
        }
    return jsonify(res)


if __name__ == "__main__":
    app.run(debug=True)