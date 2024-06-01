import os
import select
import socket
import sys
import time
import ctypes
import textwrap
import win32com.client
import pywintypes
path = os.path.abspath(os.path.dirname(__file__))
nvda_dll = ctypes.windll[os.path.join(path, 'nvdaControllerClient64.dll')]
nvda_dll.nvdaController_speakText.argtypes = (ctypes.c_wchar_p,)
try:
	jfw = win32com.client.Dispatch("freedomsci.jawsapi")
except pywintypes.com_error:
	jfw = None

class Server(object):

	def __init__(self, port, bind_host=''):
		self.port = port
		#Maps client sockets to clients
		self.clients = {}
		self.client_sockets = []
		self.running = False
		self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.server_socket.bind((bind_host, self.port))
		self.server_socket.listen(5)

	def run(self):
		self.running = True
		self.last_ping_time = time.time()
		while self.running:
			r, w, e = select.select(self.client_sockets+[self.server_socket], [], self.client_sockets, 60)
			if not self.running:
				break
			for sock in r:
				if sock is self.server_socket:
					self.accept_new_connection()
					continue
				self.clients[sock].handle_data()

	def accept_new_connection(self):
		client_sock, addr = self.server_socket.accept()
		client_sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
		client = Client(server=self, socket=client_sock)
		self.add_client(client)

	def add_client(self, client):
		self.clients[client.socket] = client
		self.client_sockets.append(client.socket)

	def remove_client(self, client):
		del self.clients[client.socket]
		self.client_sockets.remove(client.socket)

	def client_disconnected(self, client):
		self.remove_client(client)

	def close(self):
		self.running = False
		self.server_socket.close()

class Client(object):
	id = 0

	def __init__(self, server, socket):
		self.server = server
		self.socket = socket
		self.buffer = b""
		self.authenticated = False
		self.id = Client.id + 1
		Client.id += 1

	def handle_data(self):
		try:
			data = self.buffer + self.socket.recv(16384)
		except:
			self.close()
			return
		if data == b'': #Disconnect
			self.close()
			return
		if b'\n' not in data:
			self.buffer = data
			return
		self.buffer = b""
		while b'\n' in data:
			line, sep, data = data.partition(b'\n')
			self.parse(line)
		self.buffer += data

	def parse(self, line):
		line = line.decode('utf-8', errors='ignore')
		if not line:
			return
		if line[0] == U"s" or line[0] == u'l':
#			print repr(line)
			if line[1:].strip() == u'':
				return
			text = line[1:]
			if len(text) > 10000:
				lst = textwrap.wrap(text, 10000, break_on_hyphens=False)
				for item in lst:
					self.speak(item)
			else:
				self.speak(text)
		elif line[0] == u'x':
			self.cancel()

	def close(self):
		self.socket.close()
		self.server.client_disconnected(self)

	def speak(self, text):
		if nvda_dll.nvdaController_testIfRunning() == 0:
			nvda_dll.nvdaController_speakText(text)
		elif jfw is not None:
			jfw.SayString(text, False)

	def cancel(self):
		if nvda_dll.nvdaController_testIfRunning() == 0:
			nvda_dll.nvdaController_cancelSpeech()
		elif jfw is not None:
			jfw.SayString("", True)

Server(64111).run()
