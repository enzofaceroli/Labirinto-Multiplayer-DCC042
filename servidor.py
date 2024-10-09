from gerar_labirinto import *
from PIL import Image, ImageDraw
import threading as th
import base64
import socket
import pickle
from time import sleep
import random



host = ''
port = 4041

ids_jogadores = []
conections = []
clientes = []
threads = []
posicao = {}
placar = {}
cor_jogadores = []
vencedor = False
tamanho = [20,10]
size = 21
l = gerar_labirinto(tamanho[0],tamanho[1])

img_new = Image.new('RGB', (tamanho[0]*(size+1)+1,tamanho[1]*(size+1)+1), (0,0,0))
draw = ImageDraw.Draw(img_new)
desenhar_labirinto_pillow(draw, tamanho, l, size)
size += 1
img_new.save("rect_pillow.png")

aux = Image.open("rect_pillow.png")
rgb = aux.load()
with open("rect_pillow.png", 'rb') as rd:
	img_str = rd.read()
	img_code = base64.encodebytes(img_str)

def get_ID():
	Id = random.randint(0,9999)
	if Id not in ids_jogadores:
		ids_jogadores.append(Id)
		return Id
	return get_ID()


def verificar_vitoria():
	global posicao
	for ID, p in posicao.items():
		if p[0] == [size/2, tamanho[1]*size-size/2]:
			return ID

	return False

def verficar_cor(cor):
	global cor_jogadores
	if cor not in cor_jogadores:
		cor_jogadores.append(cor)
		return False
	return True


def get_cor():
	global cor_jogadores
	cor = []
	for c in range(3):
		cor.append(random.randint(15,255))
	if verficar_cor(cor):
		return get_cor()
	return cor


def broadCastMensagens(con):
	global posicao, vencedor
	q = {"posicao": posicao, "venceu": vencedor, "cores":cor_jogadores}
	con.send(pickle.dumps(q))


def controlador(client, con):
    global posicao
    # print("debug:",posicao)
    # print(1)
    try:
        for p in posicao.keys():
            # print("debug:",posicao, p)
            Id = p
            # cor = posicao[p][1]
            break
    except:
        exit()
    # print(Id, cor)
    # print(2)
    # exit()
    while True:
        try:
            tmp = pickle.loads(con.recv(512))
            # print(posicao[Id][0])
            print(tmp)
            if tmp != "''":
                print(1)
                if tmp == "left" and rgb[posicao[Id][0][0]-size/2, posicao[Id][0][1]] != (255,255,255):
                    pos = [posicao[Id][0][0]-size, posicao[Id][0][1]]
                elif tmp == "right" and rgb[posicao[Id][0][0]+size/2, posicao[Id][0][1]] != (255,255,255):
                    pos = [posicao[Id][0][0]+size, posicao[Id][0][1]]
                elif tmp == "down" and rgb[posicao[Id][0][0], posicao[Id][0][1]+size/2] != (255,255,255):
                    pos = [posicao[Id][0][0], posicao[Id][0][1]+size]
                elif tmp == "up" and rgb[posicao[Id][0][0], posicao[Id][0][1]-size/2] != (255,255,255):
                    pos = [posicao[Id][0][0], posicao[Id][0][1]-size]
                print(pos)
                posicao[Id][0] = pos
        except:
            pass


def lobbyClientServer(client, con):
    try:
        global posicao, vencedor

                

        print('Cliente conectado', client)
        Id = get_ID()
        cor = get_cor()
        posicao[Id] = [[tamanho[0]*size-size/2,size/2], cor]
        con.send(pickle.dumps({ "payload":[len(img_code)+512, (len(l[0])+len(l[1]))*4]}))
        a = pickle.dumps({ "id" :          Id, 
        						"size":       size, 
        						"tamanho": tamanho,
        						"lab":           l, 
        						"posicao": posicao,
        						"image":  img_code})
        # print(a)
        con.send(a)

        conections.append(con)
        clientes.append(client)
        while True:
            try:
                # print(posicao.values())
                vencedor = verificar_vitoria()
                broadCastMensagens(con)
                msg = con.recv(512*4)
                jogou = pickle.loads(msg)["jogou"]
                # ide = pickle.loads(msg)["posicao"]
                if jogou:
                    dataJson = pickle.loads(msg)
                    posicao[Id] = dataJson['posicao']
            except:
                del posicao[Id]
                cor_jogadores.remove(cor)
                con.close()
                ids_jogadores.remove(Id)
                print(f'{Id} Cliente foi desconectado...')
                clientes.remove(client)
                conections.remove(con)
                exit()
    except:
        exit()

print('Servidor iniciado...')
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
orig = (host, port)
s.bind(orig)
s.listen(1)

while True:
    con, client = s.accept()
    tipo = pickle.loads(con.recv(512))["tipo"]
    if tipo == "jogador":
        new_th = th.Thread(target=lobbyClientServer, args=(client, con))
    else:
        new_th = th.Thread(target=controlador, args=(client, con))
    new_th.start()

    threads.append(new_th)