from enum import unique
from flask import Flask,request,jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from flask_cors import CORS
from datetime import date
import jwt
import bcrypt
import yagmail 
app = Flask(__name__)


CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/web'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
ma = Marshmallow(app)

class Usuario(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    nombre=db.Column(db.String(100))
    apellidos=db.Column(db.String(100))
    nomUsuario=db.Column(db.String(50),unique=True)
    correo=db.Column(db.String(100),unique=True)
    contraseña=db.Column(db.String(100))
    estado_activacion=db.Column(db.Boolean)
    fecha_ing=db.Column(db.DateTime)

    def __init__(self, nombre, apellidos,correo,contraseña,nomUsuario,estado_activacion,fecha_ing):
        self.nombre = nombre
        self.apellidos=apellidos
        self.correo = correo
        self.contraseña=contraseña
        self.nomUsuario=nomUsuario
        self.estado_activacion=estado_activacion
        self.fecha_ing=fecha_ing
db.create_all()

class UsuarioSchema(ma.Schema):
    class Meta:
        fields = ('id', 'nombre', 'apellidos', 'correo' , 'contraseña','nomUsuario','estado_activacion','fecha_ing')

usuario_schema = UsuarioSchema()
usuarios_schema = UsuarioSchema(many=True)       

class Categoria(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(db.Text)

    def __init__(self, tipo):
        self.tipo = tipo

db.create_all()

class EntradaSchema(ma.Schema):
    class Meta:
        fields = ('id', 'tipo')


entrada_schema = EntradaSchema()
entradas_schema = EntradaSchema(many=True)

class Blog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(70))
    cuerpo = db.Column(db.Text)
    es_publico=db.Column(db.Boolean)
    fechas_publicacion=db.Column(db.DateTime)
    id_usuario=db.Column(db.Integer,ForeignKey("usuario.id"))
    id_categoria=db.Column(db.Integer,ForeignKey("categoria.id"))
    usuariop_id=relationship("Usuario",foreign_keys=[id_usuario])
    categoria_id=relationship("Categoria",foreign_keys=[id_categoria])
    
    def __init__(self, title, cuerpo,es_publico,fecha_publicacion,id_usuario,id_categoria):
        self.title = title
        self.cuerpo = cuerpo
        self.es_publico=es_publico
        self.fechas_publicacion=fecha_publicacion
        self.id_usuario=id_usuario
        self.id_categoria=id_categoria

db.create_all()

class BlogSchema(ma.Schema):
    class Meta:
        fields = ('id', 'title', 'cuerpo' , 'es_publico','fecha_publicacion','id_usuario','id_categoria')


blog_schema = BlogSchema()
blogs_schema = BlogSchema(many=True)


class Comentarios(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    comentario=db.Column(db.String(200))
    id_usuario=db.Column(db.Integer,ForeignKey("usuario.id"))
    id_blog=db.Column(db.Integer,ForeignKey("blog.id"))
    fecha_publicacion=db.Column(db.Date)
    usuario_id=relationship("Usuario",foreign_keys=[id_usuario])
    blog_id=relationship("Blog",foreign_keys=[id_blog])

    def __init__(self, comentario,id_usuario,id_blog,fecha_publicacion):
        self.comentario = comentario
        self.id_usuario=id_usuario
        self.id_blog=id_blog
        self.fecha_publicacion=fecha_publicacion

db.create_all()

class ComentarioSchema(ma.Schema):
    class Meta:
        fields = ('id', 'comentario' , 'id_usuario' , 'id_entrada','fecha_publicacion')


comentario_schema = ComentarioSchema()
comentarios_schema = ComentarioSchema(many=True)



@app.route('/usuario',methods=["POST"])
def crear_usuario():
    correo=request.json['correo']
    nombre=request.json['nombre']
    apellido=request.json['apellido']
    contraseña=request.json['contraseña']
    nomUsuario=request.json['nomUsuario']
    sal=bcrypt.gensalt()
    contraseña=contraseña.encode()
    hashed = bcrypt.hashpw(contraseña,sal)
    estado_activacion=False;
    now = date.today()
    usuario = Usuario.query.filter_by(correo=correo).first()
    user=Usuario.query.filter_by(nomUsuario=nomUsuario).first()
    if(usuario):
        res={
        'error':'El usuario con ese correo ya ha sido creado'
        }
    elif(user):
        res={
        'error':'El nickname ya esta en uso ya ha sido creado'
        }
    else:
        nuevo_usuario=Usuario(nombre,apellido,correo,hashed,nomUsuario,estado_activacion,now)
        db.session.add(nuevo_usuario)
        db.session.commit()
        encoded_jwt = jwt.encode({'name': nombre,'email':correo}, 'secret', algorithm='HS256')
        link="http://localhost:4200/user/validate/{flink}".format(flink=encoded_jwt.decode())
        contents= "Ingresa a este link para validar el correo {flink}".format(flink = link)
        yag=yagmail.SMTP(user='pruebamintic2022@gmail.com',password='Jmd12345678')
        yag.send(to=correo,subject='Validación Cuenta',contents=contents)
        res={
            'success':'usuario creado correctamente',
            'mensaje':'Revisa tu correo para hacer la activación de tu cuenta'
        }
    return jsonify(res) 

@app.route('/usuario/login',methods=["POST"])
def login_usuario():
    correo=request.json['correo']
    contraseña=request.json['contraseña']
    usuario = Usuario.query.filter_by(correo=correo).first()
    if(usuario):
        if(usuario.estado_activacion==True):
            if(bcrypt.checkpw(contraseña.encode(), usuario.contraseña.encode())):
                encoded_jwt = jwt.encode({'id':usuario.id}, 'secret', algorithm='HS256')
                token=encoded_jwt.decode()
                res={
                'success':'Bienvenido al Sistema de blog más interactivo del mundo',
                'id':usuario.id,
                'token':token
                }
            else:
                res={
                    'error':'La contraseña no  coincide'
                }
        else:
            res={
                'error':'La cuenta no se encuentra activada'
            }
    else:
        res={
        'error':'El usuario con ese correo no existe'
        }
    return jsonify(res)

@app.route('/usuario/password',methods=['POST'])
def cambiar_contraseña():
    correo=request.json['correo']
    usuario = Usuario.query.filter_by(correo=correo).first()
    if(usuario):
        link="http://localhost:4200/user/change/password2"
        contents= "Ingresa a este link para cambiar la contraseña {flink}".format(flink = link)
        yag=yagmail.SMTP(user='pruebamintic2022@gmail.com',password='Jmd12345678')
        yag.send(to=correo,subject='Cambiar Contraseña',contents=contents)
        res={
        'success':'Cambiando el password'
        }
        return jsonify(res)
    else:
        res={
        'error':'El usuario con ese correo no existe'
        }
        return jsonify(res)


@app.route('/usuario/password',methods=['PUT'])
def cambiar_contraseña2():
    correo=request.json['correo']
    contraseña=request.json['contraseña']
    sal=bcrypt.gensalt()
    usuario = Usuario.query.filter_by(correo=correo).first()
    if(usuario):
        hashed = bcrypt.hashpw(contraseña.encode(),sal)
        usuario.contraseña=hashed
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
    cuerpo=request.json['cuerpo']
    id_usuario=request.json['id_usuario']
    id_categoria=request.json['id_categoria']
    es_publico=request.json['es_publico']
    now = date.today()
    usuario = Usuario.query.get(id_usuario)
    if(usuario):
        nuevo_blog=Blog(title,cuerpo,es_publico,now,id_usuario,id_categoria)
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



@app.route('/blog/buscar',methods=['GET'])
def obtener_blog():
    title = request.args.get('title','')
    search = "%{}%".format(title)
    obtener_blog = Blog.query.filter(Blog.title.like(search)).first()
    if(obtener_blog):
        return blog_schema.jsonify(obtener_blog)
    else:
        res={
            'error':'No se ha pódido encontrar ninguna entrada con ese titulo'
        }
    return jsonify(res)



@app.route('/blog',methods=['GET'])
def obtener_blogs_publicos():
    obtener_blogs_publicos=Blog.query.filter(Blog.es_publico==True).all()
    result=blogs_schema.dump(obtener_blogs_publicos)
    return jsonify(result)

@app.route('/blog/privados',methods=['GET'])
def obtener_blogs_privados():
    id_usuario = request.args.get('id_usuario','')
    obtener_blogs_privados=Blog.query.filter(Blog.es_publico==False and Blog.id_usuario==id_usuario).all()
    result=blogs_schema.dump(obtener_blogs_privados)
    if(result):
        return jsonify(result)
    else:
        res={
            'error':'No tienes blogs'
        }
        return jsonify(res)


@app.route('/blog/actualizar',methods=['PUT'])
def actualizar_blog():
    id=request.json['id']
    title=request.json['title']
    cuerpo=request.json['cuerpo']
    id_categoria=request.json['id_categoria']
    es_publico=request.json['es_publico']
    blog = Blog.query.get(id)
    if(blog):
        blog.title=title
        blog.cuerpo=cuerpo
        blog.id_categoria=id_categoria
        blog.es_publico=es_publico
        db.session.commit()
        res={
            'success':'Entrada actualizada'
        }
    else:
        res={
            'error':'No se ha podido encontrar la entrada'
        }
    
    return jsonify(res)


@app.route('/entrada/eliminar',methods=['DELETE'])
def eliminar_entrada():
    id=request.json['id']
    blog=Blog.query.get(id)
    db.session.delete(blog)
    db.session.commit()
    return "Blog Eliminado con exito"


@app.route('/usuario/comentario',methods=['POST'])
def crear_comentario():
    comentario=request.json['comentario']
    id_usuario=request.json['id_usuario']
    id_blog=request.json['id_blog']
    now = date.today()
    usuario = Usuario.query.get(id_usuario)
    if(usuario):
        blog = Blog.query.get(id_blog)
        if(blog):
            nuevo_comentario=Comentarios(comentario,id_usuario,id_blog,now)
            db.session.add(nuevo_comentario)
            db.session.commit()
            res={
                'success':'Comentario creado Correctamente'
            }
        else:
            res={
                'error':'No Se ha creado ninguna entrada'
            }
    else:
        res={
            'error':'No hay ningun usuario creado'
        }
    return jsonify(res)


@app.route('/usuario/comentario/',methods=['GET'])
def obtener_comentarios():
    id_blog = request.args.get('id_blog','')
    obtener_coments=Comentarios.query.filter_by(id_blog=id_blog).all()
    result=comentarios_schema.dump(obtener_coments)
    return jsonify(result)

@app.route('/user/verify',methods=['POST'])
def validar_token():
    jwts=request.json['token']
    desjwt=jwt.decode(jwts, 'secret', algorithms=['HS256'])

    correo=desjwt['email']
    usuario = Usuario.query.filter_by(correo=correo).first()
    print(usuario)
    if(usuario):
        print('hola')
        usuario.estado_activacion=True
        db.session.commit()
        return jsonify(desjwt)
    else:
        res={
            'error':'no existe el usuario'
        }
        return jsonify(res)
if __name__ == "__main__":
    app.run(debug=True)